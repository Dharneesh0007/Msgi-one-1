-- ============================================================================
-- MSGI ONE — ENTERPRISE ECOSYSTEM MIGRATION (PHASE 2)
-- Migration: 20261125000001_enterprise_ecosystem.sql
-- Governing Textbooks: Elmasri & Navathe (3NF, Constraints), Kleppmann (Transactions, Outbox, Idempotency)
-- GOVERNANCE NOTICE: Prepared locally. Do NOT apply to remote production without explicit owner authorization.
-- ============================================================================

-- Enable btree_gist for exclusion constraints preventing overlapping confirmed meetings
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- ============================================================================
-- 1. SCHEDULING ENGINE (4 TABLES)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.alumni_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alumni_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time_local VARCHAR(5) NOT NULL,
    end_time_local VARCHAR(5) NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    slot_duration_minutes INTEGER NOT NULL DEFAULT 30 CHECK (slot_duration_minutes IN (15, 30, 45, 60, 90)),
    buffer_minutes INTEGER NOT NULL DEFAULT 10 CHECK (buffer_minutes BETWEEN 0 AND 60),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    exceptions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_availability_times CHECK (end_time_local > start_time_local)
);

CREATE TABLE IF NOT EXISTS public.meeting_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    alumni_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    mentor_request_id UUID NULL REFERENCES public.mentor_requests(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    purpose TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30 CHECK (duration_minutes IN (15, 30, 45, 60, 90)),
    student_timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'declined', 'counter_proposed', 'cancelled', 'expired')),
    decline_reason TEXT NULL,
    idempotency_key VARCHAR(128) NULL UNIQUE,
    expires_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_meeting_req_distinct_users CHECK (student_id <> alumni_id)
);

CREATE TABLE IF NOT EXISTS public.meeting_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_request_id UUID NOT NULL REFERENCES public.meeting_requests(id) ON DELETE CASCADE,
    proposed_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL DEFAULT 1 CHECK (round_number >= 1),
    start_utc TIMESTAMPTZ NOT NULL,
    end_utc TIMESTAMPTZ NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed', 'selected', 'rejected', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_meeting_slot_window CHECK (end_utc > start_utc)
);

CREATE TABLE IF NOT EXISTS public.meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_request_id UUID NULL UNIQUE REFERENCES public.meeting_requests(id) ON DELETE SET NULL,
    student_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    alumni_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    purpose TEXT NOT NULL,
    scheduled_start TIMESTAMPTZ NOT NULL,
    scheduled_end TIMESTAMPTZ NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show')),
    rescheduled_from_meeting_id UUID NULL REFERENCES public.meetings(id) ON DELETE SET NULL,
    cancellation_reason TEXT NULL,
    cancelled_by UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
    student_rating INTEGER NULL CHECK (student_rating BETWEEN 1 AND 5),
    student_feedback TEXT NULL,
    alumni_notes TEXT NULL,
    reminder_sent_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_meeting_window CHECK (scheduled_end > scheduled_start),
    CONSTRAINT chk_meeting_distinct_users CHECK (student_id <> alumni_id),
    CONSTRAINT excl_alumni_no_overlapping_meetings EXCLUDE USING gist (
        alumni_id WITH =,
        tstzrange(scheduled_start, scheduled_end, '[)') WITH &&
    ) WHERE (status IN ('scheduled', 'in_progress')),
    CONSTRAINT excl_student_no_overlapping_meetings EXCLUDE USING gist (
        student_id WITH =,
        tstzrange(scheduled_start, scheduled_end, '[)') WITH &&
    ) WHERE (status IN ('scheduled', 'in_progress'))
);

CREATE INDEX IF NOT EXISTS idx_alumni_availability_user ON public.alumni_availability(alumni_id, day_of_week);
CREATE INDEX IF NOT EXISTS idx_meeting_requests_student ON public.meeting_requests(student_id, status);
CREATE INDEX IF NOT EXISTS idx_meeting_requests_alumni ON public.meeting_requests(alumni_id, status);
CREATE INDEX IF NOT EXISTS idx_meeting_slots_request ON public.meeting_slots(meeting_request_id, round_number);
CREATE INDEX IF NOT EXISTS idx_meetings_alumni_start ON public.meetings(alumni_id, scheduled_start);
CREATE INDEX IF NOT EXISTS idx_meetings_student_start ON public.meetings(student_id, scheduled_start);

