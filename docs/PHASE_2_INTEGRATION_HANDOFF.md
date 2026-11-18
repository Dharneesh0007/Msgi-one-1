# MSGI One — Phase 2 Integration Handoff
**Phase 3 Agentic AI Tool Contracts, Service Signatures & System State Handoff**

**Phase Transition:** Phase 2 (Core Business Modules) ➔ Phase 3 (Agentic AI Command Centre with LangGraph)  
**Date:** 2026-11-18  
**Repository Branch:** `feat/phase-2-business-modules`  
**Compliance Standard:** AGENTS.md (Rule 14: Log AI Actions, Rule 15: Human Approval for Consequential Actions)  

---

## 1. Domain Services Prepared as Phase 3 AI Tools

Phase 3 implements the LangGraph multi-agent ecosystem (Supervisor, Alumni Matchmaker, Career Strategist, Event Coordinator). The domain services implemented in Phase 2 provide clean, typed tool-calling primitives that do NOT expose direct database sessions to the LLM:

### 1. Alumni Discovery Tool
- **Function:** `search_alumni(filters: Dict[str, Any], authenticated_user: AuthenticatedUser) -> Dict[str, Any]`
- **Module:** `services/api/src/services/alumni_service.py`
- **Agent Permission:** Read-only exploration.
- **Privacy Policy:** FERPA-compliant masked attributes only; private opt-out profiles are never returned to the LLM context.

### 2. Opportunity Search & Skill Analysis Tools
- **Function:** `search_jobs(filters: Dict[str, Any], authenticated_user: AuthenticatedUser) -> List[JobResponse]`
- **Function:** `evaluate_skill_overlap(required_skills: List[str], student_skills: List[str]) -> SkillOverlapResult`
- **Module:** `services/api/src/services/jobs_service.py`
- **Agent Permission:** Read-only analysis. The agent can recommend positions and present match percentages, but is strictly prohibited from executing `submit_job_application()` without the student's explicit manual confirmation in the UI.

### 3. Mentor Discovery & Scoring Tools
- **Function:** `search_mentors(filters: Dict[str, Any], authenticated_user: AuthenticatedUser) -> List[MentorProfileResponse]`
- **Function:** `score_mentor_candidates(mentors: List[Dict], student_goal: str) -> List[Dict]`
- **Function:** `prepare_mentor_request(mentor_id: str, goal: str, authenticated_user: AuthenticatedUser) -> Dict[str, Any]`
- **Module:** `services/api/src/services/mentor_service.py`
- **Agent Permission:** Read-only recommendation and draft preparation. The agent returns a structured draft card (`confirmation_required: true`). The mobile client presents a user confirmation sheet before invoking `create_mentor_request()`.

### 4. Event Search & Capacity Tools
- **Function:** `search_events(filters: Dict[str, Any], authenticated_user: AuthenticatedUser) -> List[EventResponse]`
- **Function:** `check_event_capacity(event_id: str) -> Dict[str, Any]`
- **Function:** `prepare_event_registration(event_id: str, authenticated_user: AuthenticatedUser) -> Dict[str, Any]`
- **Module:** `services/api/src/services/events_service.py`
- **Agent Permission:** Read-only. Event registration requires manual confirmation.

### 5. Regional Distribution Tool
- **Function:** `get_aggregated_locations(authenticated_user: AuthenticatedUser) -> List[LocationAggregationItem]`
- **Module:** `services/api/src/services/global_service.py`
- **Agent Permission:** Read-only regional aggregation. Privacy suppression (count >= 3) prevents the LLM from identifying lone alumni in specific regions.

---

## 2. Mandatory Human-in-the-Loop (HITL) Gate Rules

Per **Rule 15 of AGENTS.md**, autonomous agents must never execute consequential actions without explicit human approval:

| Action | Agent Autonomy Level | Execution Path |
|:---|:---:|:---|
| Search Alumni | Fully Autonomous | Directly invokes `search_alumni` |
| Analyze Skill Gaps | Fully Autonomous | Directly invokes `evaluate_skill_overlap` |
| Rank Mentors | Fully Autonomous | Directly invokes `score_mentor_candidates` |
| Draft Mentorship Request | Autonomous Preparation | Invokes `prepare_mentor_request` |
| **Send Mentorship Request** | **Human Approval Required** | Client button triggers `create_mentor_request` |
| **Apply to Job / Internship**| **Human Approval Required** | Client button triggers `submit_job_application` |
| **Register for Event** | **Human Approval Required** | Client button triggers `register_for_event` |
| **Alter Profile / Roles** | **Prohibited for Agent** | Only verified user/admin via REST API |

---

## 3. Database State Preserved for Phase 3

- **Phase 1 Tables:** `users`, `roles`, `user_roles`, `alumni_profiles`, `student_profiles`, `skills`, `user_skills`, `consent_records`.
- **Phase 2 Tables:** `mentor_profiles`, `mentor_requests`, `jobs`, `job_applications`, `events`, `event_registrations`, `alumni_chapters`.
- **Phase 3 Additive Migration Plan:**
  If semantic vector search is enabled, create an additive migration:
  `supabase/migrations/20261120000001_phase_3_vector_embeddings.sql`
  adding an embedding column (`vector(1536)`) and HNSW index to `public.alumni_profiles`. Basic SQL search remains the fallback.
