# MSGI ONE — PHASE 5 DATASET MANIFEST & REPOSITORY CATALOG

**Document Reference:** `docs/PHASE_5_DATASET_MANIFEST.md`  
**Phase:** 5 of 5 — Final Quality Assurance, Release Readiness and Dataset Ingestion  
**Status:** VALIDATED AND AUDITED (100% REPRODUCIBLE)  
**Target Environment:** Local SQLite / Seed Fixtures + Staging Supabase PostgreSQL  
**Data Privacy Enforcement:** 100% Synthetic (`@example.msgi.edu`), Zero Institutional Data Fabrication  

---

## 1. DATASET DIRECTORY LAYOUT

All datasets are maintained under version control in `supabase/seed/` with modular CSV tables in `supabase/seed/csv/` and test scenario streams in `*.jsonl`:

```
msgi-one/supabase/seed/
├── 00001_synthetic_seed.sql                # Phase 1 Auth & Core Profile SQL seed
├── 00004_phase_4_synthetic_seed.sql        # Phase 4 Relational SQL seed (9 entities)
├── ai_evaluation_cases.jsonl               # 15 AI Command Centre benchmark evaluation cases
├── qa_workflow_cases.jsonl                 # 8 Phase 5 Multi-User End-to-End Workflow scenarios
├── qa_security_cases.jsonl                 # 8 Phase 5 Security, Privacy & Compliance test cases
└── csv/
    ├── alumni.csv                          # 4 Verified Alumni Directory profiles
    ├── career_role_skills.csv              # 25 Role-to-Skill Taxonomy mappings
    ├── communities.csv                     # 6 Institutional Communities (4 public, 2 private)
    ├── community_memberships.csv           # 12 Community Memberships and join requests
    ├── events.csv                          # 2 Institutional & Chapter Events
    ├── impact_programmes.csv               # 4 Non-monetary Volunteering & Impact Programmes
    ├── jobs.csv                            # 3 CareerBridge Job Opportunities
    ├── learning_resources.csv              # 11 Curated Skill-Gap Learning Modules
    ├── mentors.csv                         # 3 MentorMatch Profiles with availability
    ├── projects.csv                        # 6 Collaborative Cross-Discipline Projects
    ├── qa_role_permissions.csv             # 35 Endpoint Role-Permission & RLS boundary definitions
    ├── qa_test_users.csv                   # 14 Multi-Role Synthetic QA Test Accounts
    ├── startups.csv                        # 5 Incubator & Alumni Startups
    ├── student_skills.csv                  # 9 Verified Student Skill Inventory records
    └── verification_requests.csv           # 5 Pending Institutional Credential Verification records
```

---

## 2. DATASET SPECIFICATIONS & RECORD COUNTS

| # | Dataset File | Entities / Records | Domain Module | Primary Key / Identifier | Foreign Key Dependencies | Demo vs Live Policy |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **1** | `csv/alumni.csv` | 4 records | Alumni Network (Mod 1) | `user_id` | `auth.users(id)` | Demo: `@example.msgi.edu` synthetic profiles; Live: institutional registrar sync |
| **2** | `csv/jobs.csv` | 3 records | CareerBridge (Mod 2) | `job_id` | `users(id)` (recruiter) | Demo: verified job mockups; Live: employer portal submissions |
| **3** | `csv/career_role_skills.csv` | 25 records | CareerBridge (Mod 2) | `(role_id, skill_name)` | None (Taxonomy root) | Standardized taxonomy across both environments |
| **4** | `csv/learning_resources.csv` | 11 records | Learning & Upskilling (Mod 7) | `resource_id` | `career_role_skills(skill_name)` | Curated educational resources (Coursera, edX, Docs) |
| **5** | `csv/student_skills.csv` | 9 records | Identity & Skills (Mod 1) | `(user_id, skill_name)` | `users(id)` | Demo: synthetic student records; Live: student self-declaration |
| **6** | `csv/communities.csv` | 6 records | Communities (Mod 8) | `community_id` | `users(id)` (creator) | 4 public open groups, 2 private moderated groups |
| **7** | `csv/community_memberships.csv` | 12 records | Communities (Mod 8) | `membership_id` | `communities(community_id)`, `users(id)` | 9 active memberships, 3 pending join requests |
| **8** | `csv/verification_requests.csv` | 5 records | Institutional Admin (Mod 9) | `request_id` | `users(id)` | 100% enter with `status='pending'`; zero auto-approval |
| **9** | `csv/projects.csv` | 6 records | Collaborative Projects (Mod 11) | `project_id` | `users(id)` (owner) | Multi-skill projects across AI, IoT, Web, Systems |
| **10** | `csv/startups.csv` | 5 records | Startups & Incubation (Mod 12) | `startup_id` | `users(id)` (founder) | Stages: idea, seed, early, growth; zero financial claims |
| **11** | `csv/impact_programmes.csv` | 4 records | Social Impact & Giving (Mod 12) | `programme_id` | None (Coordinator name) | Non-monetary only; zero payment fields permitted |
| **12** | `csv/qa_test_users.csv` | 14 records | QA Multi-Role Matrix | `user_id` | `auth.users(id)` | Covers Student, Alumni, Faculty, Recruiter, Admin, Candidate |
| **13** | `csv/qa_role_permissions.csv` | 35 records | RBAC & RLS Test Spec | `(endpoint, method)` | None | Defines allowed, forbidden, and owner-only access rules |
| **14** | `qa_workflow_cases.jsonl` | 8 scenarios | E2E Integration Suite | `case_id` | Multi-module actors | Multi-step interactive lifecycle scenarios |
| **15** | `qa_security_cases.jsonl` | 8 scenarios | DevSecOps & Compliance | `case_id` | Multi-module targets | Privacy masking, RLS isolation, privilege escalation, GDPR |
| **16** | `ai_evaluation_cases.jsonl` | 15 scenarios | LangGraph AI Command Centre | `case_id` | Subagent domains | Intent discovery, roadmaps, HITL safety, prompt injection |

