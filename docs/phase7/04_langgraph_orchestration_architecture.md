# MSGI ONE — GATE 7.3 LANGGRAPH ORCHESTRATION ARCHITECTURE
**Document Version:** 1.0.0  
**Phase:** 7 — Intelligent AI Infrastructure and Verified Integration  
**Author:** Principal AI Systems Architect  
**Governance:** MSGI One Executive Engineering Directive v2.0  
**Status:** **SPECIFIED & READY FOR PERSISTENT CHECKPOINT INTEGRATION**  

---

## 1. Executive Summary & Orchestration Topology

This document specifies the LangGraph orchestration architecture for MSGI One's AI Command Centre. In accordance with Stuart Russell & Peter Norvig (*Artificial Intelligence: A Modern Approach*) and Martin Fowler (*Patterns of Enterprise Application Architecture*), the workflow coordinates domain-specific reasoning through a controlled, state-bounded multi-agent topology.

The design strictly preserves the validated seven-node workflow topology, enforces Human-In-The-Loop (HITL) safety gateways under Rule 15, maintains backward compatibility with the frozen Android release (`a95a7169-d48b-4730-bcfd-921500e4b8fae`), and decouples state orchestration from the underlying database persistence layers.

---

## 2. Seven-Node StateGraph Workflow Topology

```mermaid
flowchart TD
    START([START]) --> SupervisorNode["1. Supervisor Node<br/>(Intent Classification & Refusal Gate)"]
    
    SupervisorNode -->|intent == 'rejected'| EndNode([END / Refusal])
    SupervisorNode -->|intent == 'alumni'| AlumniAgent["2. Alumni Discovery Agent"]
    SupervisorNode -->|intent == 'career'| CareerAgent["3. Career Strategist Agent"]
    SupervisorNode -->|intent == 'mentorship'| MentorshipAgent["5. Mentorship Matching Agent"]
    SupervisorNode -->|intent == 'events'| EventsAgent["6. Institutional Events Agent"]
    SupervisorNode -->|intent == 'orchestrator'| CareerAgent
    
    AlumniAgent --> SynthesizerNode["7. Synthesizer & Citation Validator"]
    
    CareerAgent -->|interrupted (Rule 15)| SynthesizerNode
    CareerAgent -->|status == 'running'| LearningAgent["4. Learning Roadmap Agent"]
    
    LearningAgent -->|intent == 'orchestrator'| MentorshipAgent
    LearningAgent -->|intent != 'orchestrator'| SynthesizerNode
    
    MentorshipAgent -->|interrupted (Rule 15)| SynthesizerNode
    MentorshipAgent -->|intent == 'orchestrator'| AlumniAgent
    MentorshipAgent -->|intent != 'orchestrator'| SynthesizerNode
    
    EventsAgent --> SynthesizerNode
    
    SynthesizerNode --> EndNode
```

### 2.1 Node Specifications

1. **`supervisor` (Master Router & Safety Gatekeeper):**
   - Ingests user query and authenticated identity (`AuthenticatedUser`).
   - Classifies intent (`alumni`, `career`, `mentorship`, `events`, `orchestrator`, `rejected`).
   - Evaluates prompt injection and out-of-scope refusals before domain tools are invoked.
   - Detects consequential action triggers (`apply_job`, `send_mentor_request`, `register_event`).

2. **`alumni_agent` (Verified Network Discovery):**
   - Invokes `search_alumni_network` tool.
   - Restricts search to verified alumni (`is_verified = TRUE`, `deleted_at IS NULL`).
   - Enforces FERPA privacy masking on phone numbers and private emails.

3. **`career_agent` (Competency & Opportunity Strategist):**
   - Invokes `analyze_career_skill_gap` and `search_career_opportunities`.
   - Compares student acquired skills against canonical role requirements.
   - If an application is submitted, triggers the **Rule 15 HITL Gateway** (`status = 'interrupted'`).

4. **`learning_agent` (Curriculum & Courseware Sequencing):**
   - Invokes `generate_learning_roadmap`.
   - Sequences curated courses targeting missing skills identified by the career agent.

5. **`mentorship_agent` (Advisory Matching):**
   - Invokes `find_recommended_mentors`.
   - Ranks alumni mentors matching the student's career transition goal and geographic preference.
   - If a mentorship connection request is staged, triggers the **Rule 15 HITL Gateway** (`status = 'interrupted'`).

6. **`events_agent` (Ecosystem Engagement):**
   - Invokes `search_institutional_events` and `check_event_capacity_tool`.
   - Discovers upcoming summits, webinars, galas, and workshops.
   - If an event registration is staged, triggers the **Rule 15 HITL Gateway** (`status = 'interrupted'`).

