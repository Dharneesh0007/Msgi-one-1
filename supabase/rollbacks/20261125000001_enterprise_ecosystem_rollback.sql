-- ============================================================================
-- MSGI ONE — ROLLBACK / RECOVERY SCRIPT FOR 20261125000001_enterprise_ecosystem.sql
-- Stored outside supabase/migrations/ so automated forward migrations never execute it.
-- Execute ONLY under explicit owner authorization during a verified rollback drill.
-- ============================================================================

DROP TABLE IF EXISTS public.idempotency_keys CASCADE;
DROP TABLE IF EXISTS public.outbox_events CASCADE;
DROP TABLE IF EXISTS public.push_device_tokens CASCADE;
DROP TABLE IF EXISTS public.ai_usage_ledger CASCADE;
DROP TABLE IF EXISTS public.ai_provider_configs CASCADE;
DROP TABLE IF EXISTS public.meeting_participants CASCADE;
DROP TABLE IF EXISTS public.meeting_rooms CASCADE;
DROP TABLE IF EXISTS public.user_reports CASCADE;
DROP TABLE IF EXISTS public.user_blocks CASCADE;
DROP TABLE IF EXISTS public.message_attachments CASCADE;
DROP TABLE IF EXISTS public.messages CASCADE;
DROP TABLE IF EXISTS public.conversation_participants CASCADE;
DROP TABLE IF EXISTS public.conversations CASCADE;
DROP TABLE IF EXISTS public.meetings CASCADE;
DROP TABLE IF EXISTS public.meeting_slots CASCADE;
DROP TABLE IF EXISTS public.meeting_requests CASCADE;
DROP TABLE IF EXISTS public.alumni_availability CASCADE;
