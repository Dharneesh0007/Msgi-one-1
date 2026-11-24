-- ============================================================================
-- MSGI ONE — PHASE 7 MIGRATION: LANGGRAPH POSTGRESQL CHECKPOINTS & THREADS
-- Migration: 20261121000003_langgraph_checkpoints.sql
-- Principles:
--   - Kleppmann: Durable fault-tolerant state checkpointing across process restarts
--   - Silberschatz: Multi-tenant thread ownership & referential integrity
--   - LangGraph: Canonical schema for AsyncPostgresSaver (v3.2.1)
-- GOVERNANCE NOTICE:
--   Per Rule 13 of AGENTS.md, this migration is prepared and validated locally.
--   Do NOT execute remotely on production or hosted staging without explicit owner authorization.
-- ============================================================================

-- 1. Checkpoint Migrations Tracking Table
CREATE TABLE IF NOT EXISTS public.checkpoint_migrations (
    v INTEGER PRIMARY KEY
);

-- 2. Checkpoints Primary Table
CREATE TABLE IF NOT EXISTS public.checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- 3. Checkpoint Blobs Table (Channel States & Serialized Data)
CREATE TABLE IF NOT EXISTS public.checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    type TEXT NOT NULL,
    blob BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

-- 4. Checkpoint Writes Table (Pending Task Writes & State Reducers)
CREATE TABLE IF NOT EXISTS public.checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    blob BYTEA NOT NULL,
    task_path TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);

-- 5. Multi-Tenant Thread Ownership Registry (Security Gate 7.4)
-- Enforces that every conversation thread is owned by a valid user.
-- Prevents cross-user thread inspection, tampering, or state hijacking.
CREATE TABLE IF NOT EXISTS public.agent_threads (
    thread_id VARCHAR(128) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 6. Indexes for Performance (Non-concurrent for migration compatibility)
CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON public.checkpoints (thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_blobs_thread_id ON public.checkpoint_blobs (thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_writes_thread_id ON public.checkpoint_writes (thread_id);
CREATE INDEX IF NOT EXISTS idx_agent_threads_user_id ON public.agent_threads (user_id);

-- 7. Seed migration version record (v=10 for full langgraph-checkpoint-postgres compatibility)
INSERT INTO public.checkpoint_migrations (v) VALUES (10) ON CONFLICT (v) DO NOTHING;

-- 8. Row Level Security for Agent Threads
ALTER TABLE public.agent_threads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only view their own agent threads"
    ON public.agent_threads FOR SELECT TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can create their own agent threads"
    ON public.agent_threads FOR INSERT TO authenticated
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own agent threads"
    ON public.agent_threads FOR UPDATE TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can delete their own agent threads"
    ON public.agent_threads FOR DELETE TO authenticated
    USING (user_id = auth.uid());
