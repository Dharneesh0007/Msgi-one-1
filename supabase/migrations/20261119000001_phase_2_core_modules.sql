-- =====================================================================
-- MSGI ONE — CANONICAL POSTGRESQL MIGRATION: PHASE 2 CORE BUSINESS MODULES
-- Migration ID: 20261119000001_phase_2_core_modules
-- Modules: Alumni Network, CareerBridge, MentorMatch, Events, Global Connect
-- Principle: Referential Integrity (Silberschatz Ch. 3-4), Normalisation (3NF),
--            Transaction Consistency & Concurrency (Kleppmann Ch. 7)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. MODULE 3: MENTORMATCH TABLES
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.mentor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alumni_id UUID NOT NULL REFERENCES public.alumni_profiles(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    is_accepting_requests BOOLEAN NOT NULL DEFAULT TRUE,
    max_active_mentees INTEGER NOT NULL DEFAULT 3 CHECK (max_active_mentees > 0),
    current_active_mentees INTEGER NOT NULL DEFAULT 0 CHECK (current_active_mentees >= 0),
    advisory_topics TEXT[] NOT NULL DEFAULT '{}',
    preferred_frequency VARCHAR(50) DEFAULT 'bi-weekly',
    bio TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_mentor_profiles_alumni UNIQUE (alumni_id),
    CONSTRAINT uq_mentor_profiles_user UNIQUE (user_id),
    CONSTRAINT chk_mentee_capacity CHECK (current_active_mentees <= max_active_mentees)
);

CREATE TABLE IF NOT EXISTS public.mentor_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentor_id UUID NOT NULL REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    topic VARCHAR(100) NOT NULL,
    career_goal TEXT NOT NULL,
    message TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'accepted', 'rejected', 'completed', 'cancelled')),
    mentor_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Partial unique index ensuring student cannot have multiple active pending requests with same mentor
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_mentor_request 
    ON public.mentor_requests(mentor_id, student_id) 
    WHERE status = 'pending';

-- ---------------------------------------------------------------------
-- 2. MODULE 2: CAREERBRIDGE (JOBS & APPLICATIONS)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'Global',
    opportunity_type VARCHAR(50) NOT NULL DEFAULT 'full_time' 
        CHECK (opportunity_type IN ('full_time', 'internship', 'contract', 'part_time')),
    workplace_type VARCHAR(50) NOT NULL DEFAULT 'hybrid' 
        CHECK (workplace_type IN ('remote', 'hybrid', 'onsite')),
    description TEXT NOT NULL,
    requirements TEXT[] NOT NULL DEFAULT '{}',
    required_skills TEXT[] NOT NULL DEFAULT '{}',
    application_deadline TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified_listing BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.job_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    applicant_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'submitted' 
        CHECK (status IN ('submitted', 'under_review', 'interviewing', 'accepted', 'rejected', 'withdrawn')),
    resume_url TEXT,
    cover_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_job_applications_user UNIQUE (job_id, applicant_id)
);

-- ---------------------------------------------------------------------
-- 3. MODULE 4: EVENTS AND REUNIONS
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organizer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL DEFAULT 'webinar' 
        CHECK (event_type IN ('webinar', 'reunion', 'workshop', 'career_fair', 'conference')),
    description TEXT NOT NULL,
    location VARCHAR(255) NOT NULL,
    is_virtual BOOLEAN NOT NULL DEFAULT FALSE,
    meeting_url TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    max_capacity INTEGER NOT NULL DEFAULT 100 CHECK (max_capacity > 0),
    current_registrations INTEGER NOT NULL DEFAULT 0 CHECK (current_registrations >= 0),
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_event_times CHECK (end_time > start_time),
    CONSTRAINT chk_event_capacity CHECK (current_registrations <= max_capacity)
);

CREATE TABLE IF NOT EXISTS public.event_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'confirmed' 
        CHECK (status IN ('confirmed', 'attended', 'cancelled')),
    ticket_code VARCHAR(100) NOT NULL DEFAULT gen_random_uuid()::text,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_event_registrations_user UNIQUE (event_id, user_id)
);

