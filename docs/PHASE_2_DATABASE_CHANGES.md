# MSGI One — Phase 2 Database Schema Changes
**Relational Entities, Integrity Constraints, and Row Level Security for Core Business Modules**

**Document Version:** 1.0.0  
**Migration ID:** `20261119000001_phase_2_core_modules.sql`  
**Phase:** 2 (Core Business Modules)  
**Target Database:** PostgreSQL 15+ (Supabase)  
**Standard:** 3NF Normalization (Silberschatz Ch. 3-4), Kleppmann Data-Intensive Integrity  

---

## 1. Schema Summary

Phase 2 introduces six business entities supporting the P0/P1 modules:
1. `public.mentor_profiles` (MentorMatch)
2. `public.mentor_requests` (MentorMatch)
3. `public.jobs` (CareerBridge)
4. `public.job_applications` (CareerBridge)
5. `public.events` (Events and Reunions)
6. `public.event_registrations` (Events and Reunions)
7. `public.alumni_chapters` (Global Alumni Connect)

All tables inherit foreign key constraints anchoring directly to `public.users(id)` and `public.alumni_profiles(id)` established in Phase 1 (`20261118000001_initial_identity_schema.sql`). No duplicate user or profile tables are introduced (Rule 3).

---

## 2. Entity Details & Integrity Constraints

### 2.1 MentorMatch
- **`mentor_profiles`**:
  - `alumni_id`: Foreign key to `public.alumni_profiles(id) ON DELETE CASCADE`.
  - `user_id`: Foreign key to `public.users(id) ON DELETE CASCADE`.
  - `max_active_mentees`: Capacity threshold (default 3, positive check).
  - `current_active_mentees`: Current load, guarded by table check `current_active_mentees <= max_active_mentees`.
  - `advisory_topics`: PostgreSQL `TEXT[]` array of mentoring specializations.
- **`mentor_requests`**:
  - `status`: Enumerated check (`pending`, `accepted`, `rejected`, `completed`, `cancelled`).
  - Partial Unique Index `uq_active_mentor_request`: Enforces that a student cannot submit multiple concurrent `pending` requests to the same mentor.

### 2.2 CareerBridge
- **`jobs`**:
  - `opportunity_type`: Check (`full_time`, `internship`, `contract`, `part_time`).
  - `workplace_type`: Check (`remote`, `hybrid`, `onsite`).
  - `required_skills`: `TEXT[]` array for skill-overlap calculations.
  - `application_deadline`: `TIMESTAMPTZ` enabling automatic exclusion of expired postings.
- **`job_applications`**:
  - Unique Constraint `uq_job_applications_user(job_id, applicant_id)`: Enforces duplicate application prevention transactionally.
  - `status`: Check (`submitted`, `under_review`, `interviewing`, `accepted`, `rejected`, `withdrawn`).

### 2.3 Events & Reunions
- **`events`**:
  - `event_type`: Check (`webinar`, `reunion`, `workshop`, `career_fair`, `conference`).
  - Timing Constraint: `chk_event_times CHECK (end_time > start_time)`.
  - Capacity Constraint: `chk_event_capacity CHECK (current_registrations <= max_capacity)`.
- **`event_registrations`**:
  - Unique Constraint `uq_event_registrations_user(event_id, user_id)`: Prevents multi-booking by the same institutional member.
  - `ticket_code`: Unique UUID token for check-in verification.

### 2.4 Global Connect
- **`alumni_chapters`**:
  - Unique Constraint `uq_chapter_city(country, city)`: Regional chapter registry.

---

## 3. Row Level Security (RLS) Policy Matrix

| Table | Operation | Allowed Roles | Policy Condition |
|:---|:---:|:---:|:---|
| `mentor_profiles` | SELECT | Authenticated | `is_accepting_requests = TRUE OR auth.uid() = user_id` |
| `mentor_profiles` | UPDATE | Mentor Owner | `auth.uid() = user_id` |
| `mentor_requests` | SELECT | Student / Mentor | `auth.uid() = student_id OR auth.uid() IN (SELECT user_id FROM mentor_profiles WHERE id = mentor_id)` |
| `mentor_requests` | INSERT | Student | `auth.uid() = student_id` |
| `mentor_requests` | UPDATE | Mentor / Student | `auth.uid() = student_id OR auth.uid() IN (SELECT user_id FROM mentor_profiles WHERE id = mentor_id)` |
| `jobs` | SELECT | Authenticated | `is_active = TRUE OR auth.uid() = creator_id` |
| `jobs` | INSERT | Recruiter / Admin | `auth.uid() = creator_id` |
| `job_applications` | SELECT | Applicant / Poster | `auth.uid() = applicant_id OR auth.uid() IN (SELECT creator_id FROM jobs WHERE id = job_id)` |
| `job_applications` | INSERT | Applicant | `auth.uid() = applicant_id` |
| `events` | SELECT | Authenticated | `is_published = TRUE OR auth.uid() = organizer_id` |
| `event_registrations`| SELECT | Registrant | `auth.uid() = user_id` |
| `event_registrations`| INSERT | Registrant | `auth.uid() = user_id` |
| `alumni_chapters` | SELECT | Authenticated | `TRUE` |

---

## 4. Migration Execution Verification

The migration is additive, preserves all Phase 1 schema, and introduces zero breaking changes.
Command to apply when connected to Supabase:
```bash
supabase db push
```
