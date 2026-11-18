# MSGI One — Comprehensive Data Import and Ingestion Guide

**Project:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Target Environment:** Python 3.12, PostgreSQL / Supabase, SQLite  
**Script Location:** `scripts/import_synthetic_data.py`  
**Engineering Standards:** Silberschatz Invariant Preservation & Kleppmann Schema Evolution  

---

## 1. Overview of Ingestion Pipeline

The data ingestion pipeline provides automated schema validation, domain rule checking, and database seeding for institutional alumni data. It guarantees that synthetic test data strictly complies with Rule 8 and Rule 9 (using `@example.msgi.edu` email addresses) while allowing verified real institutional registries to be imported in `live` mode.

---

## 2. Supported Datasets and Header Schemas

| Dataset | CSV File | Key Columns | Validation Rules |
|---|---|---|---|
| **Alumni Directory** | `alumni.csv` | `user_id`, `full_name`, `email`, `graduation_year`, `degree`, `major`, `company`, `title`, `industry`, `country`, `city`, `skills`, `is_verified`, `mentor_opt_in` | Demo emails must end with `@example.msgi.edu`; `1950 <= graduation_year <= 2030`. |
| **Job Opportunities** | `jobs.csv` | `job_id`, `title`, `company`, `location`, `country`, `opportunity_type`, `workplace_type`, `required_skills`, `deadline_days` | `opportunity_type` must be one of `full_time`, `internship`, `contract`, `part_time`. |
| **Career Role Skills** | `career_role_skills.csv` | `role_id`, `target_role`, `skill_name`, `importance_weight`, `category`, `minimum_proficiency` | `0.0 <= importance_weight <= 1.0`; categories: `Language`, `Framework`, `DevOps`, `Systems`. |
| **Learning Resources** | `learning_resources.csv` | `resource_id`, `title`, `provider`, `target_skill`, `difficulty`, `duration_hours`, `url`, `rating` | `difficulty` in `Beginner`, `Intermediate`, `Advanced`; `rating <= 5.0`. |
| **Student Skills** | `student_skills.csv` | `user_id`, `skill_name`, `proficiency_level`, `years_experience`, `is_verified` | `proficiency_level` in `Beginner`, `Intermediate`, `Advanced`, `Expert`. |

---

## 3. Running the Ingestion Pipeline

### Demo Mode (Default — Synthetic Seed Data)
```bash
uv run --offline --no-sync --project services/api python scripts/import_synthetic_data.py --mode demo
```

### Live Mode (Production Institutional Registry)
```bash
uv run --offline --no-sync --project services/api python scripts/import_synthetic_data.py --mode live --dir path/to/institutional_csvs/
```

---

## 4. Execution Evidence

Terminal execution of the ingestion pipeline during Phase 4 verification:
```
================================================================================
MSGI ONE — DATA INGESTION PIPELINE (MODE: DEMO)
Target Directory: C:\Users\dharneesh\OneDrive\Documents\msgi-one\supabase\seed\csv
================================================================================
Alumni            : SUCCESS (Accepted: 3, Rejected: 0)
Jobs              : SUCCESS (Accepted: 3, Rejected: 0)
Role Skills       : SUCCESS (Accepted: 25, Rejected: 0)
Learning Resources: SUCCESS (Accepted: 11, Rejected: 0)
Student Skills    : SUCCESS (Accepted: 9, Rejected: 0)
================================================================================
Ingestion validation complete.
```
All synthetic data rows passed validation with 0 rejections and 0 malformed records.
