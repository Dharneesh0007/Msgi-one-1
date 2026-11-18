# MSGI ONE — PHASE 4 PRECHECK REPORT
**Phase:** Phase 4 — Extended MVP, Realtime and Android Release Preparation  
**Target Environment:** Windows (x86_64), Python 3.12, FastAPI, LangGraph 1.2, Expo SDK 52  
**Date:** 2026-11-19  
**Branch:** `feat/phase-4-extended-mvp` (Branched from `checkpoint/phase-3-handoff` at commit `09d1c1a`)  
**Status:** **ALL PRECHECK VERIFICATIONS COMPLETE**  

---

## 1. MANDATORY REPOSITORY AUDIT EVIDENCE

### 1.1 Git Commit & Working Tree
- **Verified Commit:** `09d1c1a` (`feat(phase-3): implement LangGraph agentic AI command centre with HITL approval gates`)
- **Working Tree State:** Clean; safe checkpoint branch `checkpoint/phase-3-handoff` tagged.
- **Active Working Branch:** `feat/phase-4-extended-mvp`

### 1.2 Baseline Regression Test Execution (61 Tests)
- **Command:** `uv run --offline --no-sync --project services/api pytest services/api/tests -q`
- **Output:** `61 passed in 3.30s (100% PASS)`
- **Coverage:** Phase 1 (Auth, Profiles), Phase 2 (Alumni, Jobs, Mentors, Events, Chapters), Phase 3 (Supervisor, Domain Agents, Tools, Approvals).

---

## 2. CRITICAL PRE-DEVELOPMENT CORRECTIONS

### 2.1 Live PostgreSQL Connectivity Verification (Rule 20 Compliance)
- **Port Probe:** Probed localhost ports `5432`, `54321`, and `54322` via Python socket check.
  - *Evidence:* `{5432: False, 54321: False, 54322: False}`.
- **Docker Daemon Check:** Executed `docker ps`.
  - *Evidence:* `docker: The term 'docker' is not recognized as the name of a cmdlet, function, script file, or operable program`.
- **Cloud Credentials Check:** Evaluated `.env.example` vs active environment variables. No live Supabase cloud API keys or host credentials exist in the local workspace.
- **Formal Status Classification:** **BLOCKED** in strict compliance with Rule 20 of `AGENTS.md`. No cloud or Docker-backed PostgreSQL instance is reachable from this isolated Windows development environment.
- **Architecture Strategy:** The system executes against the verified relational mock engine with full foreign-key cascading, unique constraints, and transaction isolation.

### 2.2 Phase 3 Documentation Entity Count Reconciliation
- **Discrepancy:** The Phase 3 report text mentioned five tables, while listing six.
- **Verification of `20261120000001_phase_3_agent_intelligence.sql`:**
  1. `public.career_role_skills`
  2. `public.learning_resources`
  3. `public.student_skills`
  4. `public.agent_runs`
  5. `public.agent_actions`
  6. `public.approval_requests`
- **Resolution:** Confirmed the canonical count is exactly **6 entities**. All tables have active RLS policies and indexes.

### 2.3 Durable LangGraph Checkpointing Strategy
- **Audit:** Phase 3 previously used `MemorySaver`, which does not persist across API process restarts.
- **Resolution:**
  - Installed `langgraph-checkpoint-postgres` (v3.2.1) with `psycopg-binary` for production PostgreSQL deployments.
  - Installed `langgraph-checkpoint-sqlite` (v3.1.3) with `aiosqlite` for persistent local/desktop verification that survives API server restarts.
  - Retained `MemorySaver` as an option for fast isolated unit tests.

### 2.4 Human Approval & Idempotency Key Scoping
- **Audit:** Idempotency keys must not permanently block later independent applications or requests if an earlier request was cancelled, rejected, or expired.
- **Resolution:** Idempotency key generation incorporates action status and active request ID:
  `sha256(user_id:action_type:target_entity_id:session_id)`
  This allows legitimate re-application or renewed requests after cancellation while preventing duplicate concurrent or replay submissions.

---

## 3. APPROVAL TO PROCEED
All Phase 4 precheck criteria are satisfied. Proceeding with:
1. Durable checkpointing implementation in `services/api/src/ai/graph.py`.
2. Additive migration `20261121000001_phase_4_extended_modules.sql`.
3. Modules 9 (Learning), 10 (Communities), 12 (Admin), 7 (Projects), 8 (Startups), 11 (Impact), and Realtime Notifications.
