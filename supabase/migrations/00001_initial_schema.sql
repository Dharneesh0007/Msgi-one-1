-- ====================================================================
-- MSGI One — Phase 0 Initial Schema Migration (00001_initial_schema.sql)
-- Architecture: PostgreSQL 15+ with pgvector & Supabase Row-Level Security
-- ====================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ====================================================================
-- 2. Identity & Access Domain
-- ====================================================================

-- Roles Definition Table
CREATE TABLE IF NOT EXISTS public.roles (
    id VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL
);

INSERT INTO public.roles (id, description) VALUES
    ('student', 'Active matriculated student'),
    ('alumni', 'Verified graduate holding an institutional degree'),
    ('faculty', 'Academic faculty, professor, or researcher'),
    ('recruiter', 'Verified corporate hiring manager or placement recruiter'),
    ('admin', 'Institutional system administrator')
ON CONFLICT (id) DO NOTHING;

-- Core Users Table (Proxies Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    avatar_url TEXT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

-- User Roles Junction Table
CREATE TABLE IF NOT EXISTS public.user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role_id VARCHAR(50) NOT NULL REFERENCES public.roles(id) ON DELETE RESTRICT,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_by UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
    UNIQUE (user_id, role_id)
);

-- Alumni Profiles
CREATE TABLE IF NOT EXISTS public.alumni_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    graduation_year INTEGER NOT NULL CHECK (graduation_year BETWEEN 1950 AND 2035),
    degree VARCHAR(100) NOT NULL,
    major VARCHAR(100) NOT NULL,
    headline VARCHAR(255) NULL,
    bio TEXT NULL,
    current_company VARCHAR(150) NULL,
    current_title VARCHAR(150) NULL,
    industry VARCHAR(100) NULL,
    embedding vector(1536) NULL,
    visibility VARCHAR(30) NOT NULL DEFAULT 'institutional' CHECK (visibility IN ('public', 'institutional', 'connections_only', 'private')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Student Profiles
CREATE TABLE IF NOT EXISTS public.student_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    roll_number VARCHAR(50) NOT NULL UNIQUE,
    enrollment_year INTEGER NOT NULL CHECK (enrollment_year BETWEEN 2015 AND 2035),
    expected_graduation_year INTEGER NOT NULL CHECK (expected_graduation_year >= enrollment_year),
    department VARCHAR(100) NOT NULL,
    degree_program VARCHAR(100) NOT NULL,
    cgpa NUMERIC(3, 2) NULL CHECK (cgpa >= 0.00 AND cgpa <= 10.00),
    resume_url TEXT NULL,
    career_interests TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Faculty Profiles
CREATE TABLE IF NOT EXISTS public.faculty_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    department VARCHAR(100) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    research_interests TEXT[] NOT NULL DEFAULT '{}',
    office_location VARCHAR(100) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Recruiter Profiles
CREATE TABLE IF NOT EXISTS public.recruiter_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    company_name VARCHAR(150) NOT NULL,
    company_website VARCHAR(255) NULL,
    corporate_email VARCHAR(255) NOT NULL,
    verification_status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (verification_status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- User Preferences
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    push_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_digests_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    theme VARCHAR(20) NOT NULL DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Consent Records (FERPA / GDPR)
CREATE TABLE IF NOT EXISTS public.consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL CHECK (consent_type IN ('directory_listing', 'ai_profiling', 'recruiter_contact', 'location_sharing')),
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ NULL,
    UNIQUE (user_id, consent_type)
);

-- ====================================================================
-- 3. Professional & Networking Domain
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL CHECK (category IN ('technical', 'business', 'design', 'soft_skill', 'language')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.user_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE CASCADE,
    proficiency VARCHAR(30) NOT NULL DEFAULT 'intermediate' CHECK (proficiency IN ('beginner', 'intermediate', 'advanced', 'expert')),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (user_id, skill_id)
);

CREATE TABLE IF NOT EXISTS public.employment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alumni_id UUID NOT NULL REFERENCES public.alumni_profiles(id) ON DELETE CASCADE,
    company_name VARCHAR(150) NOT NULL,
    title VARCHAR(150) NOT NULL,
    location VARCHAR(100) NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.alumni_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    country_code VARCHAR(2) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    chapter_name VARCHAR(100) NULL,
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    addressee_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (requester_id != addressee_id),
    UNIQUE (requester_id, addressee_id)
);

-- ====================================================================
-- 4. Career & Mentorship Domain
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    posted_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    company_name VARCHAR(150) NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    employment_type VARCHAR(50) NOT NULL CHECK (employment_type IN ('full_time', 'part_time', 'internship', 'contract', 'remote')),
    location VARCHAR(100) NOT NULL,
    salary_min INTEGER NULL,
    salary_max INTEGER NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    required_skills TEXT[] NOT NULL DEFAULT '{}',
    application_deadline TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    embedding vector(1536) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.job_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    applicant_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resume_url TEXT NOT NULL,
    cover_letter TEXT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'under_review', 'shortlisted', 'rejected', 'offered')),
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, applicant_id)
);

