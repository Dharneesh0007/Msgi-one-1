# MSGI ONE — GATE 7.0 SECURITY & DEPENDENCY HANDOFF REPORT
**Document Version:** 1.0.0  
**Phase:** 7 — Intelligent AI Infrastructure and Verified Integration  
**Author:** Independent Technical Auditor & Principal AI Systems Architect  
**Governance:** MSGI One Executive Engineering Directive v2.0  
**Parent Phase:** Phase 6 — PostgreSQL Persistence, Async Repository Architecture, Authorization Audit and Frozen Android Compatibility  
**Frozen Android Artifact ID:** `a95a7169-d48b-4730-bcfd-921500e4b8fae`  
**Execution Timestamp:** 2026-11-21T21:40:00+05:30  
**Gate 7.0 Status:** **ACCEPTED WITH DOCUMENTED SECURITY CONTROLS**  

---

## 1. Executive Handoff Finding & Overview

Gate 7.0 serves as the formal gatekeeper between the verified persistence foundation established in Phase 6 and the live AI subsystem to be engineered in Phase 7. 

In accordance with Executive Engineering Directive v2.0, this handoff report evaluates the corrective Phase 6 deliverables (`docs/phase6/14` through `docs/phase6/20` and `docs/phase6/STATE.md`), performs empirical audits on the live PostgreSQL environment, resolves the Row-Level Security (RLS) findings, and defines the non-negotiable security boundaries governing Phase 7 implementation.

---

## 2. Empirical Verification of Phase 6 Corrective Results `[V-EXEC]`

The Phase 6 corrective test suite was re-executed against the live hosted staging infrastructure:

```powershell
services/api/.venv/Scripts/pytest.exe services/api/tests -v
```

### 2.1 Execution Results
- **Total Tests Collected & Executed:** 130 items
- **Passed:** 130 (100%)
- **Failed:** 0
- **Errors:** 0
- **Execution Duration:** 28.59 seconds
- **Verification Level:** `[V-EXEC]` (reproduced live on host)

### 2.2 Infrastructure & Driver Validation
- **Database Engine:** PostgreSQL 17.12 on `aarch64-unknown-linux-gnu` (Supabase hosted on AWS `ap-south-1`).
- **Connection Architecture:** Supabase Transaction Pooler (`aws-1-ap-south-1.pooler.supabase.com:6543/postgres`).
- **Python Driver & Version:** `asyncpg` 0.32.0.
- **SQLAlchemy Version:** 2.1.9 (`AsyncSession`, `create_async_engine`, `NullPool`).
- **Native UUID Rendering:** Validated custom compiler hook rendering 36-char string parameters as `$n::UUID` in PostgreSQL AST while maintaining SQLite compatibility.

### 2.3 Persistence & Transaction Durability
- **Real AsyncSession Operations:** Confirmed active async session lifecycle across repositories: `UserRepository`, `JobsRepository`, `EventsRepository`, `CommunityRepository`, `NotificationsRepository`.
- **Durability Across Independent Sessions:** Verified that records inserted and committed in Session A survive session teardown and are accurately fetched in an independent Session B.
- **Atomic Rollback:** Verified that uncommitted inserts rolled back in a failed transaction leave zero database artifacts.
- **PostgreSQL Constraints:** Verified that foreign keys (`users_id_fkey`, `auth.users(id)`), unique constraints (`uq_career_role_skill`), and check constraints (`events_event_type_check`) are natively enforced by the PostgreSQL server.
- **Connection Failure Safety:** Verified that database connection failure raises an explicit `OperationalError` / `DatabaseError` without falling back to silent in-memory persistence.

### 2.4 Safety & Isolation of the Hosted Database Environment
- **Environment Classification:** The configured Supabase database is a dedicated staging/development environment.
- **Synthetic Data Invariant (Law 9):** No real student records, alumni contact details, or institutional phone numbers exist in the database. All test fixtures utilize synthetic deterministic identifiers (e.g., `00000000-0000-0000-0000-000000000001`, `test.student@example.msgi.edu`).
- **Fixture Teardown & Cascading Cleanup:** Synthetic test identities are inserted into `auth.users` (triggering the `handle_new_auth_user` trigger to provision `public.users`), and are deleted from `auth.users` during fixture teardown, cleanly cascading deletions across all 38 relational tables without leaving persistent test remnants.
- **Destructive SQL Restrictions (Law 13):** No `DROP TABLE`, `TRUNCATE`, or destructive schema modifications are permitted against the remote database.

