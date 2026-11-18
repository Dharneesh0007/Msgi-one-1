# MSGI ONE — PHASE 3 AGENTIC AI ARCHITECTURE
**Module:** MSGI AI Command Centre  
**Orchestration Engine:** LangGraph 1.2.22 with StateGraph & MemorySaver Checkpointer  
**Backend:** FastAPI 0.115+, Pydantic v2, Python 3.12  
**Target Environment:** Windows / Android-First Expo SDK 52  
**Engineering Principles:**
- Roger S. Pressman & Bruce R. Maxim: Requirements-driven multi-agent decomposition, process management, and risk containment.
- Eric Evans: Domain-Driven Design (bounded contexts for Alumni, Career, Mentors, Events, and Synthesizer).
- Martin Kleppmann: Fault tolerance, deterministic replayability, and immutable action audit logging.

---

## 1. MULTI-AGENT TOPOLOGY & STATE GRAPH

The MSGI AI Command Centre coordinates specialized domain agents using a hierarchical supervisor pattern built on LangGraph's `StateGraph`.

```
                    ┌─────────────────────────┐
                    │       USER PROMPT       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     SUPERVISOR NODE     │
                    │   Intent Classification │
                    │   Injection & Refusal   │
                    └────────────┬────────────┘
                                 │
       ┌──────────────┬──────────┴───────────┬──────────────┐
       │ (alumni)     │ (mentorship)         │ (career)     │ (events)
       ▼              ▼                      ▼              ▼
┌─────────────┐┌─────────────┐        ┌─────────────┐┌─────────────┐
│ ALUMNI AGENT││ MENTOR MATCH│        │CAREER AGENT ││EVENT COORD  │
│  Directory  ││ Advisory    │        │  Skill-Gap  ││ Capacity    │
│  Discovery  ││ Staging     │        │  Job Search ││ Registration│
└──────┬──────┘└──────┬──────┘        └──────┬──────┘└──────┬──────┘
       │              │                      │              │
       │              │                      ▼              │
       │              │               ┌─────────────┐       │
       │              │               │LEARNING AGT │       │
       │              │               │ Roadmap     │       │
       │              │               └──────┬──────┘       │
       │              │                      │              │
       └──────────────┼──────────────────────┴──────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │    HUMAN-IN-THE-LOOP GATE     │
       │  Rule 15: interrupt() on      │
       │  apply_job, send_mentor_req,  │
       │  register_event mutations     │
       └──────────────┬────────────────┘
                      │ (Status: completed or interrupted)
                      ▼
       ┌───────────────────────────────┐
       │       SYNTHESIZER NODE        │
       │   Evidence Grounding & Brief  │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │     API ENVELOPE / MOBILE     │
       └───────────────────────────────┘
```

---

## 2. CENTRAL STATE MODEL: `CommandCentreState`

All nodes read from and update the shared `CommandCentreState`:

```python
class CommandCentreState(TypedDict, total=False):
    session_id: str
    user_id: str
    user_roles: List[str]
    user_email: str
    prompt: str
    intent: str                      # 'alumni', 'career', 'mentorship', 'events', 'orchestrator', 'rejected'
    target_role: Optional[str]
    extracted_skills: List[str]
    skill_gap: Optional[Dict[str, Any]]
    learning_roadmap: Optional[List[Dict[str, Any]]]
    recommended_mentors: Optional[List[Dict[str, Any]]]
    recommended_jobs: Optional[List[Dict[str, Any]]]
    recommended_events: Optional[List[Dict[str, Any]]]
    alumni_matches: Optional[List[Dict[str, Any]]]
    pending_approval: Optional[Dict[str, Any]]
    approval_status: Optional[str]   # 'pending', 'approved', 'rejected'
    completed_actions: List[Dict[str, Any]]
    action_logs: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    final_summary: str
    status: str                      # 'running', 'interrupted', 'completed', 'failed', 'rejected'
    safety_refusal: Optional[str]
    total_tokens: int
    latency_ms: int
```

---

## 3. DOMAIN AGENTS

1. **Supervisor Node (`supervisor_node`)**:
   - Classifies natural language input into one of five functional paths (`alumni`, `career`, `mentorship`, `events`, `orchestrator`) or `rejected`.
   - Defends against SQL injection (`DROP TABLE`) and system prompt overrides (`GRANT ME ROLE ADMIN`).
   - Rejects non-institutional queries (e.g. poetry, recipes) with safe refusal notes.

2. **Alumni Discovery Agent (`alumni_agent_node`)**:
   - Invokes `search_alumni_network` with industry, country, and verified filters.
   - Enforces user privacy settings (`is_profile_public = true`).

3. **Career Strategist Agent (`career_agent_node`)**:
   - Compares user's baseline skills against `career_role_skills.csv` to calculate match percentages and identify missing skills.
   - Searches active, non-expired jobs via `search_career_opportunities`.
   - Detects consequential job applications and triggers human approval.

4. **Learning Roadmap Agent (`learning_agent_node`)**:
   - Sequences curated courses from `learning_resources.csv` ordered by importance weight and prerequisite dependencies.

5. **Mentor Matching Agent (`mentorship_agent_node`)**:
   - Matches and ranks verified mentors with open capacity.
   - Stages mentorship outreach requests for human approval.

6. **Event Coordinator Agent (`events_agent_node`)**:
   - Queries active summits and webinars.
   - Checks seat availability via `check_event_capacity_tool`.
   - Stages event registrations for human approval.

7. **Synthesizer Node (`synthesizer_node`)**:
   - Aggregates findings into an executive advisory response with explicit institutional evidence grounding.