CREATE TABLE IF NOT EXISTS public.mentor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alumni_id UUID NOT NULL UNIQUE REFERENCES public.alumni_profiles(id) ON DELETE CASCADE,
    topics TEXT[] NOT NULL DEFAULT '{}',
    max_mentees INTEGER NOT NULL DEFAULT 3 CHECK (max_mentees BETWEEN 1 AND 20),
    active_mentees INTEGER NOT NULL DEFAULT 0 CHECK (active_mentees >= 0),
    is_accepting_requests BOOLEAN NOT NULL DEFAULT TRUE,
    meeting_preference VARCHAR(30) NOT NULL DEFAULT 'virtual' CHECK (meeting_preference IN ('virtual', 'in_person', 'both')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.mentor_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentee_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    mentor_id UUID NOT NULL REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
    goal_statement TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'completed', 'cancelled')),
    rejection_reason TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.mentor_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES public.mentor_requests(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ NOT NULL,
    meeting_link TEXT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show')),
    mentor_notes TEXT NULL,
    mentee_feedback TEXT NULL,
    rating INTEGER NULL CHECK (rating BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.career_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.student_profiles(id) ON DELETE CASCADE,
    target_role VARCHAR(150) NOT NULL,
    target_country VARCHAR(100) NOT NULL,
    target_industry VARCHAR(100) NOT NULL,
    target_date DATE NULL,
    skill_gap_summary JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ====================================================================
-- 5. Engagement & Communities Domain
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organizer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('reunion', 'webinar', 'networking', 'career_fair', 'workshop')),
    location_type VARCHAR(20) NOT NULL CHECK (location_type IN ('in_person', 'virtual', 'hybrid')),
    venue_address TEXT NULL,
    virtual_link TEXT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL CHECK (end_time > start_time),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    registered_count INTEGER NOT NULL DEFAULT 0 CHECK (registered_count <= capacity),
    banner_url TEXT NULL,
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.event_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'registered' CHECK (status IN ('registered', 'attended', 'cancelled')),
    ticket_code VARCHAR(50) NOT NULL UNIQUE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (event_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.communities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    privacy VARCHAR(30) NOT NULL DEFAULT 'public' CHECK (privacy IN ('public', 'private', 'invite_only')),
    member_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.community_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id UUID NOT NULL REFERENCES public.communities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'moderator', 'admin')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (community_id, user_id)
);

-- ====================================================================
-- 6. Learning & Innovation Domain
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    provider VARCHAR(100) NOT NULL DEFAULT 'MSGI Academy',
    course_url TEXT NULL,
    difficulty VARCHAR(30) NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    associated_skills TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.learning_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('not_started', 'in_progress', 'completed')),
    progress_percent INTEGER NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),
    completed_at TIMESTAMPTZ NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, course_id)
);

CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    abstract TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'recruiting' CHECK (status IN ('recruiting', 'in_progress', 'completed', 'archived')),
    required_skills TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL DEFAULT 'contributor',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.startups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    founder_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    pitch_summary TEXT NOT NULL,
    industry VARCHAR(100) NOT NULL,
    stage VARCHAR(50) NOT NULL CHECK (stage IN ('idea', 'mvp', 'seed', 'growth', 'profitable')),
    website VARCHAR(255) NULL,
    deck_url TEXT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.startup_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    startup_id UUID NOT NULL REFERENCES public.startups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role_title VARCHAR(100) NOT NULL,
    is_cofounder BOOLEAN NOT NULL DEFAULT FALSE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (startup_id, user_id)
);

-- ====================================================================
-- 7. Institutional Operations Domain
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.impact_programmes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    target_amount NUMERIC(12, 2) NOT NULL CHECK (target_amount > 0),
    raised_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (raised_amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.donation_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    programme_id UUID NOT NULL REFERENCES public.impact_programmes(id) ON DELETE RESTRICT,
    donor_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    transaction_reference VARCHAR(100) NOT NULL UNIQUE,
    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(30) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.volunteering_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    hours_contributed NUMERIC(6, 2) NOT NULL CHECK (hours_contributed > 0),
    date_completed DATE NOT NULL,
    verified_by UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.institutional_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    file_url TEXT NOT NULL,
    content_text TEXT NOT NULL,
    embedding vector(1536) NULL,
    uploaded_by UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ====================================================================
-- 8. AI & Observability Domain
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    workflow_type VARCHAR(100) NOT NULL,
    prompt_input TEXT NOT NULL,
    state_graph_snapshot JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(30) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'awaiting_approval', 'failed', 'cancelled')),
    final_output JSONB NULL,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES public.agent_runs(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    tool_input JSONB NOT NULL,
    tool_output JSONB NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'error', 'blocked')),
    execution_time_ms INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES public.agent_runs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL CHECK (action_type IN ('send_mentor_request', 'contact_alumni', 'apply_job', 'publish_event', 'update_record', 'financial_action')),
    payload JSONB NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    decision_reason TEXT NULL,
    decided_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('mentorship', 'career', 'event', 'ai_approval', 'system')),
    metadata JSONB NOT NULL DEFAULT '{}',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NULL,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    previous_state JSONB NULL,
    new_state JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ====================================================================
-- 9. Performance Indexes
-- ====================================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON public.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_alumni_profiles_user_id ON public.alumni_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_alumni_profiles_grad_year ON public.alumni_profiles(graduation_year);
CREATE INDEX IF NOT EXISTS idx_student_profiles_user_id ON public.student_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_is_active_deadline ON public.jobs(is_active, application_deadline);
CREATE INDEX IF NOT EXISTS idx_job_applications_job_id ON public.job_applications(job_id);
CREATE INDEX IF NOT EXISTS idx_mentor_requests_mentor_id ON public.mentor_requests(mentor_id);
CREATE INDEX IF NOT EXISTS idx_events_start_time ON public.events(start_time);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_agent_runs_user_id ON public.agent_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_user_id ON public.approval_requests(user_id, status);

-- pgvector HNSW Cosine Distance Indexes
CREATE INDEX IF NOT EXISTS idx_alumni_profiles_embedding ON public.alumni_profiles 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_jobs_embedding ON public.jobs 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_institutional_documents_embedding ON public.institutional_documents 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