-- ---------------------------------------------------------------------
-- 4. MODULE 5: GLOBAL ALUMNI CONNECT CHAPTERS
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.alumni_chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    lead_alumni_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_chapter_city UNIQUE (country, city)
);

-- ---------------------------------------------------------------------
-- 5. PERFORMANCE INDEXES
-- ---------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_mentor_profiles_user ON public.mentor_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_profiles_accepting ON public.mentor_profiles(is_accepting_requests);
CREATE INDEX IF NOT EXISTS idx_mentor_requests_mentor ON public.mentor_requests(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_requests_student ON public.mentor_requests(student_id);
CREATE INDEX IF NOT EXISTS idx_mentor_requests_status ON public.mentor_requests(status);

CREATE INDEX IF NOT EXISTS idx_jobs_active_type ON public.jobs(is_active, opportunity_type);
CREATE INDEX IF NOT EXISTS idx_jobs_deadline ON public.jobs(application_deadline);
CREATE INDEX IF NOT EXISTS idx_jobs_creator ON public.jobs(creator_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_job ON public.job_applications(job_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_user ON public.job_applications(applicant_id);

CREATE INDEX IF NOT EXISTS idx_events_start_time ON public.events(start_time);
CREATE INDEX IF NOT EXISTS idx_events_published ON public.events(is_published);
CREATE INDEX IF NOT EXISTS idx_event_registrations_event ON public.event_registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_event_registrations_user ON public.event_registrations(user_id);

CREATE INDEX IF NOT EXISTS idx_chapters_country_city ON public.alumni_chapters(country, city);

-- ---------------------------------------------------------------------
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- ---------------------------------------------------------------------

ALTER TABLE public.mentor_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alumni_chapters ENABLE ROW LEVEL SECURITY;

-- Mentor Profiles: Anyone authenticated can view accepting mentors; only owner can edit
CREATE POLICY "mentor_profiles_select" ON public.mentor_profiles
    FOR SELECT TO authenticated
    USING (is_accepting_requests = TRUE OR auth.uid() = user_id);

CREATE POLICY "mentor_profiles_update" ON public.mentor_profiles
    FOR UPDATE TO authenticated
    USING (auth.uid() = user_id);

-- Mentor Requests: Student or mentor can view their own requests
CREATE POLICY "mentor_requests_select" ON public.mentor_requests
    FOR SELECT TO authenticated
    USING (
        auth.uid() = student_id OR 
        auth.uid() IN (SELECT user_id FROM public.mentor_profiles WHERE id = mentor_id)
    );

CREATE POLICY "mentor_requests_insert" ON public.mentor_requests
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = student_id);

CREATE POLICY "mentor_requests_update" ON public.mentor_requests
    FOR UPDATE TO authenticated
    USING (
        auth.uid() = student_id OR 
        auth.uid() IN (SELECT user_id FROM public.mentor_profiles WHERE id = mentor_id)
    );

-- Jobs: Active jobs are readable by all authenticated users
CREATE POLICY "jobs_select" ON public.jobs
    FOR SELECT TO authenticated
    USING (is_active = TRUE OR auth.uid() = creator_id);

CREATE POLICY "jobs_insert" ON public.jobs
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = creator_id);

-- Job Applications: Only applicant or job creator can view
CREATE POLICY "job_applications_select" ON public.job_applications
    FOR SELECT TO authenticated
    USING (
        auth.uid() = applicant_id OR 
        auth.uid() IN (SELECT creator_id FROM public.jobs WHERE id = job_id)
    );

CREATE POLICY "job_applications_insert" ON public.job_applications
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = applicant_id);

-- Events: Published events visible to all authenticated users
CREATE POLICY "events_select" ON public.events
    FOR SELECT TO authenticated
    USING (is_published = TRUE OR auth.uid() = organizer_id);

-- Event Registrations: User can see and insert own registrations
CREATE POLICY "event_registrations_select" ON public.event_registrations
    FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "event_registrations_insert" ON public.event_registrations
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Chapters: Publicly readable by all authenticated members
CREATE POLICY "alumni_chapters_select" ON public.alumni_chapters
    FOR SELECT TO authenticated
    USING (TRUE);
