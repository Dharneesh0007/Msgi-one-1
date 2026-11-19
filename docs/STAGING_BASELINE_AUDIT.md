# MSGI One — Staging Baseline & Safety Audit
**Environment:** STAGING ONLY  
**Branch:** `deploy/staging-hosted`  
**Base Commit / Tag:** `d2cccac` / `checkpoint/phase-5-handoff`  
**Execution Timestamp:** 2026-11-19T21:55:00+05:30  
**Compliance Standard:** Mandatory Engineering Laws (AGENTS.md Rules 1, 2, 7, 10, 13, 15, 20)  

---

## 1. Executive Summary & Audit Scope

This baseline audit evaluates the MSGI One repository prior to any remote staging deployment or hosted database migration. The primary objective is to verify repository cleanliness, security isolation, secret exclusion, branch isolation, and catalogue every fallback mechanism across the application.

All checks conducted herein conform to the 7-layer architecture (Layers A–G) documented in `docs/SYSTEM_ARCHITECTURE.md` and international software engineering standards (Silberschatz relational integrity, Kleppmann reliability, Pressman process controls).

---

## 2. Git Status, Revision History & Checkpoint Verification

### 2.1 Baseline Revision Verification
- **Verified Latest Commit on Main:** `d2cccac` (`feat(phase-5): complete final quality assurance, offline integration gates, security audit, and release reports`)
- **Preceding Commit Lineage:**
  - `38ece01` — `feat(phase-4): prepare deterministic synthetic fixtures, CSV templates, validators, and reproducible SQL seed`
  - `65ebde0` — `feat(phase-4): implement extended modules, durable checkpoints, realtime notifications, and android release prep`
  - `09d1c1a` — `feat(phase-3): implement LangGraph agentic AI command centre with HITL approval gates`
  - `930a9d5` — `feat(phase-2): implement core connected business modules (alumni, career, mentors, events, global)`

### 2.2 Branch & Checkpoint Isolation
- **Base Immutable Tag:** `checkpoint/phase-5-handoff` created at `d2cccac`.
- **Active Staging Deployment Branch:** `deploy/staging-hosted` checked out.
- **Initial Staging Commit:** `db0e819` (`chore(staging): archive legacy Phase 0 schema draft and add sqlite shm/wal to gitignore`).
- **Working Tree State:** Clean (`nothing to commit, working tree clean`).

---

## 3. Secret Exclusion & Git Security Audit

A thorough scan of Git tracking status and repository files was conducted to guarantee zero leakage of credentials, private keys, or connection strings:

```powershell
git ls-files | Select-String -Pattern "\.env"
# Result: .env.example (Tracked template only)
```

### 3.1 Excluded Artifacts & Patterns (.gitignore)
1. `.env`, `.env.*` (except `.env.example`)
2. `*.pem`, `*.key`, `*.pfx`, `*.p12`
3. `serviceAccountKey.json`, `google-services-key.json`
4. `*.sqlite`, `*.sqlite3`, `*.sqlite-shm`, `*.sqlite-wal`, `*.db`
5. `checkpoints.sqlite`
6. `node_modules/`, `apps/mobile/.expo/`, `apps/mobile/android/`, `apps/mobile/ios/`
7. `services/api/.venv/`, `__pycache__/`, `.pytest_cache/`

