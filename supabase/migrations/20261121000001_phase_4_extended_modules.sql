-- ============================================================================
-- MSGI ONE — PHASE 4 MIGRATION: EXTENDED MVP MODULES & REALTIME NOTIFICATIONS
-- Migration: 20261121000001_phase_4_extended_modules.sql
-- Principles:
--   - Abraham Silberschatz: Strong relational invariants, foreign keys, CHECK constraints
--   - Martin Kleppmann: Reliable event propagation, append-only notification logs
--   - Eric Evans: Bounded contexts for Learning, Communities, Administration, Projects, Startups, Impact
-- ============================================================================

-- 1. MODULE 9: LEARNING ACADEMY (ENROLLMENTS & PROGRESS)
CREATE TABLE IF NOT EXISTS public.course_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resource_id VARCHAR(64) NOT NULL REFERENCES public.learning_resources(resource_id) ON DELETE CASCADE,
    progress_percentage INTEGER NOT NULL DEFAULT 0
        CHECK (progress_percentage BETWEEN 0 AND 100),
    status VARCHAR(32) NOT NULL DEFAULT 'enrolled'
        CHECK (status IN ('enrolled', 'in_progress', 'completed', 'dropped')),
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_course_enrollment UNIQUE (user_id, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_course_enrollments_user ON public.course_enrollments (user_id);
CREATE INDEX IF NOT EXISTS idx_course_enrollments_resource ON public.course_enrollments (resource_id);

-- 2. MODULE 10: COMMUNITIES & INTEREST GROUPS
CREATE TABLE IF NOT EXISTS public.communities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    slug VARCHAR(128) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'Technology',
    is_private BOOLEAN NOT NULL DEFAULT false,
    creator_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    member_count INTEGER NOT NULL DEFAULT 1 CHECK (member_count >= 0),
    topics TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_communities_category ON public.communities (category);

CREATE TABLE IF NOT EXISTS public.community_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id UUID NOT NULL REFERENCES public.communities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL DEFAULT 'member'
        CHECK (role IN ('member', 'moderator', 'admin')),
    status VARCHAR(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('pending', 'active', 'rejected', 'banned')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_community_membership UNIQUE (community_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_community_memberships_user ON public.community_memberships (user_id);
CREATE INDEX IF NOT EXISTS idx_community_memberships_comm ON public.community_memberships (community_id);

-- 3. MODULE 12: INSTITUTIONAL ADMINISTRATION & VERIFICATIONS
CREATE TABLE IF NOT EXISTS public.verification_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    requested_role VARCHAR(32) NOT NULL
        CHECK (requested_role IN ('alumni', 'faculty', 'recruiter')),
    evidence_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    review_notes TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_pending_verification UNIQUE (user_id, requested_role, status)
);

CREATE INDEX IF NOT EXISTS idx_verification_requests_status ON public.verification_requests (status);

CREATE TABLE IF NOT EXISTS public.admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    action VARCHAR(64) NOT NULL,
    target_type VARCHAR(64) NOT NULL,
    target_id VARCHAR(128) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin ON public.admin_audit_logs (admin_id);

-- 4. MODULE 7: COLLABORATION & INNOVATION HUB (P1)
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    owner_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    required_skills TEXT[] NOT NULL DEFAULT '{}',
    status VARCHAR(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'archived')),
    member_count INTEGER NOT NULL DEFAULT 1 CHECK (member_count >= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL DEFAULT 'contributor'
        CHECK (role IN ('owner', 'contributor', 'applicant')),
    status VARCHAR(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('pending', 'active', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_project_member UNIQUE (project_id, user_id)
);

-- 5. MODULE 8: STARTUP ECOSYSTEM (P1)
CREATE TABLE IF NOT EXISTS public.startups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    founder_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    industry VARCHAR(64) NOT NULL,
    stage VARCHAR(32) NOT NULL DEFAULT 'seed'
        CHECK (stage IN ('idea', 'seed', 'early', 'growth', 'mature')),
    tagline TEXT NOT NULL,
    website_url TEXT,
    seeking_mentors BOOLEAN NOT NULL DEFAULT true,
    seeking_talent BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.startup_connection_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    startup_id UUID NOT NULL REFERENCES public.startups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    intent VARCHAR(32) NOT NULL DEFAULT 'mentorship'
        CHECK (intent IN ('mentorship', 'talent', 'collaboration')),
    message TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'declined')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_startup_connection UNIQUE (startup_id, user_id)
);

-- 6. MODULE 11: GIVING AND SOCIAL IMPACT (P1)
CREATE TABLE IF NOT EXISTS public.impact_programmes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    coordinator_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    programme_type VARCHAR(64) NOT NULL DEFAULT 'volunteering'
        CHECK (programme_type IN ('volunteering', 'mentorship_drive', 'community_outreach')),
    target_volunteers INTEGER NOT NULL DEFAULT 10 CHECK (target_volunteers > 0),
    current_volunteers INTEGER NOT NULL DEFAULT 0 CHECK (current_volunteers >= 0),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.volunteer_interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    programme_id UUID NOT NULL REFERENCES public.impact_programmes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    interest_note TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'registered'
        CHECK (status IN ('registered', 'confirmed', 'withdrawn')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_volunteer_interest UNIQUE (programme_id, user_id)
);

-- 7. UNIFIED REALTIME NOTIFICATIONS MODEL
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON public.notifications (user_id, is_read);

-- 8. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE public.course_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.communities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.startups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.startup_connection_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.impact_programmes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Course Enrollments: Users manage their own
CREATE POLICY "Users can manage their own course enrollments"
    ON public.course_enrollments FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Communities: Public communities viewable by all authenticated
CREATE POLICY "Anyone authenticated can view public communities"
    ON public.communities FOR SELECT TO authenticated
    USING (is_private = false OR creator_id = auth.uid() OR EXISTS (
        SELECT 1 FROM public.community_memberships cm
        WHERE cm.community_id = communities.id AND cm.user_id = auth.uid() AND cm.status = 'active'
    ));

-- Community Memberships: Users manage their own; moderators manage community
CREATE POLICY "Users can view and request their own community memberships"
    ON public.community_memberships FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Verification Requests: Users view their own; admins manage all
CREATE POLICY "Users view own verification requests"
    ON public.verification_requests FOR SELECT TO authenticated
    USING (user_id = auth.uid());

-- Notifications: Strictly owner-isolated
CREATE POLICY "Users access own notifications only"
    ON public.notifications FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