---

## 3. Mandatory Security Review: RLS Findings & Backend Privileges

### 3.1 The `BYPASSRLS` Finding
Empirical query of the PostgreSQL catalog (`pg_roles`) confirms:
```sql
SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'postgres';
-- Output: rolname = 'postgres', rolsuper = True, rolbypassrls = True
```
- **Finding:** The backend application connects to the database as the privileged role `postgres`.
- **Architectural Consequence:** In PostgreSQL, any user with `rolsuper = True` or `rolbypassrls = True` bypasses all Row-Level Security policies. PostgreSQL's internal query rewriter completely ignores `USING (...)` and `WITH CHECK (...)` clauses for queries executed under this role.
- **Crucial Rule for Phase 7:** **Database-level RLS policies DO NOT protect backend server queries.** The presence of an RLS policy in a migration script provides zero protection for any query initiated by FastAPI, domain services, or AI agents connecting via `DATABASE_URL`.
- **Authoritative Security Perimeter:** **Authorization is strictly enforced in the FastAPI application layer** (`src/core/dependencies.py`, `src/core/security.py`, and domain repository query scoping).

### 3.2 Detailed Audit of the Three Tables Without RLS
Of the 38 tables in the public schema, exactly 35 have `relrowsecurity = true`. Exactly 3 tables do not:

| Table Name | Purpose & Contents | Sensitive Data Classification | Role Grants | Missing RLS Status | Adequacy Assessment |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`public.roles`** | Reference lookup table mapping the 5 canonical roles (`student`, `alumni`, `faculty`, `recruiter`, `admin`) to descriptions. | Public Reference Data (Zero PII) | `SELECT` to `anon`, `authenticated`, `postgres` | **Intentional** Reference Table | **Adequate.** Static dictionary without sensitive data. Mutations restricted to database migrations. |
| **`public.skills`** | Central skills taxonomy mapping skill UUIDs to canonical skill names and categories (`technical`, `business`, etc.). | Public Reference Data (Zero PII) | `SELECT` to `anon`, `authenticated`, `postgres` | **Intentional** Reference Table | **Adequate.** Static taxonomy required for global autocomplete and skill matching. Zero user identity association. |
| **`public.user_skills`** | User-skill mapping table linking `user_id` to `skill_id` with `proficiency` and `verified` flags. | User-Specific Academic / Professional Association (FERPA/PII adjacent) | Read/Write to `authenticated`, `postgres` | **Omission in Migration 20261118000001** | **Conditionally Adequate.** The FastAPI repository layer strictly enforces `WHERE user_id = current_user.id`. However, if accessed directly via PostgREST client, rows would be visible. |

### 3.3 Security Remediation & AI Retrieval Mandate
To ensure that Phase 7 live AI, vector retrieval, and LangGraph orchestration do not introduce vulnerabilities:

1. **AI Retrieval Security Boundary:**
   AI agents, vector search tools, and RAG retrievers **MUST NEVER** rely on database-level RLS. Every query constructed by an AI tool or vector retriever must explicitly enforce:
   - Authenticated user context (`user_id`, `roles`, `is_verified`).
   - Explicit tenant / visibility constraints:
     ```sql
     WHERE visibility IN ('public', 'institutional')
       AND is_active = TRUE
       AND deleted_at IS NULL
     ```
   - FERPA-protected PII (phone numbers, physical addresses, private email addresses) must be masked *before* data enters the LangGraph state or LLM context window.

2. **Schema Migration for `user_skills` RLS:**
   A schema migration script (`ALTER TABLE public.user_skills ENABLE ROW LEVEL SECURITY;` with `user_id = auth.uid()` policy) has been prepared locally. Per Law 13 and Directive v2.0, it will not be executed on the remote database without explicit project-owner authorization.

---

## 4. Frozen Android APK Compatibility Boundaries

### 4.1 Artifact Preservation
- **Artifact Identifier:** `a95a7169-d48b-4730-bcfd-921500e4b8fae`
- **Integrity Status:** Strictly preserved. No rebuilding, re-signing, or asset modification has been performed.

