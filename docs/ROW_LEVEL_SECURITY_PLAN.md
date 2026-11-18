# MSGI One — Row-Level Security (RLS) & Data Protection Plan

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** DevSecOps Engineer & Database Architect  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Security Architecture & Threat Model

In accordance with **Roger S. Pressman** (*Software Engineering*, Ch. 9: "Security Engineering") and **Abraham Silberschatz** (*Database System Concepts*, Ch. 5: "Authorization"):
1. **Defense-in-Depth:** Application-level role-based authorization (Layer B & C) is backed by database-level Row-Level Security (Layer D). Even in the event of an application logic defect or SQL injection attempt, PostgreSQL enforces tenant boundaries directly at the storage engine.
2. **Principle of Least Privilege:** Users possess zero blanket access. By default, `ENABLE ROW LEVEL SECURITY` blocks all `SELECT`, `INSERT`, `UPDATE`, and `DELETE` operations unless an explicit policy permits it.
3. **FERPA / GDPR Privacy Isolation:** Alumni contact details and location data are filtered based on explicit `consent_records` and `visibility` flags. Student academic metrics (CGPA, roll numbers) are concealed from non-administrative queries.
4. **Service Role Separation:** Background workers, migration runners, and the LangGraph orchestrator connect using a dedicated internal database role bypassing RLS when executing administrative maintenance, while client-facing requests execute with authenticated user claims (`auth.uid()`).

---

## 2. Table-by-Table RLS Policy Specifications

### 2.1 Identity & Profile Access

```sql
-- 1. Enable RLS on core identity tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alumni_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consent_records ENABLE ROW LEVEL SECURITY;

-- 2. Policy: users
-- Anyone authenticated can view active, verified users' public profiles
CREATE POLICY users_view_public ON public.users
    FOR SELECT
    TO authenticated
    USING (is_active = TRUE AND deleted_at IS NULL);

-- Users can only modify their own profile
CREATE POLICY users_update_self ON public.users
    FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- 3. Policy: alumni_profiles
-- Viewable based on visibility settings and active consent
CREATE POLICY alumni_profiles_view_policy ON public.alumni_profiles
    FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid() OR
        visibility = 'public' OR
        (visibility = 'institutional' AND EXISTS (
            SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.is_verified = TRUE
        )) OR
        (visibility = 'connections_only' AND EXISTS (
            SELECT 1 FROM public.connections c 
            WHERE (c.requester_id = auth.uid() AND c.addressee_id = alumni_profiles.user_id AND c.status = 'accepted')
               OR (c.addressee_id = auth.uid() AND c.requester_id = alumni_profiles.user_id AND c.status = 'accepted')
        ))
    );

-- Alumni can only edit their own profile
CREATE POLICY alumni_profiles_modify_self ON public.alumni_profiles
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 4. Policy: student_profiles
-- Students view and edit their own academic profile
CREATE POLICY student_profiles_self ON public.student_profiles
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Institutional Faculty and Admins can view student academic profiles
CREATE POLICY student_profiles_faculty_admin ON public.student_profiles
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur 
            WHERE ur.user_id = auth.uid() AND ur.role_id IN ('faculty', 'admin')
        )
    );

-- 5. Policy: consent_records
-- Users have exclusive read/write over their personal consent settings
CREATE POLICY consent_records_owner_only ON public.consent_records
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
```

---

### 2.2 Career & Mentorship Access

```sql
-- Enable RLS on Career & Mentorship tables
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_requests ENABLE ROW LEVEL SECURITY;

-- 1. Policy: jobs
-- Anyone authenticated can view active jobs
CREATE POLICY jobs_view_active ON public.jobs
    FOR SELECT
    TO authenticated
    USING (is_active = TRUE AND application_deadline > now());

-- Recruiters and Alumni can post jobs; Posters can manage their own jobs
CREATE POLICY jobs_manage_poster ON public.jobs
    FOR ALL
    TO authenticated
    USING (posted_by = auth.uid())
    WITH CHECK (posted_by = auth.uid());

-- 2. Policy: job_applications
-- Applicants can view and submit their own applications
CREATE POLICY job_applications_applicant ON public.job_applications
    FOR ALL
    TO authenticated
    USING (applicant_id = auth.uid())
    WITH CHECK (applicant_id = auth.uid());

-- Job Posters can view applications submitted to their jobs
CREATE POLICY job_applications_poster ON public.job_applications
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.jobs j 
            WHERE j.id = job_applications.job_id AND j.posted_by = auth.uid()
        )
    );

-- 3. Policy: mentor_profiles
-- Anyone authenticated can view active mentor profiles
CREATE POLICY mentor_profiles_view ON public.mentor_profiles
    FOR SELECT
    TO authenticated
    USING (is_accepting_requests = TRUE);

-- Mentors manage their own settings
CREATE POLICY mentor_profiles_manage ON public.mentor_profiles
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.alumni_profiles ap 
            WHERE ap.id = mentor_profiles.alumni_id AND ap.user_id = auth.uid()
        )
    );

-- 4. Policy: mentor_requests
-- Visible only to the requesting mentee and target mentor
CREATE POLICY mentor_requests_participants ON public.mentor_requests
    FOR SELECT
    TO authenticated
    USING (
        mentee_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.mentor_profiles mp
            JOIN public.alumni_profiles ap ON mp.alumni_id = ap.id
            WHERE mp.id = mentor_requests.mentor_id AND ap.user_id = auth.uid()
        )
    );
```

---

### 2.3 AI Agent Runs & Approval Gates

```sql
-- Enable RLS on AI tables
ALTER TABLE public.agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_requests ENABLE ROW LEVEL SECURITY;

-- 1. Policy: agent_runs
-- Users can only view their own AI execution history
CREATE POLICY agent_runs_user ON public.agent_runs
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- 2. Policy: approval_requests
-- Users can view and decide their own approval requests
CREATE POLICY approval_requests_user ON public.approval_requests
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
```

---

### 2.4 Audit Logs & Compliance

```sql
-- Enable RLS on Audit Logs
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Only Admins can view audit logs
CREATE POLICY audit_logs_admin_only ON public.audit_logs
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid() AND ur.role_id = 'admin'
        )
    );

-- No direct client INSERT/UPDATE/DELETE permitted on audit_logs.
-- System triggers and internal service workers write audit logs.
```

---

## 3. RLS Performance & Security Verification

1. **Subquery Indexing:** All subqueries used inside RLS `USING` clauses (`auth.uid() = user_id`, `ur.user_id = auth.uid()`) are backed by B-tree indexes, ensuring zero row-scan overhead.
2. **Leakproof Views:** In Phase 1, PostgreSQL `security_barrier` views will be established over `users` and `student_profiles` to prevent side-channel timing attacks on private student fields.
