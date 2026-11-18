# MSGI One — Relational Database Architecture & Design

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** Database Architect & Principal Software Architect  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Database Engineering Principles

The database architecture is designed in strict accordance with the classical relational theory of **Abraham Silberschatz, Henry F. Korth, and S. Sudarshan** (*Database System Concepts*, 7th Edition):
1. **Third Normal Form (3NF) & Boyce-Codd Normal Form (BCNF):** Eliminates insertion, update, and deletion anomalies across all core transactional entities.
2. **Referential Integrity:** Enforced via foreign key constraints with explicit referential actions (`ON DELETE CASCADE` for tightly bound child records like profile extensions; `ON DELETE RESTRICT` for financial and employment records).
3. **Surrogate Primary Keys:** All transactional tables utilize standard RFC 4122 UUID v4 keys (`gen_random_uuid()`) to eliminate enumeration attacks and simplify distributed replication.
4. **Separation of Concerns:** Zero passwords stored in custom tables. Authentication identity is owned by Supabase Auth (`auth.users`), with application profile metadata isolated in `public.users` and role-specific profile extensions.
5. **Privacy Separation (FERPA / GDPR):** Publicly displayable data (graduation year, degree, industry) is strictly separated from private personal data (email, phone, CGPA, donation amounts) through explicit visibility flags and Row-Level Security.

---

## 2. Domain Schema Groupings

```
msgi_one_db
├── 1. Identity & Access Domain
│   ├── users
│   ├── roles
│   ├── user_roles
│   ├── student_profiles
│   ├── alumni_profiles
│   ├── faculty_profiles
│   ├── recruiter_profiles
│   ├── user_preferences
│   └── consent_records
├── 2. Professional & Networking Domain
│   ├── skills
│   ├── user_skills
│   ├── employment_history
│   ├── alumni_locations
│   └── connections
├── 3. Career & Mentorship Domain
│   ├── jobs
│   ├── job_applications
│   ├── mentor_profiles
│   ├── mentor_requests
│   ├── mentor_sessions
│   └── career_goals
├── 4. Engagement & Communities Domain
│   ├── events
│   ├── event_registrations
│   ├── communities
│   └── community_memberships
├── 5. Learning & Innovation Domain
│   ├── courses
│   ├── learning_progress
│   ├── projects
│   ├── project_members
│   ├── startups
│   └── startup_members
├── 6. Institutional Operations Domain
│   ├── impact_programmes
│   ├── volunteering_records
│   ├── donation_records
│   └── institutional_documents
└── 7. AI & Observability Domain
    ├── agent_runs
    ├── agent_actions
    ├── approval_requests
    ├── notifications
    └── audit_logs
```

---

## 3. Detailed Table Schema Definitions

### 3.1 Identity & Access Domain

#### `users`
Central identity proxy linked to `auth.users`.
- `id` UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE
- `email` VARCHAR(255) NOT NULL UNIQUE
- `first_name` VARCHAR(100) NOT NULL
- `last_name` VARCHAR(100) NOT NULL
- `avatar_url` TEXT NULL
- `is_verified` BOOLEAN NOT NULL DEFAULT FALSE
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `deleted_at` TIMESTAMPTZ NULL

#### `roles`
Enumeration of institutional system roles.
- `id` VARCHAR(50) PRIMARY KEY (Values: `student`, `alumni`, `faculty`, `recruiter`, `admin`)
- `description` TEXT NOT NULL