### 4.2 Invariant API Contracts Verified `[V-API]`
1. **Dual Prefix Routing:** Fully operational via `DoublePrefixNormalizationMiddleware` and dual router mounts. Both `POST /api/v1/ai/chat` and `POST /api/v1/api/v1/ai/chat` resolve to the identical endpoint logic.
2. **Profile Me Aliases:** Direct aliases (`GET /api/v1/profiles/me` and `GET /api/v1/users/me`) return HTTP 200 with valid `StandardEnvelope[UserProfileResponse]`.
3. **Response Envelope:** All AI responses must conform to `StandardEnvelope[AIChatResponse]` with keys `status`, `data`, `timestamp`, `meta`.
4. **Non-Streaming Requirement for Mobile:** The frozen APK requires discrete JSON responses. While web clients may eventually support Server-Sent Events (SSE), all primary mobile AI endpoints (`/api/v1/ai/chat`, `/api/v1/ai/workflows`) must return complete JSON payloads.
5. **Polling Semantics:** The mobile app polls `/api/v1/notifications` and `/api/v1/ai/workflows/{id}`. These endpoints must continue to support standard HTTP GET polling with pagination metadata.

### 4.3 Runtime Verdict
- **API Contract Verification:** **`PASSED`** `[V-API]` (9/9 automated tests in `test_frozen_apk_contracts.py`).
- **Physical Device Runtime Execution:** **`UNVERIFIED`** `[UNKNOWN]` (no physical Android device or emulator hardware is attached to the headless automated test runner).

---

## 5. Phase 7 Dependency & Environment Audit

Inspection of the virtual environment (`services/api/.venv`) confirms that all required Phase 7 libraries are installed:

| Package | Installed Version | Purpose in Phase 7 | Documentation Reference |
| :--- | :---: | :--- | :--- |
| **`google-genai`** | 3.5.0 | Official Google Gen AI Python SDK for Gemini 2.5/Flash inference | Google Gen AI Python SDK Reference |
| **`langgraph`** | 1.2.22 | State graph orchestration, supervisor routing, conditional transitions | LangGraph 1.2 Documentation |
| **`langchain-core`** | 1.8.3 | Message abstractions (`HumanMessage`, `AIMessage`), tools, runnables | LangChain Core Documentation |
| **`langgraph-checkpoint-postgres`** | 3.2.1 | Asynchronous PostgreSQL checkpoint persistence (`AsyncPostgresSaver`) | LangGraph Checkpoint PostgreSQL Guide |
| **`psycopg`** | 3.3.9 | Modern async PostgreSQL driver required by LangGraph checkpointer | Psycopg 3 Documentation |
| **`asyncpg`** | 0.32.0 | High-performance async PostgreSQL driver for SQLAlchemy repositories | asyncpg Documentation |
| **`pgvector`** | 0.5.1 | Python integration and SQLAlchemy types for PostgreSQL vector search | pgvector Python Documentation |
| **`sqlalchemy`** | 2.1.9 | Async ORM declarative mappings and database engine | SQLAlchemy 2.0 Documentation |
| **`fastapi`** | 0.164.0 | High-performance async web framework | FastAPI Documentation |
| **`pydantic`** | 2.14.3 | Strict request/response validation and schema serialization | Pydantic v2 Documentation |

### Live Database pgvector Extension Audit `[V-EXEC]`
Empirical query via `check_pgvector.py` on the live database confirms:
- **Extension Name:** `vector`
- **Installed Version:** `0.8.2`
- **Vector Columns Found:** `public.alumni_profiles.embedding` (declared as `vector(1536)`).
- **Existing Vector Indexes:** None (ready for controlled index creation).
- **Existing Checkpoint Tables:** None (ready for controlled checkpoint table initialization).

---

## 6. Gate 7.0 Acceptance Decision

### Decision: **ACCEPTED WITH CONDITIONS**

1. **Pre-requisite Validation:** Phase 6 persistence, async repositories, and API backward compatibility are empirically verified (`130 passed in 28.59s`).
2. **Security Constraint:** The backend connects as `postgres` with `BYPASSRLS`. Therefore, all Phase 7 AI tools, vector retrieval functions, and agent nodes must enforce authorization and tenant filtering at the application layer. No AI tool may execute raw unparameterized SQL.
3. **Execution Guardrails:**
   - Real Gemini API inference requires valid credentials. When credentials are not configured, the system must fail transparently without fabricating responses.
   - Database migrations for LangGraph checkpoints and pgvector indices must be reviewed and tested locally before applying remotely.
   - All Phase 7 AI operations must strictly adhere to the frozen APK contract and maintain the 130-test baseline.

Live Phase 7 architecture planning and non-destructive implementation are hereby authorized to proceed to Gate 7.1.
