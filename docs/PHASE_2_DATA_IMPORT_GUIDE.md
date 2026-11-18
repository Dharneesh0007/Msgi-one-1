# MSGI One — Phase 2 Data Import & Ingestion Guide
**Standard Operating Procedure for Administrative CSV Import in DEMO and LIVE Modes**

**Document Version:** 1.0.0  
**Phase:** 2 (Core Business Modules)  
**Script:** `scripts/import_synthetic_data.py`  
**Compliance Standard:** AGENTS.md (Rule 8: No Real Data Fabrication, Rule 9: Labeled Synthetic Seed)  

---

## 1. Data Modes

The MSGI One ingestion pipeline supports two mutually exclusive modes:

### DEMO Mode
- **Purpose:** Local testing, CI pipelines, functional demonstrations, and QA validation.
- **Enforcement:** All email addresses MUST terminate in `@example.msgi.edu`.
- **Identity:** Relies on synthetic UUIDs mapped to seed authentication records.

### LIVE Mode
- **Purpose:** Production institutional roster loading by verified institutional administrators.
- **Enforcement:** Valid institutional university domains, verified identity matching, and student FERPA privacy agreements.
- **Audit:** All bulk imports generate audit log entries in `public.audit_logs`.

---

## 2. Supported CSV File Specifications

### 2.1 Alumni Records (`alumni.csv`)
**Target Table:** `public.alumni_profiles`
```csv
user_id,full_name,email,graduation_year,degree,major,company,title,industry,country,city,skills,is_verified,mentor_opt_in
user-kenji-001,Kenji Sato,kenji.sato@example.msgi.edu,2021,B.Tech,Information Technology,Rakuten Symphony,Staff AI Engineer,Artificial Intelligence,Japan,Tokyo,"Python;Machine Learning;PyTorch;FastAPI",true,true
```
- `user_id`: Must reference an existing identity in `public.users(id)`.
- `skills`: Semicolon-delimited list of skill names.
- `mentor_opt_in`: Boolean determining eligibility for the MentorMatch directory.

### 2.2 CareerBridge Listings (`jobs.csv`)
**Target Table:** `public.jobs`
```csv
job_id,title,company,location,country,opportunity_type,workplace_type,required_skills,deadline_days
job-ai-010,Machine Learning Platform Intern,Rakuten Symphony,"Tokyo, Japan",Japan,internship,hybrid,"Python;Machine Learning;PyTorch;FastAPI",30
```
- `opportunity_type`: Must be one of `full_time`, `internship`, `contract`, `part_time`.
- `workplace_type`: Must be one of `remote`, `hybrid`, `onsite`.
- `deadline_days`: Integer days from import date when application window closes.

### 2.3 Mentor Profiles (`mentors.csv`)
**Target Table:** `public.mentor_profiles`
```csv
mentor_id,user_id,full_name,current_company,current_title,country,advisory_topics,max_mentees
mentor-kenji-001,user-kenji-001,Kenji Sato,Rakuten Symphony,Staff AI Engineer,Japan,"AI Career Pathways;Transitioning to Industry in Japan;Graduate Studies",3
```

### 2.4 Events & Reunions (`events.csv`)
**Target Table:** `public.events`
```csv
event_id,title,event_type,location,is_virtual,meeting_url,start_days_ahead,duration_hours,max_capacity
event-summit-001,MSGI Annual Global Alumni Summit & Tech Gala,reunion,"Tokyo International Forum",true,https://stream.example.msgi.edu/summit-2026,24,6,500
```

---

## 3. Execution Instructions

### Running in Demo Mode:
```powershell
python scripts/import_synthetic_data.py --mode demo
```

### Running in Live Mode:
```powershell
python scripts/import_synthetic_data.py --mode live --dir /path/to/approved_institutional_csvs
```

All malformed or unverified rows are rejected and logged with exact line numbers without disclosing sensitive personal data.