**Total Ingestion Footprint:**  
- **13 CSV Datasets:** 139 Accepted Rows (validated via `scripts/import_synthetic_data.py --dry-run`)
- **3 JSONL Evaluation Suites:** 31 Scenarios (15 AI benchmarks + 8 workflow lifecycles + 8 security cases)
- **Zero Foreign-Key Violations or Unresolved Aliases**

---

## 3. SYNTHETIC PERSONA CATALOG (`qa_test_users.csv`)

| User ID | Full Name | Primary Role | Verification Status | Department / Organization | Persona Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `user-student-001` | Alex Rivera | Student | Verified | Computer Science (2025) | Active student seeking cloud/backend internships |
| `user-student-002` | Jordan Smith | Student | Verified | Electrical Engineering (2026) | Undergraduate exploring robotics and embedded systems |
| `user-student-phase4-001` | Priya Nair | Student | Verified | Data Science (2025) | Graduate researcher in NLP and LLM alignment |
| `user-student-phase4-002` | Lucas Vance | Student | Verified | Information Systems (2026) | Junior student exploring cloud operations and DevOps |
| `student-journey-uuid-999` | Journey Test Student | Student | Verified | Computer Science (2025) | Dedicated persona for automated end-to-end integration tests |
| `user-kenji-001` | Kenji Sato | Alumni | Verified | Cloud Solutions Architect, Tokyo | Active mentor, cloud infrastructure lead |
| `user-ananya-002` | Ananya Sharma | Alumni | Verified | Staff AI Engineer, Bengaluru | Founder of NeuralFlow, AI researcher, community moderator |
| `user-david-003` | David Chen | Alumni | Verified | Principal Product Manager, Singapore | Private alumni profile with restricted contact visibility |
| `user-yuki-004` | Yuki Tanaka | Alumni | Verified | Senior Data Scientist, Tokyo | Chapter lead, mentor with coarse location consent |
| `user-candidate-001` | Maya Patel | Alumni | Pending | Biomedical Informatics (2023) | Unverified alumni awaiting credential review |
| `user-candidate-002` | Carlos Mendez | Alumni | Pending | Software Engineering (2022) | Test account for GDPR account erasure validation |
| `user-faculty-001` | Dr. Robert Zhang | Faculty | Verified | Computer Science Department Head | Project creator, research lab director |
| `user-recruiter-001` | Elena Rostova | Recruiter | Verified | Talent Partner, CloudNative Labs | Corporate job posting author |
| `user-admin-001` | Sarah Jenkins | Admin | Verified | Institutional Affairs | Central administrator with audit log and verification rights |

---

## 4. INGESTION RUNNER VERIFICATION

The dataset ingestion pipeline was verified with `--dry-run`:
```
================================================================================
MSGI ONE — DATA INGESTION PIPELINE (MODE: DEMO)
Dry Run: True
Target Directory: C:\Users\dharneesh\OneDrive\Documents\msgi-one\supabase\seed\csv
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
