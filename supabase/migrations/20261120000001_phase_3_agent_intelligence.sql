-- ============================================================================
-- MSGI ONE — PHASE 3 MIGRATION: AGENTIC AI INTELLIGENCE & AUDIT TRAIL
-- Migration: 20261120000001_phase_3_agent_intelligence.sql
-- Principles:
--   - Silberschatz: Referential integrity, CHECK constraints, non-null guarantees
--   - Kleppmann: Immutable action logs, state machines for approval workflows
--   - Evans: Domain models for Career Role Skills, Learning Resources, Approvals
-- ============================================================================

-- 1. CAREER ROLE SKILLS (Deterministic Taxonomy & Weights)
CREATE TABLE IF NOT EXISTS public.career_role_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id VARCHAR(64) NOT NULL,
    role_name VARCHAR(128) NOT NULL,
    skill_name VARCHAR(128) NOT NULL,
    required_level VARCHAR(32) NOT NULL DEFAULT 'Intermediate'
        CHECK (required_level IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
    importance_weight INTEGER NOT NULL DEFAULT 3
        CHECK (importance_weight BETWEEN 1 AND 5),
    category VARCHAR(64) NOT NULL DEFAULT 'Technical',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_career_role_skill UNIQUE (role_id, skill_name)
);

CREATE INDEX IF NOT EXISTS idx_career_role_skills_role ON public.career_role_skills (role_id);
CREATE INDEX IF NOT EXISTS idx_career_role_skills_name ON public.career_role_skills (skill_name);

-- 2. LEARNING RESOURCES (Curated Courseware for Roadmaps)
CREATE TABLE IF NOT EXISTS public.learning_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    provider VARCHAR(128) NOT NULL,
    target_skill VARCHAR(128) NOT NULL,
    difficulty VARCHAR(32) NOT NULL DEFAULT 'Intermediate'
        CHECK (difficulty IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
    duration_hours NUMERIC(5, 1) NOT NULL CHECK (duration_hours > 0),
    url TEXT NOT NULL,
    rating NUMERIC(3, 2) NOT NULL DEFAULT 4.5 CHECK (rating BETWEEN 0.0 AND 5.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_learning_resources_skill ON public.learning_resources (target_skill);

-- 3. STUDENT SKILLS (User Baseline Proficiency)
CREATE TABLE IF NOT EXISTS public.student_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    skill_name VARCHAR(128) NOT NULL,
    proficiency_level VARCHAR(32) NOT NULL DEFAULT 'Beginner'
        CHECK (proficiency_level IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
    years_experience INTEGER NOT NULL DEFAULT 0 CHECK (years_experience >= 0),
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_student_skill UNIQUE (user_id, skill_name)
);

CREATE INDEX IF NOT EXISTS idx_student_skills_user ON public.student_skills (user_id);

-- 4. AGENT RUNS (Workflow & Command Centre Execution Audit)
CREATE TABLE IF NOT EXISTS public.agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    session_id VARCHAR(128) NOT NULL,
    intent VARCHAR(64) NOT NULL,
    prompt_summary TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'interrupted', 'completed', 'failed', 'rejected')),
    total_tokens INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    latency_ms INTEGER NOT NULL DEFAULT 0 CHECK (latency_ms >= 0),
    routing_decision JSONB NOT NULL DEFAULT '{}'::jsonb,
    final_response JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_user ON public.agent_runs (user_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_session ON public.agent_runs (session_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON public.agent_runs (status);

-- 5. AGENT ACTIONS (Granular Tool Invocations & Observability)
CREATE TABLE IF NOT EXISTS public.agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES public.agent_runs(id) ON DELETE CASCADE,
    agent_name VARCHAR(64) NOT NULL,
    tool_name VARCHAR(64) NOT NULL,
    action_input JSONB NOT NULL DEFAULT '{}'::jsonb,
    action_output JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'success'
        CHECK (status IN ('success', 'failed', 'pending_approval', 'rejected')),
    latency_ms INTEGER NOT NULL DEFAULT 0 CHECK (latency_ms >= 0),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_actions_run ON public.agent_actions (run_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_tool ON public.agent_actions (tool_name);

-- 6. APPROVAL REQUESTS (Human-In-The-Loop Consequential Gateways)
CREATE TABLE IF NOT EXISTS public.approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES public.agent_runs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    action_type VARCHAR(64) NOT NULL
        CHECK (action_type IN ('send_mentor_request', 'apply_job', 'register_event')),
    action_payload JSONB NOT NULL,
    target_entity_id VARCHAR(128) NOT NULL,
    target_entity_name VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    decision_note TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_approval_requests_user ON public.approval_requests (user_id, status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_idempotency ON public.approval_requests (idempotency_key);

-- 7. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE public.career_role_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_requests ENABLE ROW LEVEL SECURITY;

-- Read policies for reference data
CREATE POLICY "Anyone authenticated can view role skills"
    ON public.career_role_skills FOR SELECT TO authenticated USING (true);

CREATE POLICY "Anyone authenticated can view learning resources"
    ON public.learning_resources FOR SELECT TO authenticated USING (true);

-- Student Skills policies (Users manage their own skills)
CREATE POLICY "Users can manage their own skills"
    ON public.student_skills FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Agent Runs & Actions (Users view their own runs)
CREATE POLICY "Users can view their own agent runs"
    ON public.agent_runs FOR SELECT TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can view actions from their own runs"
    ON public.agent_actions FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM public.agent_runs r
        WHERE r.id = agent_actions.run_id AND r.user_id = auth.uid()
    ));

-- Approval Requests policies
CREATE POLICY "Users can view and decide their own approval requests"
    ON public.approval_requests FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