#### `user_roles`
Many-to-many role assignments with audit timestamps.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `role_id` VARCHAR(50) NOT NULL REFERENCES roles(id) ON DELETE RESTRICT
- `assigned_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `assigned_by` UUID NULL REFERENCES users(id) ON DELETE SET NULL
- UNIQUE (`user_id`, `role_id`)

#### `alumni_profiles`
Public and private professional data for verified graduates.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
- `graduation_year` INTEGER NOT NULL CHECK (graduation_year BETWEEN 1950 AND 2035)
- `degree` VARCHAR(100) NOT NULL
- `major` VARCHAR(100) NOT NULL
- `headline` VARCHAR(255) NULL
- `bio` TEXT NULL
- `current_company` VARCHAR(150) NULL
- `current_title` VARCHAR(150) NULL
- `industry` VARCHAR(100) NULL
- `embedding` vector(1536) NULL -- pgvector for semantic discovery
- `visibility` VARCHAR(30) NOT NULL DEFAULT 'institutional' CHECK (visibility IN ('public', 'institutional', 'connections_only', 'private'))
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `student_profiles`
Academic records and career search status for active students.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
- `roll_number` VARCHAR(50) NOT NULL UNIQUE
- `enrollment_year` INTEGER NOT NULL CHECK (enrollment_year BETWEEN 2015 AND 2035)
- `expected_graduation_year` INTEGER NOT NULL CHECK (expected_graduation_year >= enrollment_year)
- `department` VARCHAR(100) NOT NULL
- `degree_program` VARCHAR(100) NOT NULL
- `cgpa` NUMERIC(3, 2) NULL CHECK (cgpa >= 0.00 AND cgpa <= 10.00)
- `resume_url` TEXT NULL -- Supabase Storage path
- `career_interests` TEXT[] NOT NULL DEFAULT '{}'
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `faculty_profiles`
Academic departments, research domains, and supervisory roles.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
- `department` VARCHAR(100) NOT NULL
- `designation` VARCHAR(100) NOT NULL
- `research_interests` TEXT[] NOT NULL DEFAULT '{}'
- `office_location` VARCHAR(100) NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `recruiter_profiles`
Corporate hiring affiliations and job poster credentials.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
- `company_name` VARCHAR(150) NOT NULL
- `company_website` VARCHAR(255) NULL
- `corporate_email` VARCHAR(255) NOT NULL
- `verification_status` VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (verification_status IN ('pending', 'approved', 'rejected'))
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `user_preferences`
Mobile app settings, push notifications, and UI themes.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
- `push_notifications_enabled` BOOLEAN NOT NULL DEFAULT TRUE
- `email_digests_enabled` BOOLEAN NOT NULL DEFAULT TRUE
- `theme` VARCHAR(20) NOT NULL DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system'))
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `consent_records`
Explicit privacy consent log for FERPA/GDPR compliance.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `consent_type` VARCHAR(100) NOT NULL CHECK (consent_type IN ('directory_listing', 'ai_profiling', 'recruiter_contact', 'location_sharing'))
- `granted` BOOLEAN NOT NULL DEFAULT FALSE
- `granted_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `revoked_at` TIMESTAMPTZ NULL
- UNIQUE (`user_id`, `consent_type`)

---

### 3.2 Professional & Networking Domain

#### `skills`
Central standardized skills taxonomy.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `name` VARCHAR(100) NOT NULL UNIQUE
- `category` VARCHAR(50) NOT NULL CHECK (category IN ('technical', 'business', 'design', 'soft_skill', 'language'))
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `user_skills`
User competency endorsements and proficiency ratings.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `skill_id` UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE
- `proficiency` VARCHAR(30) NOT NULL DEFAULT 'intermediate' CHECK (proficiency IN ('beginner', 'intermediate', 'advanced', 'expert'))
- `verified` BOOLEAN NOT NULL DEFAULT FALSE
- UNIQUE (`user_id`, `skill_id`)

#### `employment_history`
Verifiable corporate track record for alumni.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `alumni_id` UUID NOT NULL REFERENCES alumni_profiles(id) ON DELETE CASCADE
- `company_name` VARCHAR(150) NOT NULL
- `title` VARCHAR(150) NOT NULL
- `location` VARCHAR(100) NULL
- `start_date` DATE NOT NULL
- `end_date` DATE NULL -- NULL signifies currently employed
- `is_current` BOOLEAN NOT NULL DEFAULT FALSE
- `description` TEXT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `alumni_locations`
Geographic coordinates for Global Connect Chapter mapping.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
- `country_code` VARCHAR(2) NOT NULL -- ISO 3166-1 alpha-2
- `country_name` VARCHAR(100) NOT NULL
- `city` VARCHAR(100) NOT NULL
- `latitude` NUMERIC(9, 6) NOT NULL
- `longitude` NUMERIC(9, 6) NOT NULL
- `chapter_name` VARCHAR(100) NULL
- `is_public` BOOLEAN NOT NULL DEFAULT TRUE
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `connections`
Mutual peer-to-peer relationships between users.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `requester_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `addressee_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `status` VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'blocked'))
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- CHECK (requester_id != addressee_id),
- UNIQUE (`requester_id`, `addressee_id`)

---

### 3.3 Career & Mentorship Domain

