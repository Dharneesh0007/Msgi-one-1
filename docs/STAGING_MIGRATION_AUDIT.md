# MSGI One — Staging Database Migration Reconciliation & Schema Audit
**Environment:** STAGING ONLY  
**Branch:** `deploy/staging-hosted`  
**Execution Timestamp:** 2026-11-19T21:57:00+05:30  
**Compliance Standard:** Mandatory Engineering Laws (AGENTS.md Rules 1, 3, 4, 6, 9, 13)  

---

## 1. Executive Summary

This report provides the full architectural reconciliation of database migration files, relational foreign keys, table-creation sequences, and seed fixture mapping across the MSGI One platform prior to applying migrations to a hosted Supabase staging instance.

All canonical migration files have been verified for compliance with:
- **Abraham Silberschatz et al.:** 3NF relational normalization, primary key constraints, cascading foreign keys, check constraints.
- **Martin Kleppmann:** Append-only event logs, state machines, and resilient audit logging.
- **Eric Evans:** Domain boundaries aligned with the 12 core MSGI One modules.

---

## 2. Canonical Migration Inventory & Lineage

The canonical migration directory (`supabase/migrations/`) contains exactly 4 timestamped SQL migrations that form an uninterrupted, additive lineage:

| Migration File | Module Scope | Created Tables | RLS Policies | Indexes |
| :--- | :--- | :---: | :---: | :---: |
| `20261118000001_initial_identity_schema.sql` | Phase 1 Foundation: Identity, Auth, Profiles, Skills | 13 | 16 | 14 |
| `20261119000001_phase_2_core_modules.sql` | Phase 2 Core: Mentors, Jobs, Events, Chapters | 7 | 14 | 13 |
| `20261120000001_phase_3_agent_intelligence.sql` | Phase 3 Intelligence: Taxonomy, Agent Runs, Approvals | 6 | 6 | 10 |
| `20261121000001_phase_4_extended_modules.sql` | Phase 4 Extended: Learning, Communities, Projects, Startups, Impact, Notifications | 12 | 8 | 7 |
| **Total Canonical Lineage** | **12 Functional Modules** | **38** | **44** | **44** |

### 2.1 Resolution of Legacy Draft Migration
During the repository audit, an unversioned migration file (`00001_initial_schema.sql`, 24,579 bytes) was detected in `supabase/migrations/`.
- **Finding:** This file was a Phase 0 architectural draft containing conflicting pre-correction columns (e.g. `jobs.posted_by` vs canonical `jobs.creator_id`, non-nullable `first_name` and `last_name`). If left in place, Supabase CLI would execute it first, causing schema collisions with Phase 1–4 migrations.
- **Resolution:** Moved to `supabase/archive/00001_phase_0_draft_schema.sql` via Git. The active `supabase/migrations/` directory now strictly contains the 4 canonical timestamped migrations.

---

## 3. Relational Foreign-Key Dependency & Topological Order

All 38 tables conform to a strict directed acyclic graph (DAG) of foreign-key dependencies, preventing foreign-key creation errors during execution:

```
[auth.users] (Supabase Managed Identity)
     │
     ├──► [public.users] (1:1 Application Identity Proxy)
     │         │
     │         ├──► [public.user_roles] ──► [public.roles]
     │         ├──► [public.alumni_profiles] ──► [public.mentor_profiles] ──► [public.mentor_requests]
     │         ├──► [public.student_profiles]
     │         ├──► [public.faculty_profiles]
     │         ├──► [public.recruiter_profiles]
     │         ├──► [public.user_preferences]
     │         ├──► [public.consent_records]
     │         ├──► [public.alumni_locations]
     │         ├──► [public.user_skills] ──► [public.skills]
     │         ├──► [public.jobs] ──► [public.job_applications]
     │         ├──► [public.events] ──► [public.event_registrations]
     │         ├──► [public.alumni_chapters]
     │         ├──► [public.student_skills]
     │         ├──► [public.agent_runs] ──► [public.agent_actions]
     │         │         │
     │         │         └──► [public.approval_requests]
     │         ├──► [public.course_enrollments] ──► [public.learning_resources]
     │         ├──► [public.communities] ──► [public.community_memberships]
     │         ├──► [public.verification_requests]
     │         ├──► [public.admin_audit_logs]
     │         ├──► [public.projects] ──► [public.project_members]
     │         ├──► [public.startups] ──► [public.startup_connection_requests]
     │         ├──► [public.impact_programmes] ──► [public.volunteer_interests]
     │         └──► [public.notifications]
```

