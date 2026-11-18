# MSGI One — Data Dictionary

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** Database Architect & Data Governance Lead  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Data Dictionary Conventions

- **UUID:** RFC 4122 universally unique identifier (`gen_random_uuid()`).
- **TIMESTAMPTZ:** Timestamp with explicit UTC timezone offset (`now()`).
- **VECTOR(1536):** High-dimensional float array for OpenAI / Gemini embedding representation.
- **JSONB:** Binary structured JSON document with GIN index support.
- **TEXT[]:** PostgreSQL native variable-length string array.

---

## 2. Entity Attribute Catalog

### Table: `users`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | — | PK, FK -> `auth.users(id)` ON DELETE CASCADE | Central user identifier proxying Supabase Auth. |
| `email` | VARCHAR(255) | No | — | UNIQUE, format validated | Institutional or verified personal email address. |
| `first_name` | VARCHAR(100) | No | — | — | User legal first name. |
| `last_name` | VARCHAR(100) | No | — | — | User legal surname. |
| `avatar_url` | TEXT | Yes | NULL | Valid URI | Public CDN URL for profile avatar image. |
| `is_verified` | BOOLEAN | No | `FALSE` | — | True if degree or institutional affiliation is officially verified. |
| `is_active` | BOOLEAN | No | `TRUE` | — | Soft account disable flag. |
| `created_at` | TIMESTAMPTZ | No | `now()` | — | System registration timestamp. |
| `updated_at` | TIMESTAMPTZ | No | `now()` | — | Record modification timestamp. |
| `deleted_at` | TIMESTAMPTZ | Yes | NULL | — | Soft-delete timestamp for GDPR grace period. |

### Table: `roles`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | VARCHAR(50) | No | — | PK | Role code (`student`, `alumni`, `faculty`, `recruiter`, `admin`). |
| `description` | TEXT | No | — | — | Human-readable explanation of role responsibilities. |

### Table: `user_roles`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Surrogate primary key. |
| `user_id` | UUID | No | — | FK -> `users(id)` ON DELETE CASCADE | Target user receiving role. |
| `role_id` | VARCHAR(50) | No | — | FK -> `roles(id)` ON DELETE RESTRICT | Target role assigned. |
| `assigned_at` | TIMESTAMPTZ | No | `now()` | — | Role grant timestamp. |
| `assigned_by` | UUID | Yes | NULL | FK -> `users(id)` ON DELETE SET NULL | Administrator user who granted role. |

### Table: `alumni_profiles`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Surrogate key. |
| `user_id` | UUID | No | — | UNIQUE, FK -> `users(id)` ON DELETE CASCADE | Associated user account. |
| `graduation_year`| INTEGER | No | — | CHECK (year BETWEEN 1950 AND 2035) | Institutional graduation year. |
| `degree` | VARCHAR(100) | No | — | — | Degree earned (e.g. B.Tech, M.S., Ph.D.). |
| `major` | VARCHAR(100) | No | — | — | Academic major / department (e.g. Computer Science). |
| `headline` | VARCHAR(255) | Yes | NULL | — | Professional bio snippet (e.g. "Senior ML Engineer at Mercari"). |
| `bio` | TEXT | Yes | NULL | — | Detailed narrative biography. |
| `current_company`| VARCHAR(150)| Yes | NULL | — | Current employing organization. |
| `current_title` | VARCHAR(150) | Yes | NULL | — | Current job title. |
| `industry` | VARCHAR(100) | Yes | NULL | — | Industry sector (e.g. Artificial Intelligence, FinTech). |
| `embedding` | VECTOR(1536) | Yes | NULL | HNSW indexed | Semantic vector representation for AI matching. |
| `visibility` | VARCHAR(30) | No | `'institutional'` | CHECK (`public`, `institutional`, `connections_only`, `private`) | Profile directory exposure boundary. |

