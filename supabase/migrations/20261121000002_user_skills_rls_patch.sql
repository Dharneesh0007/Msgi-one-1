-- ============================================================================
-- MSGI ONE — CORRECTION PATCH: ROW LEVEL SECURITY FOR public.user_skills
-- Migration: 20261121000002_user_skills_rls_patch.sql
-- Governance: MSGI One Executive Engineering Directive v2.0 (Correction 1)
-- Principles: Silberschatz (Least Privilege), Anderson (Trust Boundaries)
-- Status: PREPARED LOCALLY — AWAITING EXPLICIT PROJECT OWNER APPROVAL
-- ============================================================================

-- 1. Enable Row-Level Security on user_skills
ALTER TABLE public.user_skills ENABLE ROW LEVEL SECURITY;

-- 2. Owner-Scoped SELECT Policy
-- Users can only read their own skill associations
DROP POLICY IF EXISTS user_skills_select_owner ON public.user_skills;
CREATE POLICY user_skills_select_owner ON public.user_skills
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

-- 3. Owner-Scoped INSERT Policy
-- Users can only insert skill records assigned to their own user_id
DROP POLICY IF EXISTS user_skills_insert_owner ON public.user_skills;
CREATE POLICY user_skills_insert_owner ON public.user_skills
    FOR INSERT TO authenticated
    WITH CHECK (user_id = auth.uid());

-- 4. Owner-Scoped UPDATE Policy
-- Users can only modify their own skill records
DROP POLICY IF EXISTS user_skills_update_owner ON public.user_skills;
CREATE POLICY user_skills_update_owner ON public.user_skills
    FOR UPDATE TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 5. Owner-Scoped DELETE Policy
-- Users can only delete their own skill records
DROP POLICY IF EXISTS user_skills_delete_owner ON public.user_skills;
CREATE POLICY user_skills_delete_owner ON public.user_skills
    FOR DELETE TO authenticated
    USING (user_id = auth.uid());

-- 6. Grant appropriate permissions to authenticated role
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_skills TO authenticated;