### 3.1 Verification of `auth.users` to `public.users.id`
- `public.users.id` is explicitly declared as:
  ```sql
  CREATE TABLE IF NOT EXISTS public.users (
      id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
      email VARCHAR(255) NOT NULL UNIQUE,
      first_name VARCHAR(100) NULL,
      last_name VARCHAR(100) NULL,
      ...
  );
  ```
- **Automatic Identity Synchronization Trigger:**
  Migration `20261118000001_initial_identity_schema.sql` establishes `public.handle_new_auth_user()` triggered `AFTER INSERT ON auth.users FOR EACH ROW`.
  When a user registers via Supabase Auth, PostgreSQL automatically creates their profile row in `public.users`, assigns the default `student` role in `public.user_roles`, and seeds their default preferences in `public.user_preferences`.

---

## 4. Synthetic Fixture Mapping & UUID Resolution

### 4.1 Invariant Validation via Dry-Run
Execution of `scripts/import_synthetic_data.py --dry-run` validates all 139 synthetic fixture records across all 12 modules:

```
================================================================================
MSGI ONE — DATA INGESTION PIPELINE (MODE: DEMO)
Dry Run: True
Target Directory: msgi-one\supabase\seed\csv
================================================================================
DATASET                   | STATUS  | ACCEPTED | REJECTED | DUPLICATES | UNRESOLVED
--------------------------------------------------------------------------------
Alumni Directory          | SUCCESS | 4        | 0        | 0          | 0         
Job Opportunities         | SUCCESS | 3        | 0        | 0          | 0         
Role Skill Taxonomy       | SUCCESS | 25       | 0        | 0          | 0         
Learning Resources        | SUCCESS | 11       | 0        | 0          | 0         
Student Skills            | SUCCESS | 9        | 0        | 0          | 0         
Communities (6)           | SUCCESS | 6        | 0        | 0          | 0         
Memberships (12)          | SUCCESS | 12       | 0        | 0          | 0         
Verifications (5)         | SUCCESS | 5        | 0        | 0          | 0         
Projects (6)              | SUCCESS | 6        | 0        | 0          | 0         
Startups (5)              | SUCCESS | 5        | 0        | 0          | 0         
Impact Programmes (4)     | SUCCESS | 4        | 0        | 0          | 0         
QA Test Users (14)        | SUCCESS | 14       | 0        | 0          | 0         
QA Role Perms (35)        | SUCCESS | 35       | 0        | 0          | 0         
================================================================================
Total Accepted Records  : 139
Total Rejected Records  : 0
Total Duplicate Records : 0
Total Unresolved FKeys  : 0
Final Validation State  : ALL DATASETS VALIDATED (100% PASS)
================================================================================
```

### 4.2 Raw SQL Seed File Discrepancy Note (`00004_phase_4_synthetic_seed.sql`)
- **Finding:** The fixture file `supabase/seed/00004_phase_4_synthetic_seed.sql` contains literal string aliases (e.g. `'user-kenji-001'`, `'comm-ai-001'`) instead of UUIDs.
- **Rule Enforcement:** Under no circumstances should `00004_phase_4_synthetic_seed.sql` be executed directly against PostgreSQL via psql or db push.
- **Staging Ingestion Protocol:** When seeding the hosted staging database, test accounts must be provisioned via Supabase Auth Admin API (producing real UUIDs), and records ingested using `scripts/import_synthetic_data.py`, which resolves aliases to actual UUIDs.

---

## 5. Migration Reconciliation Verdict

1. **Migration lineage is 100% validated** with 4 canonical files and 38 strictly typed relational tables.
2. **Obsolete draft migration `00001_initial_schema.sql` is archived** and isolated from CLI execution.
3. **Foreign key topology is verified:** All foreign keys cleanly resolve without cyclic or dangling dependencies.
4. **Identity synchronization trigger is confirmed** to bridge `auth.users` with `public.users`.
5. **Synthetic data dry-run confirms 139/139 valid records** with zero unmapped foreign keys.
6. **Preflight status:** Ready for non-destructive Step 3 staging verification.