### Table: `student_profiles`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Surrogate key. |
| `user_id` | UUID | No | — | UNIQUE, FK -> `users(id)` ON DELETE CASCADE | Associated user account. |
| `roll_number` | VARCHAR(50) | No | — | UNIQUE | Institutional student register identifier. |
| `enrollment_year`| INTEGER | No | — | CHECK (year BETWEEN 2015 AND 2035) | Academic matriculation year. |
| `expected_graduation_year`| INTEGER | No | — | CHECK (expected >= enrollment) | Target completion year. |
| `department` | VARCHAR(100) | No | — | — | Academic division. |
| `degree_program`| VARCHAR(100)| No | — | — | Undergraduate / Postgraduate program. |
| `cgpa` | NUMERIC(3, 2)| Yes | NULL | CHECK (cgpa BETWEEN 0.00 AND 10.00)| Cumulative Grade Point Average (Private). |
| `resume_url` | TEXT | Yes | NULL | Storage S3 Path | Private signed URL pointer to latest CV. |
| `career_interests`| TEXT[] | No | `'{}'` | — | Target career aspiration tags. |

### Table: `skills`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Skill identifier. |
| `name` | VARCHAR(100) | No | — | UNIQUE | Canonical skill name (e.g. "PyTorch", "Rust"). |
| `category` | VARCHAR(50) | No | — | CHECK (`technical`, `business`, `design`, `soft_skill`, `language`) | Skill classification. |

### Table: `user_skills`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Mapping primary key. |
| `user_id` | UUID | No | — | FK -> `users(id)` ON DELETE CASCADE | Skill owner. |
| `skill_id` | UUID | No | — | FK -> `skills(id)` ON DELETE CASCADE | Associated taxonomy skill. |
| `proficiency` | VARCHAR(30) | No | `'intermediate'` | CHECK (`beginner`, `intermediate`, `advanced`, `expert`) | Self-reported competency level. |
| `verified` | BOOLEAN | No | `FALSE` | — | Peer or faculty endorsed. |

### Table: `alumni_locations`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Location identifier. |
| `user_id` | UUID | No | — | UNIQUE, FK -> `users(id)` ON DELETE CASCADE | Associated user. |
| `country_code` | VARCHAR(2) | No | — | ISO 3166-1 alpha-2 | Country code (e.g. JP, US, IN). |
| `country_name` | VARCHAR(100) | No | — | — | Human-readable country name. |
| `city` | VARCHAR(100) | No | — | — | Current city of residence. |
| `latitude` | NUMERIC(9, 6)| No | — | — | Geographic latitude coordinate. |
| `longitude` | NUMERIC(9, 6)| No | — | — | Geographic longitude coordinate. |
| `chapter_name` | VARCHAR(100) | Yes | NULL | — | Associated regional alumni chapter. |
| `is_public` | BOOLEAN | No | `TRUE` | — | Privacy opt-in for Global Connect map. |

### Table: `jobs`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Job posting key. |
| `posted_by` | UUID | No | — | FK -> `users(id)` ON DELETE CASCADE | Recruiter or alumni poster. |
| `company_name` | VARCHAR(150) | No | — | — | Hiring corporation. |
| `title` | VARCHAR(150) | No | — | — | Role title. |
| `description` | TEXT | No | — | Length >= 50 chars | Complete job description and responsibilities. |
| `employment_type`| VARCHAR(50) | No | — | CHECK (`full_time`, `part_time`, `internship`, `contract`, `remote`)| Employment engagement structure. |
| `location` | VARCHAR(100) | No | — | — | Job physical location or "Remote". |
| `salary_min` | INTEGER | Yes | NULL | — | Compensation lower bound. |
| `salary_max` | INTEGER | Yes | NULL | — | Compensation upper bound. |
| `currency` | VARCHAR(3) | No | `'USD'` | — | ISO 4217 3-letter currency code. |
| `required_skills`| TEXT[] | No | `'{}'` | — | Must-have competency keywords. |
| `application_deadline`| TIMESTAMPTZ| No | — | Must be future date | Application closing timestamp. |
| `is_active` | BOOLEAN | No | `TRUE` | — | Listing publication status. |
| `embedding` | VECTOR(1536) | Yes | NULL | HNSW indexed | Semantic vector for skill-to-job matching. |

