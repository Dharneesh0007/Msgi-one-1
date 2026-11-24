-- ============================================================================
-- MSGI ONE — LEAST-PRIVILEGE RUNTIME DATABASE ROLE MIGRATION (PHASE 3)
-- Migration: 20261125000002_runtime_rls_role.sql
-- GOVERNANCE NOTICE: Prepared locally. Do NOT apply to remote production without explicit owner authorization.
-- Purpose: Separates migration privileges (postgres) from runtime API privileges (msgi_api_runtime)
--          with NOBYPASSRLS so PostgreSQL RLS policies remain enforceable at runtime when user context is set.
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'msgi_api_runtime') THEN
        CREATE ROLE msgi_api_runtime NOLOGIN NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO msgi_api_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO msgi_api_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO msgi_api_runtime;

-- Helper function allowing RLS policies to read either Supabase auth.uid() or FastAPI transaction-local context
CREATE OR REPLACE FUNCTION public.current_actor_id()
RETURNS UUID AS $$
DECLARE
    ctx_uid TEXT;
BEGIN
    ctx_uid := NULLIF(current_setting('app.current_user_id', true), '');
    IF ctx_uid IS NOT NULL THEN
        RETURN ctx_uid::UUID;
    END IF;
    RETURN auth.uid();
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;