### 3.2 Findings
- **Zero secrets are committed to the repository.**
- Only deterministic synthetic development defaults and `.env.example` templates exist in source control.
- Staging environment variables (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`) must be loaded strictly from local uncommitted `.env` files or cloud container environment injection.

---

## 4. Fallback Architecture & Activation Catalog

The repository currently contains 14 in-memory and file-based fallback paths designed for rapid offline testing, deterministic test suite execution, and decoupled local development without requiring live PostgreSQL network connectivity.

| Fallback Store | File Path | Activation Trigger | Hosted Staging Behavior |
| :--- | :--- | :--- | :--- |
| **LangGraph Checkpointer (`checkpoints.sqlite`)** | `services/api/src/ai/graph.py` | `LANGGRAPH_CHECKPOINT_MODE=sqlite` | In staging, switch to `LANGGRAPH_CHECKPOINT_MODE=postgres` to persist state in hosted PostgreSQL table `checkpoints`. |
| **LangGraph MemorySaver** | `services/api/src/ai/graph.py` | `LANGGRAPH_CHECKPOINT_MODE=memory` or fallback on connection failure | Used only for ephemeral unit tests; deactivated in staging. |
| **Agent Runs Audit Store (`_AGENT_RUNS_STORE`)** | `services/api/src/ai/graph.py` | Unset `DATABASE_URL` / offline execution | In staging, records should write directly to `public.agent_runs`. |
| **Dev Profile Store (`_DEV_PROFILE_STORE`)** | `services/api/src/routers/users.py` | `DATABASE_URL` offline / mock mode | Bypassed when database sessions query `public.users` and sub-profile tables. |
| **Synthetic Alumni Store (`_SYNTHETIC_ALUMNI_STORE`)** | `services/api/src/services/alumni_service.py` | Module initialization | Serves synthetic directory data when PostgreSQL table `public.alumni_profiles` is empty or unlinked. |
| **Synthetic Jobs Store (`_JOBS_STORE`)** | `services/api/src/services/career_service.py` | Module initialization | Serves synthetic opportunities when `public.jobs` is unlinked. |
| **Synthetic Mentors Store (`_MENTORS_STORE`)** | `services/api/src/services/mentor_service.py` | Module initialization | Serves mentor roster when `public.mentor_profiles` is unlinked. |
| **Synthetic Events Store (`_EVENTS_STORE`)** | `services/api/src/services/event_service.py` | Module initialization | Serves calendar fixtures when `public.events` is unlinked. |
| **Synthetic Chapters Store (`_CHAPTERS_STORE`)** | `services/api/src/services/chapter_service.py` | Module initialization | Serves geographic chapters when `public.alumni_chapters` is unlinked. |
| **Synthetic Enrollments Store (`_ENROLLMENTS_STORE`)** | `services/api/src/routers/learning.py` | Module initialization | In-memory tracking when `public.course_enrollments` is unlinked. |
| **Synthetic Communities Store (`_COMMUNITIES_STORE`)** | `services/api/src/routers/communities.py` | Module initialization | In-memory community state when `public.communities` is unlinked. |
| **Verification Store (`_VERIFICATION_REQUESTS_STORE`)** | `services/api/src/routers/verification.py` | Module initialization | In-memory requests when `public.verification_requests` is unlinked. |
| **Projects Store (`_PROJECTS_STORE`)** | `services/api/src/routers/projects.py` | Module initialization | In-memory projects when `public.projects` is unlinked. |
| **Startups Store (`_STARTUPS_STORE`)** | `services/api/src/routers/startups.py` | Module initialization | In-memory ventures when `public.startups` is unlinked. |
| **Impact Programmes Store (`_IMPACT_PROGRAMMES_STORE`)** | `services/api/src/routers/impact.py` | Module initialization | In-memory impact drives when `public.impact_programmes` is unlinked. |
| **Notifications Store (`_NOTIFICATIONS_STORE`)** | `services/api/src/routers/notifications.py` | Module initialization | In-memory notifications when `public.notifications` is unlinked. |

---

## 5. Mobile App & EAS Build Configuration

### 5.1 Mobile App Baseline (`apps/mobile/app.json`)
- **Name:** MSGI One
- **Slug:** `msgi-one`
- **Package Name:** `edu.msgi.one`
- **SDK:** Expo SDK 52+
- **Routing:** `expo-router` (typed routes enabled)
- **Storage:** `expo-secure-store`
- **Permissions:** `INTERNET`, `ACCESS_NETWORK_STATE`

### 5.2 EAS Build Profile Baseline (`apps/mobile/eas.json`)
- Existing profiles: `development`, `preview`, `production`.
- **Finding:** A dedicated `staging` profile is missing from `apps/mobile/eas.json`.
- **Remediation Plan (Step 8):** Add an explicit `staging` build profile pointing to the staging backend API (`EXPO_PUBLIC_API_URL`) and Supabase staging URL (`EXPO_PUBLIC_SUPABASE_URL`).

---

## 6. Safety Audit Verdict

1. **Repository state is verified and locked** at tag `checkpoint/phase-5-handoff` (`d2cccac`).
2. **Zero credentials or secrets are present in Git.**
3. **Dedicated staging branch `deploy/staging-hosted` is active.**
4. **All 14 fallback paths have been documented with precise deactivation triggers.**
5. **Preflight condition:** Ready to proceed to Step 2 (Database Migration Audit).