### Table: `job_applications`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Application key. |
| `job_id` | UUID | No | — | FK -> `jobs(id)` ON DELETE CASCADE | Target opening. |
| `applicant_id` | UUID | No | — | FK -> `users(id)` ON DELETE CASCADE | Submitting student/alumni. |
| `resume_url` | TEXT | No | — | Signed URL | Encrypted resume asset pointer. |
| `cover_letter` | TEXT | Yes | NULL | — | Optional applicant statement. |
| `status` | VARCHAR(30) | No | `'submitted'` | CHECK (`submitted`, `under_review`, `shortlisted`, `rejected`, `offered`)| Applicant review state. |

### Table: `mentor_profiles`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Mentor configuration key. |
| `alumni_id` | UUID | No | — | UNIQUE, FK -> `alumni_profiles(id)` ON DELETE CASCADE | Alumni offering mentorship. |
| `topics` | TEXT[] | No | `'{}'` | — | Mentorship advisory areas. |
| `max_mentees` | INTEGER | No | `3` | CHECK (max BETWEEN 1 AND 20) | Active student concurrency limit. |
| `active_mentees`| INTEGER | No | `0` | CHECK (active >= 0) | Currently enrolled mentees count. |
| `is_accepting_requests`| BOOLEAN | No | `TRUE` | — | Mentorship open/closed switch. |

### Table: `mentor_requests`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Mentorship request key. |
| `mentee_id` | UUID | No | — | FK -> `users(id)` ON DELETE CASCADE | Requesting student user. |
| `mentor_id` | UUID | No | — | FK -> `mentor_profiles(id)` ON DELETE CASCADE | Target alumni mentor. |
| `goal_statement`| TEXT | No | — | Length >= 20 chars | Mentee objective narrative. |
| `status` | VARCHAR(30) | No | `'pending'` | CHECK (`pending`, `accepted`, `declined`, `completed`, `cancelled`)| Workflow status. |
| `rejection_reason`| TEXT | Yes | NULL | — | Explanation if declined. |

### Table: `agent_runs`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | LangGraph execution trace key. |
| `user_id` | UUID | No | — | FK -> `users(id)` ON DELETE CASCADE | Initiating user. |
| `workflow_type` | VARCHAR(100) | No | — | — | Name of graph workflow executed. |
| `prompt_input` | TEXT | No | — | — | Raw user prompt. |
| `state_graph_snapshot`| JSONB | No | `'{}'` | — | Serialized LangGraph state at checkpoint. |
| `status` | VARCHAR(30) | No | `'in_progress'` | CHECK (`in_progress`, `completed`, `awaiting_approval`, `failed`, `cancelled`)| Orchestrator lifecycle state. |
| `final_output` | JSONB | Yes | NULL | — | Structured output payload. |
| `total_tokens` | INTEGER | No | `0` | — | Aggregate LLM token consumption. |
| `latency_ms` | INTEGER | No | `0` | — | Execution duration in milliseconds. |

### Table: `approval_requests`
| Column Name | Data Type | Nullable | Default | Constraints / References | Description |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `id` | UUID | No | `gen_random_uuid()` | PK | Approval gate key. |
| `run_id` | UUID | No | — | FK -> `agent_runs(id)` ON DELETE CASCADE | Parent agent workflow. |
| `user_id` | UUID | No | — | FK -> `users(id)` ON DELETE CASCADE | Authorizing user. |
| `action_type` | VARCHAR(100) | No | — | CHECK (`send_mentor_request`, `contact_alumni`, `apply_job`, `publish_event`, `update_record`, `financial_action`)| Consequential boundary category. |
| `payload` | JSONB | No | — | — | Exact parameters to execute upon approval. |
| `status` | VARCHAR(30) | No | `'pending'` | CHECK (`pending`, `approved`, `rejected`, `expired`)| Human decision status. |
| `decision_reason`| TEXT | Yes | NULL | — | Optional user justification. |