-- ============================================================================
-- 2. REAL-TIME MESSAGING & SAFETY (6 TABLES)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_one_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    participant_two_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    last_message_at TIMESTAMPTZ NULL,
    last_message_preview VARCHAR(255) NULL,
    last_seq BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_conversation_canonical_order CHECK (participant_one_id < participant_two_id),
    CONSTRAINT uq_conversation_pair UNIQUE (participant_one_id, participant_two_id)
);

CREATE TABLE IF NOT EXISTS public.conversation_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    last_read_seq BIGINT NOT NULL DEFAULT 0,
    last_delivered_seq BIGINT NOT NULL DEFAULT 0,
    unread_count INTEGER NOT NULL DEFAULT 0 CHECK (unread_count >= 0),
    is_muted BOOLEAN NOT NULL DEFAULT FALSE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_conversation_participant UNIQUE (conversation_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    seq BIGINT NOT NULL,
    body TEXT NOT NULL,
    message_type VARCHAR(32) NOT NULL DEFAULT 'text'
        CHECK (message_type IN ('text', 'attachment', 'system', 'meeting_invite')),
    status VARCHAR(32) NOT NULL DEFAULT 'sent'
        CHECK (status IN ('sent', 'delivered', 'read')),
    client_idempotency_key VARCHAR(128) NULL,
    reply_to_message_id UUID NULL REFERENCES public.messages(id) ON DELETE SET NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    edited_at TIMESTAMPTZ NULL,
    CONSTRAINT uq_message_conv_seq UNIQUE (conversation_id, seq),
    CONSTRAINT uq_message_client_idempotency UNIQUE (conversation_id, sender_id, client_idempotency_key)
);

