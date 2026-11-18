-- ====================================================================
-- MSGI One — Canonical Migration: 20261118000001_initial_identity_schema.sql
-- Module: Phase 1 Application Foundation (Identity, Auth & Profiles)
-- Canonical Migration Engine: Supabase SQL Migrations
-- Principles: Silberschatz et al. (3NF Relational Integrity), Kleppmann (Single Source of Truth)
-- ====================================================================

-- 1. Enable Core Extensions
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
    ('student', 'Active matriculated student (default base access)'),
    ('alumni', 'Verified graduate holding an institutional degree'),
    ('faculty', 'Academic faculty, professor, or researcher'),
    ('recruiter', 'Verified corporate hiring manager or placement partner'),
    ('admin', 'Institutional ecosystem compliance and system administrator')
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;

-- Core Users Table (1:1 proxy to Supabase auth.users)
-- Correction 4 Applied: first_name & last_name are NULLABLE initially to allow safe email signup without fake data
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NULL,
    last_name VARCHAR(100) NULL,
    avatar_url TEXT NULL,
    requested_role VARCHAR(50) NOT NULL DEFAULT 'student' CHECK (requested_role IN ('student', 'alumni', 'faculty', 'recruiter')),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

-- User Roles Junction Table
-- Correction 2 Applied: Server-mediated role assignments; default role is strictly 'student'
CREATE TABLE IF NOT EXISTS public.user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role_id VARCHAR(50) NOT NULL REFERENCES public.roles(id) ON DELETE RESTRICT,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_by UUID NULL REFERENCES public.users(id) ON DELETE SET NULL,
    UNIQUE (user_id, role_id)
);

-- Alumni Profiles (Sub-type extension for verified graduates)
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

-- Student Profiles (Sub-type extension for active students)
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

-- Faculty Profiles (Sub-type extension for academic staff)
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

-- Recruiter Profiles (Sub-type extension for corporate partners)
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

-- User Preferences (App settings, themes, notification switches)
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    push_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_digests_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    theme VARCHAR(20) NOT NULL DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Consent Records (FERPA / GDPR Compliance)
CREATE TABLE IF NOT EXISTS public.consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL CHECK (consent_type IN ('directory_listing', 'ai_profiling', 'recruiter_contact', 'location_sharing')),
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ NULL,
    UNIQUE (user_id, consent_type)
);

-- Geographic Sharing Table
-- Correction 5 Applied: is_public defaults to FALSE (privacy by default)
CREATE TABLE IF NOT EXISTS public.alumni_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    country_code VARCHAR(2) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    chapter_name VARCHAR(100) NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Central Skills Taxonomy
CREATE TABLE IF NOT EXISTS public.skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL CHECK (category IN ('technical', 'business', 'design', 'soft_skill', 'language')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- User Skills Mapping
CREATE TABLE IF NOT EXISTS public.user_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE CASCADE,
    proficiency VARCHAR(30) NOT NULL DEFAULT 'intermediate' CHECK (proficiency IN ('beginner', 'intermediate', 'advanced', 'expert')),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (user_id, skill_id)
);

-- Audit Logs Table (Layer G Observability & Compliance)
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
-- 3. Idempotent User Bootstrap Trigger
-- ====================================================================

-- Function to safely insert a public.users row when a Supabase auth.users record is created
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER AS $$
DECLARE
    default_role VARCHAR(50);
BEGIN
    -- Extract requested role from raw_user_meta_data if present, otherwise default to student
    default_role := COALESCE(NEW.raw_user_meta_data->>'requested_role', 'student');
    IF default_role NOT IN ('student', 'alumni', 'faculty', 'recruiter') THEN
        default_role := 'student';
    END IF;

    -- Idempotent insert into public.users
    INSERT INTO public.users (
        id,
        email,
        first_name,
        last_name,
        requested_role,
        is_verified,
        is_active,
        created_at,
        updated_at
    ) VALUES (
        NEW.id,
        NEW.email,
        NULLIF(TRIM(NEW.raw_user_meta_data->>'first_name'), ''),
        NULLIF(TRIM(NEW.raw_user_meta_data->>'last_name'), ''),
        default_role,
        FALSE,
        TRUE,
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        updated_at = NOW();

    -- Assign default least-privilege role in public.user_roles (Correction 2)
    INSERT INTO public.user_roles (user_id, role_id)
    VALUES (NEW.id, 'student')
    ON CONFLICT (user_id, role_id) DO NOTHING;

    -- Initialize default user preferences
    INSERT INTO public.user_preferences (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger binding to Supabase auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_auth_user();

-- ====================================================================
-- 4. Row-Level Security (RLS) Policies
-- ====================================================================

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alumni_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faculty_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recruiter_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alumni_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 4.1 public.users Policies
CREATE POLICY users_select_active ON public.users
    FOR SELECT TO authenticated
    USING (is_active = TRUE AND deleted_at IS NULL);

CREATE POLICY users_update_self ON public.users
    FOR UPDATE TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- 4.2 public.user_roles Policies
CREATE POLICY user_roles_select ON public.user_roles
    FOR SELECT TO authenticated
    USING (user_id = auth.uid() OR EXISTS (
        SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid() AND ur.role_id = 'admin'
    ));

-- 4.3 public.alumni_profiles Policies
CREATE POLICY alumni_profiles_select ON public.alumni_profiles
    FOR SELECT TO authenticated
    USING (
        user_id = auth.uid() OR
        visibility = 'public' OR
        (visibility = 'institutional' AND EXISTS (
            SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.is_verified = TRUE
        ))
    );

CREATE POLICY alumni_profiles_update_self ON public.alumni_profiles
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 4.4 public.student_profiles Policies
CREATE POLICY student_profiles_self ON public.student_profiles
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY student_profiles_faculty_admin ON public.student_profiles
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur 
            WHERE ur.user_id = auth.uid() AND ur.role_id IN ('faculty', 'admin')
        )
    );

-- 4.5 public.user_preferences Policies
CREATE POLICY user_preferences_self ON public.user_preferences
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 4.6 public.consent_records Policies
CREATE POLICY consent_records_self ON public.consent_records
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 4.7 public.alumni_locations Policies
CREATE POLICY alumni_locations_select ON public.alumni_locations
    FOR SELECT TO authenticated
    USING (
        user_id = auth.uid() OR
        (is_public = TRUE AND EXISTS (
            SELECT 1 FROM public.consent_records cr
            WHERE cr.user_id = alumni_locations.user_id 
              AND cr.consent_type = 'location_sharing' 
              AND cr.granted = TRUE
        ))
    );

CREATE POLICY alumni_locations_self ON public.alumni_locations
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 4.8 public.audit_logs Policies
CREATE POLICY audit_logs_admin_select ON public.audit_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur 
            WHERE ur.user_id = auth.uid() AND ur.role_id = 'admin'
        )
    );

-- ====================================================================
-- 5. Performance Indexes
-- ====================================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON public.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_alumni_profiles_user ON public.alumni_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_student_profiles_user ON public.student_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON public.user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_consent_records_user ON public.consent_records(user_id, consent_type);
CREATE INDEX IF NOT EXISTS idx_alumni_locations_user ON public.alumni_locations(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON public.audit_logs(actor_id, created_at);
