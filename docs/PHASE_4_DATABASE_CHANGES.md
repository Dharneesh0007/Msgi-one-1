# MSGI ONE — PHASE 4 DATABASE CHANGES
**Migration:** `supabase/migrations/20261121000001_phase_4_extended_modules.sql`  
**Principles Applied:**
- Abraham Silberschatz et al.: Relational integrity, check constraints, foreign key cascades, unique enrollment/membership constraints.
- Martin Kleppmann: Append-only audit logs, unified notification event log, durable event-driven state.
- Eric Evans: Bounded contexts for Learning Academy, Communities, Administration, Projects, Startups, and Impact.

---

## 1. NEW RELATIONAL ENTITIES

| Entity | Purpose | Key Constraints |
| :--- | :--- | :--- |
| `public.course_enrollments` | Student course tracking & completion | `UNIQUE(user_id, resource_id)`, `progress_percentage BETWEEN 0 AND 100` |
| `public.communities` | Interest and professional groups directory | `UNIQUE(slug)`, `member_count >= 0` |
| `public.community_memberships` | User group membership & moderation | `UNIQUE(community_id, user_id)`, role/status checking |
| `public.verification_requests` | Alumni/Faculty/Recruiter credential reviews | `UNIQUE(user_id, requested_role, status)`, status checking |
| `public.admin_audit_logs` | Immutable audit trail of admin decisions | Append-only, `admin_id NOT NULL` |
| `public.projects` (P1) | Collaborative research and engineering ventures | `owner_id NOT NULL`, `member_count >= 1` |
| `public.project_members` (P1) | Project team roster & join requests | `UNIQUE(project_id, user_id)` |
| `public.startups` (P1) | Alumni/student venture directory | `founder_id NOT NULL`, stage checking |
| `public.startup_connection_requests` (P1) | Introduction requests for startups | `UNIQUE(startup_id, user_id)` |
| `public.impact_programmes` (P1) | Community outreach & volunteering | `coordinator_id NOT NULL`, `target_volunteers > 0` |
| `public.volunteer_interests` (P1) | Recorded volunteer signups | `UNIQUE(programme_id, user_id)` |
| `public.notifications` | Unified cross-module notification log | `user_id NOT NULL`, `is_read BOOLEAN` |

---

## 2. ROW-LEVEL SECURITY (RLS) POLICIES

- `course_enrollments`: Restricted to `user_id = auth.uid()`. Cross-user progress changes blocked.
- `communities`: Public groups readable by all authenticated users; private groups visible only to members.
- `community_memberships`: Users manage their own memberships.
- `verification_requests`: Users see their own; administrators manage all with audit logging.
- `notifications`: Strictly isolated to `user_id = auth.uid()`. Cross-user event snooping blocked.