CREATE TABLE IF NOT EXISTS public.message_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
    uploader_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 26214400),
    sha256_checksum VARCHAR(64) NOT NULL,
    storage_path TEXT NOT NULL,
    scan_status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (scan_status IN ('pending', 'clean', 'quarantined', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.user_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    blocked_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    reason VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_block_distinct CHECK (blocker_id <> blocked_id),
    CONSTRAINT uq_user_block UNIQUE (blocker_id, blocked_id)
);

CREATE TABLE IF NOT EXISTS public.user_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    reported_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    message_id UUID NULL REFERENCES public.messages(id) ON DELETE SET NULL,
    category VARCHAR(64) NOT NULL CHECK (category IN ('spam', 'harassment', 'impersonation', 'inappropriate', 'other')),
    description TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'under_review', 'resolved', 'dismissed')),
    reviewed_by UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
    resolution_notes TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_conv_participants_user ON public.conversation_participants(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conv_seq ON public.messages(conversation_id, seq);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON public.messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_user_blocks_pair ON public.user_blocks(blocker_id, blocked_id);
CREATE INDEX IF NOT EXISTS idx_user_reports_status ON public.user_reports(status);

-- ============================================================================
-- 3. REAL-TIME AUDIO/VIDEO MEETING ROOMS (2 TABLES)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.meeting_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL UNIQUE REFERENCES public.meetings(id) ON DELETE CASCADE,
    provider VARCHAR(32) NOT NULL DEFAULT 'livekit',
    room_name VARCHAR(128) NOT NULL UNIQUE,
    room_sid VARCHAR(128) NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'waiting'
        CHECK (status IN ('waiting', 'active', 'ended', 'expired')),
    host_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    waiting_room_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    recording_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    started_at TIMESTAMPTZ NULL,
    ended_at TIMESTAMPTZ NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.meeting_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES public.meeting_rooms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL DEFAULT 'participant' CHECK (role IN ('host', 'participant')),
    admission_status VARCHAR(32) NOT NULL DEFAULT 'waiting'
        CHECK (admission_status IN ('waiting', 'admitted', 'removed', 'left')),
    joined_at TIMESTAMPTZ NULL,
    left_at TIMESTAMPTZ NULL,
    connection_quality VARCHAR(32) NULL,
    audio_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    video_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    screen_sharing BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_meeting_room_participant UNIQUE (room_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_meeting_rooms_status ON public.meeting_rooms(status);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_room ON public.meeting_participants(room_id);

-- ============================================================================
-- 4. AI PROVIDER ENCRYPTED VAULT & USAGE LEDGER (2 TABLES)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ai_provider_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(32) NOT NULL CHECK (provider IN ('gemini', 'openai', 'anthropic', 'deepseek')),
    display_name VARCHAR(120) NOT NULL,
    model_id VARCHAR(120) NOT NULL,
    encrypted_api_key TEXT NOT NULL,
    nonce VARCHAR(64) NOT NULL,
    key_version INTEGER NOT NULL DEFAULT 1,
    key_hint VARCHAR(32) NOT NULL,
    capabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_priority INTEGER NOT NULL DEFAULT 100,
    verification_status VARCHAR(32) NOT NULL DEFAULT 'unverified'
        CHECK (verification_status IN ('unverified', 'verified', 'failed')),
    last_verified_at TIMESTAMPTZ NULL,
    daily_budget_usd NUMERIC(10, 4) NOT NULL DEFAULT 10.0000,
    monthly_budget_usd NUMERIC(10, 4) NOT NULL DEFAULT 100.0000,
    requests_per_minute_limit INTEGER NOT NULL DEFAULT 60 CHECK (requests_per_minute_limit > 0),
    configured_by UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ai_provider_model UNIQUE (provider, model_id)
);

CREATE TABLE IF NOT EXISTS public.ai_usage_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_config_id UUID NULL REFERENCES public.ai_provider_configs(id) ON DELETE SET NULL,
    provider VARCHAR(32) NOT NULL,
    model_id VARCHAR(120) NOT NULL,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    run_id UUID NULL REFERENCES public.agent_runs(id) ON DELETE SET NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0 CHECK (prompt_tokens >= 0),
    output_tokens INTEGER NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
    thinking_tokens INTEGER NOT NULL DEFAULT 0 CHECK (thinking_tokens >= 0),
    total_tokens INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    estimated_cost_usd NUMERIC(12, 6) NOT NULL DEFAULT 0.000000,
    latency_ms INTEGER NOT NULL DEFAULT 0 CHECK (latency_ms >= 0),
    status VARCHAR(32) NOT NULL DEFAULT 'completed',
    error_code VARCHAR(64) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_provider_enabled ON public.ai_provider_configs(is_enabled, is_primary);
CREATE INDEX IF NOT EXISTS idx_ai_usage_ledger_user ON public.ai_usage_ledger(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_ai_usage_ledger_provider ON public.ai_usage_ledger(provider, created_at);

-- ============================================================================
-- 5. PUSH NOTIFICATIONS, OUTBOX & IDEMPOTENCY (3 TABLES)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.push_device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token VARCHAR(512) NOT NULL UNIQUE,
    platform VARCHAR(16) NOT NULL CHECK (platform IN ('android', 'ios', 'web')),
    device_name VARCHAR(128) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id VARCHAR(128) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    schema_version VARCHAR(16) NOT NULL DEFAULT '1.0',
    actor_id UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(24) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'dispatched', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    dispatched_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.idempotency_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope VARCHAR(64) NOT NULL,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    idempotency_key VARCHAR(128) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    response_status INTEGER NOT NULL,
    response_body JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_idempotency_scope_user_key UNIQUE (scope, user_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_push_tokens_user ON public.push_device_tokens(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_outbox_pending ON public.outbox_events(status, available_at);
CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON public.idempotency_keys(expires_at);

-- ============================================================================
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE public.alumni_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_provider_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_usage_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.push_device_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.idempotency_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "alumni_availability_select" ON public.alumni_availability
    FOR SELECT TO authenticated USING (is_active = TRUE OR auth.uid() = alumni_id);
CREATE POLICY "alumni_availability_own" ON public.alumni_availability
    FOR ALL TO authenticated USING (auth.uid() = alumni_id) WITH CHECK (auth.uid() = alumni_id);

CREATE POLICY "meeting_requests_participants" ON public.meeting_requests
    FOR SELECT TO authenticated USING (auth.uid() IN (student_id, alumni_id));
CREATE POLICY "meetings_participants" ON public.meetings
    FOR SELECT TO authenticated USING (auth.uid() IN (student_id, alumni_id));

CREATE POLICY "conversations_participants" ON public.conversations
    FOR SELECT TO authenticated USING (auth.uid() IN (participant_one_id, participant_two_id));
CREATE POLICY "conversation_participants_own" ON public.conversation_participants
    FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "messages_participants" ON public.messages
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.conversation_participants cp
            WHERE cp.conversation_id = messages.conversation_id AND cp.user_id = auth.uid()
        )
    );

CREATE POLICY "user_blocks_own" ON public.user_blocks
    FOR ALL TO authenticated USING (auth.uid() = blocker_id) WITH CHECK (auth.uid() = blocker_id);
CREATE POLICY "user_reports_own" ON public.user_reports
    FOR SELECT TO authenticated USING (auth.uid() = reporter_id);

CREATE POLICY "push_device_tokens_own" ON public.push_device_tokens
    FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "ai_usage_ledger_own" ON public.ai_usage_ledger
    FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "idempotency_keys_own" ON public.idempotency_keys
    FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
