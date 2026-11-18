# MSGI ONE — PHASE 3 DATABASE CHANGES
**Migration:** `supabase/migrations/20261120000001_phase_3_agent_intelligence.sql`  
**Principles Applied:**
- Abraham Silberschatz et al.: Strong relational integrity, CHECK constraints on levels/weights/statuses, foreign key cascading.
- Martin Kleppmann: Append-only audit logging for AI agent actions, state machine transitions for approvals.
- Eric Evans: Bounded contexts for Career Intelligence and Agent Execution Tracking.

---

## 1. NEW RELATIONAL ENTITIES

| Entity | Purpose | Key Constraints |
| :--- | :--- | :--- |
| `public.career_role_skills` | Maps target job roles to required competencies | `UNIQUE(role_id, skill_name)`, `importance_weight BETWEEN 1 AND 5` |
| `public.learning_resources` | Curated courseware catalog for automated roadmaps | `UNIQUE(resource_id)`, `duration_hours > 0`, `rating BETWEEN 0 AND 5` |
| `public.student_skills` | Ground-truth user skills baseline | `UNIQUE(user_id, skill_name)`, `FK user_id -> users(id)` |
| `public.agent_runs` | Session execution lifecycle and token/latency audit | `CHECK status IN ('running', 'interrupted', 'completed', 'failed', 'rejected')` |
| `public.agent_actions` | Fine-grained tool invocation telemetry | `FK run_id -> agent_runs(id)`, status checking |
| `public.approval_requests` | Human-In-The-Loop approval gates | `UNIQUE(idempotency_key)`, `CHECK action_type IN ('send_mentor_request', 'apply_job', 'register_event')` |

---

## 2. ROW LEVEL SECURITY (RLS) MATRIX

- `career_role_skills`: Authenticated read-only.
- `learning_resources`: Authenticated read-only.
- `student_skills`: Owner-isolated (`user_id = auth.uid()`).
- `agent_runs`: Owner-isolated (`user_id = auth.uid()`).
- `agent_actions`: Sub-query isolated via `agent_runs.user_id = auth.uid()`.
- `approval_requests`: Owner-isolated (`user_id = auth.uid()`). Consequential actions cannot be approved or rejected across user boundaries.