#### `jobs`
Job and internship listings.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `posted_by` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `company_name` VARCHAR(150) NOT NULL
- `title` VARCHAR(150) NOT NULL
- `description` TEXT NOT NULL
- `employment_type` VARCHAR(50) NOT NULL CHECK (employment_type IN ('full_time', 'part_time', 'internship', 'contract', 'remote'))
- `location` VARCHAR(100) NOT NULL
- `salary_min` INTEGER NULL
- `salary_max` INTEGER NULL
- `currency` VARCHAR(3) NOT NULL DEFAULT 'USD'
- `required_skills` TEXT[] NOT NULL DEFAULT '{}'
- `application_deadline` TIMESTAMPTZ NOT NULL
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `embedding` vector(1536) NULL -- pgvector for resume-job matching
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `job_applications`
Student job submissions.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `job_id` UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE
- `applicant_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `resume_url` TEXT NOT NULL
- `cover_letter` TEXT NULL
- `status` VARCHAR(30) NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'under_review', 'shortlisted', 'rejected', 'offered'))
- `applied_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- UNIQUE (`job_id`, `applicant_id`)

#### `mentor_profiles`
Mentorship availability settings.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `alumni_id` UUID NOT NULL UNIQUE REFERENCES alumni_profiles(id) ON DELETE CASCADE
- `topics` TEXT[] NOT NULL DEFAULT '{}'
- `max_mentees` INTEGER NOT NULL DEFAULT 3 CHECK (max_mentees BETWEEN 1 AND 20)
- `active_mentees` INTEGER NOT NULL DEFAULT 0 CHECK (active_mentees >= 0)
- `is_accepting_requests` BOOLEAN NOT NULL DEFAULT TRUE
- `meeting_preference` VARCHAR(30) NOT NULL DEFAULT 'virtual' CHECK (meeting_preference IN ('virtual', 'in_person', 'both'))
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `mentor_requests`
Mentorship match requests.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `mentee_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `mentor_id` UUID NOT NULL REFERENCES mentor_profiles(id) ON DELETE CASCADE
- `goal_statement` TEXT NOT NULL
- `status` VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'completed', 'cancelled'))
- `rejection_reason` TEXT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `mentor_sessions`
Scheduled mentorship meetings and logs.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `request_id` UUID NOT NULL REFERENCES mentor_requests(id) ON DELETE CASCADE
- `scheduled_at` TIMESTAMPTZ NOT NULL
- `meeting_link` TEXT NULL
- `status` VARCHAR(30) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show'))
- `mentor_notes` TEXT NULL
- `mentee_feedback` TEXT NULL
- `rating` INTEGER NULL CHECK (rating BETWEEN 1 AND 5)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `career_goals`
Structured student career targets used by the AI engine.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `student_id` UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE
- `target_role` VARCHAR(150) NOT NULL
- `target_country` VARCHAR(100) NOT NULL
- `target_industry` VARCHAR(100) NOT NULL
- `target_date` DATE NULL
- `skill_gap_summary` JSONB NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

---

### 3.4 Engagement, Events & Communities Domain

#### `events`
Institutional reunions, webinars, and meetups.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `organizer_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `title` VARCHAR(200) NOT NULL
- `description` TEXT NOT NULL
- `category` VARCHAR(50) NOT NULL CHECK (category IN ('reunion', 'webinar', 'networking', 'career_fair', 'workshop'))
- `location_type` VARCHAR(20) NOT NULL CHECK (location_type IN ('in_person', 'virtual', 'hybrid'))
- `venue_address` TEXT NULL
- `virtual_link` TEXT NULL
- `start_time` TIMESTAMPTZ NOT NULL
- `end_time` TIMESTAMPTZ NOT NULL CHECK (end_time > start_time)
- `capacity` INTEGER NOT NULL CHECK (capacity > 0)
- `registered_count` INTEGER NOT NULL DEFAULT 0 CHECK (registered_count <= capacity)
- `banner_url` TEXT NULL
- `is_published` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `event_registrations`
User RSVPs and attendance records.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `event_id` UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `status` VARCHAR(30) NOT NULL DEFAULT 'registered' CHECK (status IN ('registered', 'attended', 'cancelled'))
- `ticket_code` VARCHAR(50) NOT NULL UNIQUE
- `registered_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- UNIQUE (`event_id`, `user_id`)

#### `communities`
Affinity groups and regional clubs.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `creator_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `name` VARCHAR(100) NOT NULL UNIQUE
- `description` TEXT NOT NULL
- `privacy` VARCHAR(30) NOT NULL DEFAULT 'public' CHECK (privacy IN ('public', 'private', 'invite_only'))
- `member_count` INTEGER NOT NULL DEFAULT 1
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `community_memberships`
Community roster and moderation roles.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `community_id` UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `role` VARCHAR(30) NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'moderator', 'admin'))
- `joined_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- UNIQUE (`community_id`, `user_id`)

---

### 3.5 Learning & Innovation Domain

#### `courses`
Curated learning modules and upskilling tracks.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `title` VARCHAR(200) NOT NULL
- `description` TEXT NOT NULL
- `provider` VARCHAR(100) NOT NULL DEFAULT 'MSGI Academy'
- `course_url` TEXT NULL
- `difficulty` VARCHAR(30) NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced'))
- `associated_skills` TEXT[] NOT NULL DEFAULT '{}'
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `learning_progress`
Individual student progress through courses.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `course_id` UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE
- `status` VARCHAR(30) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('not_started', 'in_progress', 'completed'))
- `progress_percent` INTEGER NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100)
- `completed_at` TIMESTAMPTZ NULL
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- UNIQUE (`user_id`, `course_id`)

#### `projects`
Collaborative research and cross-department projects.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `lead_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `title` VARCHAR(200) NOT NULL
- `abstract` TEXT NOT NULL
- `status` VARCHAR(30) NOT NULL DEFAULT 'recruiting' CHECK (status IN ('recruiting', 'in_progress', 'completed', 'archived'))
- `required_skills` TEXT[] NOT NULL DEFAULT '{}'
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `project_members`
Project team assignments.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `project_id` UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `role` VARCHAR(100) NOT NULL DEFAULT 'contributor'
- `joined_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- UNIQUE (`project_id`, `user_id`)

#### `startups`
Alumni and student entrepreneurial ventures.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `founder_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `name` VARCHAR(150) NOT NULL
- `pitch_summary` TEXT NOT NULL
- `industry` VARCHAR(100) NOT NULL
- `stage` VARCHAR(50) NOT NULL CHECK (stage IN ('idea', 'mvp', 'seed', 'growth', 'profitable'))
- `website` VARCHAR(255) NULL
- `deck_url` TEXT NULL
- `is_verified` BOOLEAN NOT NULL DEFAULT FALSE
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `startup_members`
Co-founders and early startup employees.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `startup_id` UUID NOT NULL REFERENCES startups(id) ON DELETE CASCADE
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `role_title` VARCHAR(100) NOT NULL
- `is_cofounder` BOOLEAN NOT NULL DEFAULT FALSE
- `joined_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- UNIQUE (`startup_id`, `user_id`)

---

### 3.6 Institutional Operations Domain

#### `impact_programmes`
Institutional fundraising, endowment funds, and scholarships.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `title` VARCHAR(200) NOT NULL
- `description` TEXT NOT NULL
- `target_amount` NUMERIC(12, 2) NOT NULL CHECK (target_amount > 0)
- `raised_amount` NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (raised_amount >= 0)
- `currency` VARCHAR(3) NOT NULL DEFAULT 'USD'
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `donation_records`
Financial contributions and giving history.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `programme_id` UUID NOT NULL REFERENCES impact_programmes(id) ON DELETE RESTRICT
- `donor_id` UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT
- `amount` NUMERIC(12, 2) NOT NULL CHECK (amount > 0)
- `currency` VARCHAR(3) NOT NULL DEFAULT 'USD'
- `transaction_reference` VARCHAR(100) NOT NULL UNIQUE
- `is_anonymous` BOOLEAN NOT NULL DEFAULT FALSE
- `status` VARCHAR(30) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'refunded'))
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `volunteering_records`
Alumni guest lectures and volunteer service.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `title` VARCHAR(200) NOT NULL
- `hours_contributed` NUMERIC(6, 2) NOT NULL CHECK (hours_contributed > 0)
- `date_completed` DATE NOT NULL
- `verified_by` UUID NULL REFERENCES users(id) ON DELETE SET NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `institutional_documents`
Policy docs, accreditation records, and knowledge base files for RAG.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `title` VARCHAR(255) NOT NULL
- `category` VARCHAR(100) NOT NULL
- `file_url` TEXT NOT NULL
- `content_text` TEXT NOT NULL
- `embedding` vector(1536) NULL -- pgvector for institutional QA
- `uploaded_by` UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

---

### 3.7 AI & Observability Domain

#### `agent_runs`
Master trace of all LangGraph execution runs.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `workflow_type` VARCHAR(100) NOT NULL -- e.g. 'career_roadmap', 'alumni_search'
- `prompt_input` TEXT NOT NULL
- `state_graph_snapshot` JSONB NOT NULL DEFAULT '{}'
- `status` VARCHAR(30) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'awaiting_approval', 'failed', 'cancelled'))
- `final_output` JSONB NULL
- `total_tokens` INTEGER NOT NULL DEFAULT 0
- `latency_ms` INTEGER NOT NULL DEFAULT 0
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `agent_actions`
Fine-grained tool invocation audit trail.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `run_id` UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE
- `agent_name` VARCHAR(100) NOT NULL
- `tool_name` VARCHAR(100) NOT NULL
- `tool_input` JSONB NOT NULL
- `tool_output` JSONB NULL
- `status` VARCHAR(30) NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'error', 'blocked'))
- `execution_time_ms` INTEGER NOT NULL DEFAULT 0
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `approval_requests`
Human-in-the-loop consequential action gates.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `run_id` UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `action_type` VARCHAR(100) NOT NULL CHECK (action_type IN ('send_mentor_request', 'contact_alumni', 'apply_job', 'publish_event', 'update_record', 'financial_action'))
- `payload` JSONB NOT NULL
- `status` VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired'))
- `decision_reason` TEXT NULL
- `decided_at` TIMESTAMPTZ NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `notifications`
Real-time user alerts delivered via WebSocket / Push.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `user_id` UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `title` VARCHAR(200) NOT NULL
- `body` TEXT NOT NULL
- `category` VARCHAR(50) NOT NULL CHECK (category IN ('mentorship', 'career', 'event', 'ai_approval', 'system'))
- `metadata` JSONB NOT NULL DEFAULT '{}'
- `is_read` BOOLEAN NOT NULL DEFAULT FALSE
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

#### `audit_logs`
Immutable compliance and security audit trail.
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `actor_id` UUID NULL REFERENCES users(id) ON DELETE SET NULL
- `action` VARCHAR(100) NOT NULL
- `entity_type` VARCHAR(100) NOT NULL
- `entity_id` UUID NULL
- `ip_address` VARCHAR(45) NULL
- `user_agent` TEXT NULL
- `previous_state` JSONB NULL
- `new_state` JSONB NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

---

## 4. Indexing & Query Optimization Strategy

Following **Silberschatz et al. (Ch. 12: Indexing and Hashing)**:
1. **Primary & Foreign Key Indexes:** All foreign keys are indexed to prevent sequential scans during `JOIN` operations (e.g. `idx_alumni_profiles_user_id`, `idx_jobs_posted_by`, `idx_job_applications_job_id`).
2. **Filtering & Sorting Indexes:** Composite B-tree indexes for high-frequency queries:
   - `events(is_published, start_time)`
   - `jobs(is_active, application_deadline)`
   - `alumni_profiles(graduation_year, major)`
   - `alumni_locations(country_code, city)`
3. **Vector Similarity Indexes (pgvector):**
   - Hierarchical Navigable Small World (HNSW) index on `alumni_profiles(embedding)` using cosine distance (`vector_cosine_ops`) with parameters `m = 16, ef_construction = 64` for high-throughput sub-50ms approximate nearest neighbor (ANN) retrieval.
   - HNSW index on `jobs(embedding)` and `institutional_documents(embedding)`.

---

## 5. Deletion & Retention Policies

1. **User Deletion:** Complies with GDPR "Right to be Forgotten". When a user requests account deletion, a soft-delete (`deleted_at = now()`) is initiated. Personal profile data is anonymized after a 30-day recovery grace period. Financial donation records and audit logs are retained in anonymized form for institutional compliance.
2. **Audit & Log Retention:** `agent_actions` and `audit_logs` are retained for 365 days; historical `agent_runs` state snapshots are compressed after 90 days.
3. **Draft / Transient Data:** Unapproved AI workflow runs expire automatically after 7 days via database cleanup triggers.
