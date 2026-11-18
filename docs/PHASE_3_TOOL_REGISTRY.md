# MSGI ONE — PHASE 3 TOOL REGISTRY
**Target Specification:** 10 Typed Domain Tools  
**Principles Applied:** Ian Sommerville (Traceability) & Eric Evans (Domain Services)

---

## 1. TOOL INVENTORY & CONTRACTS

| # | Tool Identifier | Scope / Module | Type | Requires Human Approval | Domain Service Invoked |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `search_alumni_network` | Alumni Network | Query | No | `src.services.alumni_service.search_alumni` |
| 2 | `find_recommended_mentors` | MentorMatch | Query | No | `src.services.mentor_service.search_mentors` |
| 3 | `create_mentor_request_tool` | MentorMatch | Mutation | **YES (Rule 15)** | `src.services.mentor_service.create_mentor_request` |
| 4 | `search_career_opportunities` | CareerBridge | Query | No | `src.services.jobs_service.search_jobs` |
| 5 | `submit_job_application_tool` | CareerBridge | Mutation | **YES (Rule 15)** | `src.services.jobs_service.submit_job_application` |
| 6 | `search_institutional_events` | Events & Reunions | Query | No | `src.services.events_service.search_events` |
| 7 | `register_for_event_tool` | Events & Reunions | Mutation | **YES (Rule 15)** | `src.services.events_service.register_for_event` |
| 8 | `check_event_capacity_tool` | Events & Reunions | Query | No | `src.services.events_service.check_event_capacity` |
| 9 | `analyze_career_skill_gap` | Career Intelligence | Compute | No | Deterministic Taxonomy Matrix (`career_role_skills.csv`) |
| 10 | `generate_learning_roadmap` | Career Intelligence | Compute | No | Curated Curriculum Catalog (`learning_resources.csv`) |

---

## 2. TOOL INPUT & OUTPUT SPECIFICATIONS

### Tool 1: `search_alumni_network`
- **Inputs:** `query?: str`, `industry?: str`, `country?: str`, `authenticated_user: AuthenticatedUser`
- **Outputs:** `Dict[str, Any]` with `items: List[AlumniDirectoryItem]`, `total: int`
- **Error Codes:** `UNAUTHENTICATED (401)`

### Tool 2: `find_recommended_mentors`
- **Inputs:** `student_goal?: str`, `topic?: str`, `country?: str`, `authenticated_user: AuthenticatedUser`
- **Outputs:** `List[MentorProfileResponse]`
- **Ranking Criteria:** Matches advisory topic, active capacity, country affinity.

### Tool 3: `create_mentor_request_tool`
- **Inputs:** `mentor_user_id: str`, `topic: str`, `message: str`, `authenticated_user: AuthenticatedUser`
- **Outputs:** `MentorRequestResponse`
- **Constraints:** Enforces `student_id != mentor_user_id` (400), unique pending request constraint (409), capacity limit (400).

### Tool 4: `search_career_opportunities`
- **Inputs:** `keyword?: str`, `opportunity_type?: str`, `country?: str`, `authenticated_user: AuthenticatedUser`
- **Outputs:** `List[JobResponse]`
- **Constraints:** Excludes expired listings and inactive postings.

### Tool 5: `submit_job_application_tool`
- **Inputs:** `job_id: str`, `cover_note: str`, `authenticated_user: AuthenticatedUser`
- **Outputs:** `JobApplicationResponse`
- **Constraints:** Rejects duplicate applications with `DUPLICATE_APPLICATION (409)`.

### Tool 6: `search_institutional_events`
- **Inputs:** `topic?: str`, `event_type?: str`, `country?: str`, `authenticated_user: AuthenticatedUser`
- **Outputs:** `List[EventResponse]`

### Tool 7: `register_for_event_tool`
- **Inputs:** `event_id: str`, `authenticated_user: AuthenticatedUser`
- **Outputs:** `EventRegistrationResponse`
- **Constraints:** Atomic seat check (`current_registrations < max_capacity`), duplicate prevention (`DUPLICATE_REGISTRATION (409)`).

### Tool 8: `check_event_capacity_tool`
- **Inputs:** `event_id: str`
- **Outputs:** `Dict[str, Any]` with `available_seats: int`, `is_at_capacity: bool`

### Tool 9: `analyze_career_skill_gap`
- **Inputs:** `target_role: str`, `current_skills: List[str]`, `authenticated_user: AuthenticatedUser`
- **Outputs:**
  ```json
  {
    "target_role": "AI Engineer",
    "match_percentage": 20.0,
    "covered_skills": [...],
    "missing_skills": [...],
    "missing_skills_count": 5
  }
  ```

### Tool 10: `generate_learning_roadmap`
- **Inputs:** `missing_skills: List[str]`, `authenticated_user: AuthenticatedUser`
- **Outputs:** `List[LearningRoadmapStep]` containing sequenced milestones with duration, provider, URL, and difficulty.