7. **`synthesizer` (Citation Grounding & Response Assembly):**
   - Stitches multi-agent findings into a cohesive, structured brief.
   - Executes algorithmic citation verification (`verify_source_citations`) against retrieved entity IDs.
   - Compiles final JSON payload matching `AIChatResponse`.

---

## 3. Explicit Typed State Schema (`CommandCentreState`)

The graph state contract guarantees clean privilege boundaries and prevents credential leakage:

```python
class CommandCentreState(TypedDict, total=False):
    # 1. Trusted Authentication & Tenant Context
    session_id: str
    user_id: str
    user_roles: List[str]
    user_email: str
    thread_owner_id: str  # For multi-tenant checkpoint isolation

    # 2. Query & Intent Parsing
    prompt: str
    intent: str  # 'alumni', 'career', 'mentorship', 'events', 'orchestrator', 'rejected'
    target_role: Optional[str]
    extracted_skills: List[str]

    # 3. Domain Output Payloads
    skill_gap: Optional[Dict[str, Any]]
    learning_roadmap: Optional[List[Dict[str, Any]]]
    recommended_mentors: Optional[List[Dict[str, Any]]]
    recommended_jobs: Optional[List[Dict[str, Any]]]
    recommended_events: Optional[List[Dict[str, Any]]]
    alumni_matches: Optional[List[Dict[str, Any]]]

    # 4. Human-In-The-Loop Approval Gates (Rule 15)
    pending_approval: Optional[Dict[str, Any]]
    approval_status: Optional[str]  # 'pending', 'approved', 'rejected'

    # 5. RAG Retrieval & Citation Grounding
    retrieved_docs: Optional[List[Dict[str, Any]]]
    validated_citations: List[str]

    # 6. Observability, Telemetry & Status
    status: str  # 'running', 'interrupted', 'completed', 'failed', 'rejected'
    safety_refusal: Optional[str]
    error: Optional[str]
    total_tokens: int
    latency_ms: int
    final_summary: str
    evidence: List[Dict[str, Any]]
    action_logs: List[Dict[str, Any]]
```

---

## 4. Rule 15 Human-In-The-Loop (HITL) Approval Gate

Consequential mutations that modify institutional records or dispatch real-world communications **must never** execute autonomously:

```
[Agent Detects Consequential Intent]
              |
              v
[StateGraph Sets status = 'interrupted']
              |
              v
[Approval Staged in public.approval_requests]
              |
              v
[Response Returned to Mobile: status='interrupted', pending_approval={...}]
              |
       (Human Reviews Action in App)
              |
              +-------------------------------+
              |                               |
              v                               v
       [Human Approves]               [Human Rejects]
              |                               |
              v                               v
    [Action Service Executes]        [Action Discarded]
```

### Supported Consequential Actions:
1. `apply_job`: Submitting a formal job application on behalf of a student.
2. `send_mentor_request`: Dispatching an official advisory request to an alumni mentor.
3. `register_event`: Registering a student for an institutional event and decrementing capacity.

---

## 5. Frozen Android Contract Preservation

The frozen Android APK (`a95a7169-d48b-4730-bcfd-921500e4b8fae`) connects via dual-prefix endpoints:
- `POST /api/v1/ai/chat`
- `POST /api/v1/api/v1/ai/chat`
- `POST /api/v1/ai/workflows`

### Envelope Invariant:
```json
{
  "status": "success",
  "data": {
    "session_id": "sess-abc12345",
    "status": "completed",
    "intent": "orchestrator",
    "target_role": "AI Engineer",
    "skill_gap": { ... },
    "learning_roadmap": [ ... ],
    "recommended_mentors": [ ... ],
    "recommended_jobs": [ ... ],
    "recommended_events": [ ... ],
    "alumni_matches": [ ... ],
    "pending_approval": null,
    "final_summary": "Executive career synthesis...",
    "evidence": [ ... ],
    "action_logs": [ ... ],
    "latency_ms": 142,
    "total_tokens": 128
  },
  "timestamp": "2026-11-21T23:10:00Z",
  "meta": {
    "execution_mode": "sandboxed_deterministic",
    "engine": "LangGraph 1.2"
  }
}
```

---

## 6. Implementation Readiness

Gate 7.3 architecture is fully specified. Proceeding to **Gate 7.4 (PostgreSQL Checkpoint Persistence)** to integrate `AsyncPostgresSaver` backed by durable database storage.
