# MSGI ONE — GATE 7.1 EXISTING AI ARCHITECTURE & CONTRACTS AUDIT
**Document Version:** 1.0.0  
**Phase:** 7 — Intelligent AI Infrastructure and Verified Integration  
**Author:** Principal AI Systems Architect & Independent Technical Auditor  
**Governance:** MSGI One Executive Engineering Directive v2.0  
**Inherited Test Baseline:** 130 passed in 28.59s `[V-EXEC]`  
**Status:** **AUDIT COMPLETE — TARGETS IDENTIFIED FOR PRESERVATION, EXTENSION, AND REPLACEMENT**  

---

## 1. Executive Audit Summary

Before modifying the MSGI One AI subsystem, an exhaustive source code and architectural audit of all existing AI components in `services/api/src/ai/`, `src/routers/ai.py`, `src/schemas/ai.py`, `src/db/models/ai.py`, and `tests/test_ai_command_centre.py` was conducted.

The current subsystem is a deterministic, rule-based prototype constructed during Phase 3 to establish routing topologies and validate Human-In-The-Loop (HITL) approval gateways under Rule 15. While structurally clean and rigorously tested (15 unit tests passing), it exhibits significant architectural gaps:
1. **Model Inference:** Relies entirely on regex/keyword heuristics; no live LLM API is called.
2. **Persistence:** Agent workflow runs and approval decisions are stored in volatile Python dictionaries (`_AGENT_RUNS_STORE`, `_APPROVALS_STORE`) rather than the mapped PostgreSQL audit tables.
3. **Data Access:** Skill gap and learning roadmap tools read static seed CSV files directly from disk instead of querying the relational database.
4. **Vector Search:** The `pgvector` extension and `alumni_profiles.embedding` column are present in PostgreSQL but completely unutilized.
5. **Checkpointing:** State checkpointing defaults to an ephemeral SQLite database or in-memory dictionary.

This audit establishes a precise component inventory, classifies every module for preservation, extension, replacement, or deprecation, and defines the target integration architecture.

---

## 2. Component Inventory & Architectural Analysis

### 2.1 AIProvider Abstraction (`services/api/src/ai/provider.py`) `[V-READ]`
- **Current Role:** Singleton class (`provider = AIProvider()`) that inspects environment variables `GEMINI_API_KEY` and `AI_PROVIDER`.
- **Current Implementation:** Contains a single method `classify_intent_and_entities(prompt: str)` based on regex substring matching.
  - Detects prompt injection keywords (`drop table`, `system override`) -> returns `REFUSE_INJECTION`.
  - Detects out-of-scope keywords (`butterfly`, `poem`, `recipe`) -> returns `REFUSE_OUT_OF_SCOPE`.
  - Detects cross-user authorization violations (`on behalf of`) -> returns `FORBIDDEN_AUTHORIZATION`.
  - Classifies intents into 6 discrete targets (`alumni`, `career`, `mentorship`, `events`, `orchestrator`, `rejected`).
  - Detects consequential actions requiring human approval (`apply_job`, `send_mentor_request`, `register_event`).
- **Audit Assessment:**
  - *Strengths:* Clean separation of concerns; deterministic mode provides a fast, zero-cost, reproducible regression baseline.
  - *Weaknesses:* Synchronous only; lacks live Gemini API invocation; no structured Pydantic output parsing from LLM; cannot handle ambiguous or novel queries.
- **Decision:** **EXTEND.** Preserve the deterministic classification logic as a resilient offline fallback and test harness. Add an asynchronous live Gemini client utilizing the official `google-genai` SDK with typed structured outputs, configurable model IDs, usage telemetry, and safe fallback.

### 2.2 LangGraph Orchestrator & Agents (`services/api/src/ai/graph.py`, `src/ai/agents/`) `[V-READ]`
- **Current Role:** Assembles the StateGraph containing 7 nodes:
  1. `supervisor` (`src/ai/agents/supervisor.py`): Routes query based on intent classification.
  2. `alumni_agent` (`src/ai/agents/alumni.py`): Calls `search_alumni_network` tool.
  3. `career_agent` (`src/ai/agents/career.py`): Calls `analyze_career_skill_gap` and `search_career_opportunities`.
  4. `learning_agent` (`src/ai/agents/learning.py`): Calls `generate_learning_roadmap`.
  5. `mentorship_agent` (`src/ai/agents/mentorship.py`): Calls `find_recommended_mentors`.
  6. `events_agent` (`src/ai/agents/events.py`): Calls `search_institutional_events`.
  7. `synthesizer` (`src/ai/graph.py`): Stitches domain outputs into a structured textual brief.
- **Current Implementation:**
  - Uses `StateGraph(CommandCentreState)`.
  - Graph is compiled globally at module import: `command_centre_graph = build_command_centre_graph()`.
  - Execution entrypoint `run_command_centre(prompt, user, session_id)` is a synchronous wrapper.
  - Checkpointer helper `get_default_checkpointer()` attempts `SqliteSaver` on a local file or falls back to `MemorySaver`.
- **Audit Assessment:**
  - *Strengths:* The node topology aligns with Evans' bounded contexts and correctly models student career progression (Career -> Learning -> Mentorship -> Alumni).
  - *Weaknesses:* Synchronous execution blocks the event loop; checkpointer does not use PostgreSQL; agent run results are written to an in-memory dictionary `_AGENT_RUNS_STORE`.
- **Decision:** **EXTEND.** Maintain the 7-node topology and state contract. Migrate checkpointer to `AsyncPostgresSaver` backed by PostgreSQL. Support asynchronous invocation (`ainvoke`). Persist agent runs to `public.agent_runs` and `public.agent_actions`.

### 2.3 Graph State Contract (`services/api/src/ai/state.py`) `[V-READ]`
- **Current Role:** Defines `CommandCentreState(TypedDict, total=False)`.
- **Fields:**
  - Identity Context: `session_id`, `user_id`, `user_roles`, `user_email`.
  - Intent & Extraction: `prompt`, `intent`, `target_role`, `extracted_skills`.
  - Domain Payloads: `skill_gap`, `learning_roadmap`, `recommended_mentors`, `recommended_jobs`, `recommended_events`, `alumni_matches`.
  - HITL Gate: `pending_approval`, `approval_status`.
  - Telemetry & Synthesis: `completed_actions`, `action_logs`, `evidence`, `final_summary`, `status`, `safety_refusal`, `total_tokens`, `latency_ms`.
- **Audit Assessment:**
  - *Strengths:* Strongly typed, comprehensive, zero credential leakage into state.
  - *Weaknesses:* Lacks explicit fields for RAG context, source document citations, and model provenance.
- **Decision:** **EXTEND.** Add optional fields: `rag_context: Optional[List[Dict[str, Any]]]`, `citations: Optional[List[str]]`, `model_name: Optional[str]`, `thread_owner_id: Optional[str]`.

### 2.4 Agent Tool Registry (`services/api/src/ai/tools.py`) `[V-READ]`
- **Current Role:** Provides 10 tools consumed by agent nodes.
  - Domain service wrappers: `search_alumni_network`, `find_recommended_mentors`, `create_mentor_request_tool`, `search_career_opportunities`, `submit_job_application_tool`, `search_institutional_events`, `register_for_event_tool`, `check_event_capacity_tool`.
  - Seed file processors: `analyze_career_skill_gap`, `generate_learning_roadmap`.
- **Audit Assessment:**
  - *Strengths:* Domain wrappers correctly invoke Phase 2 business services with `AuthenticatedUser` context.
  - *Weaknesses:* Tools 9 and 10 load CSV files (`career_role_skills.csv`, `learning_resources.csv`) from disk via `csv.DictReader` on every invocation instead of querying the mapped database tables `public.career_role_skills` and `public.learning_resources`.
- **Decision:** **EXTEND & MIGRATE.** Connect `analyze_career_skill_gap` and `generate_learning_roadmap` to query the database entities via SQLAlchemy repositories (or fallback to cached seed data if DB is offline). Add vector retrieval tool `semantic_search_alumni_and_jobs`.

### 2.5 Approval Gateway (`services/api/src/ai/approvals.py`) `[V-READ]`
- **Current Role:** Implements Rule 15 Human-In-The-Loop gatekeeper for consequential mutations (`apply_job`, `send_mentor_request`, `register_event`).
- **Current Implementation:**
  - Staged actions are assigned an `idempotency_key` and stored in `_APPROVALS_STORE: Dict[str, ApprovalRequestRecord]`.
  - Helper functions `create_approval_request`, `get_pending_approvals`, `get_approval_by_id`, `decide_approval`.
  - Verifies that only the owning user can approve or reject their own action (cross-user tampering raises HTTP 403).
- **Audit Assessment:**
  - *Strengths:* Fully compliant with Rule 15; robust cross-user authorization tests.
  - *Weaknesses:* Volatile in-memory store; approvals do not survive API server reboots.
- **Decision:** **EXTEND.** Persist approval requests to `public.approval_requests` using the existing mapped SQLAlchemy model while preserving the existing public interface.

### 2.6 AI Router & Schemas (`services/api/src/routers/ai.py`, `src/schemas/ai.py`) `[V-READ]`
- **Current Role:** Exposes 5 REST endpoints conforming to legacy mobile contracts:
  - `POST /api/v1/ai/chat` (StandardEnvelope[AIChatResponse])
  - `POST /api/v1/ai/workflows` (StandardEnvelope[AIChatResponse])
  - `GET  /api/v1/ai/workflows/{session_id}` (StandardEnvelope[dict])
  - `GET  /api/v1/ai/approvals/pending` (StandardEnvelope[List[ApprovalItem]])
  - `POST /api/v1/ai/approvals/{approval_id}/decision` (StandardEnvelope[ApprovalItem])
- **Audit Assessment:**
  - *Strengths:* Strict Pydantic v2 validation; `StandardEnvelope` structure strictly adheres to frozen APK expectations.
  - *Weaknesses:* Workflow status endpoint reads from in-memory `_AGENT_RUNS_STORE`.
- **Decision:** **PRESERVE.** The HTTP endpoints, DTO shapes, and envelope structures are frozen contracts. Backend implementation will be enhanced to query persistent database records while keeping response schemas 100% identical.

### 2.7 Declarative Database Models (`services/api/src/db/models/ai.py`) `[V-READ]`
- **Current Role:** SQLAlchemy 2.0 mapped models for all 6 Phase 3 database tables:
  1. `CareerRoleSkill` (`public.career_role_skills`)
  2. `LearningResource` (`public.learning_resources`)
  3. `StudentSkill` (`public.student_skills`)
  4. `AgentRun` (`public.agent_runs`)
  5. `AgentAction` (`public.agent_actions`)
  6. `ApprovalRequest` (`public.approval_requests`)
- **Audit Assessment:**
  - Fully mapped with typed columns, foreign keys, cascades, and check constraints matching the Supabase migration `20261120000001_phase_3_agent_intelligence.sql`.
- **Decision:** **PRESERVE.** Ready for immediate use by Phase 7 async repositories and checkpointers.

---

## 3. Existing AI Dependency Map

```
                  +-----------------------------------+
                  |      FROZEN ANDROID CLIENT        |
                  |     (Artifact: a95a7169...)       |
                  +-----------------+-----------------+
                                    |
                                    | HTTP (Dual-Prefix: /api/v1 & /api/v1/api/v1)
                                    v
                  +-----------------------------------+
                  |        src/routers/ai.py          |
                  |  - chat_with_command_centre       |
                  |  - trigger_workflow               |
                  |  - list_pending_approvals         |
                  |  - submit_approval_decision       |
                  +-----------------+-----------------+
                                    |
                 +------------------+------------------+
                 |                                     |
                 v                                     v
   +-----------------------------+       +-----------------------------+
   |     src/ai/approvals.py     |       |       src/ai/graph.py       |
   | - create_approval_request   |       | - run_command_centre        |
   | - decide_approval           |       | - StateGraph topology       |
   | - _APPROVALS_STORE (Memory) |       | - _AGENT_RUNS_STORE (Memory)|
   +--------------+--------------+       +--------------+--------------+
                  |                                     |
                  v                                     v
   +-----------------------------+       +-----------------------------+
   |   Domain Mutations (Phase 2)|       |     src/ai/provider.py      |
   | - submit_job_application    |       | - classify_intent_and_...   |
   | - create_mentor_request     |       | - Regex heuristics (Mock)   |
   | - register_for_event        |       +--------------+--------------+
   +-----------------------------+                      |
                                                        v
                                         +-----------------------------+
                                         |     src/ai/agents/*         |
                                         | - supervisor, alumni,       |
                                         |   career, learning, mentors,|
                                         |   events, synthesizer       |
                                         +--------------+--------------+
                                                        |
                                                        v
                                         +-----------------------------+
                                         |      src/ai/tools.py        |
                                         | - 8 domain service wrappers |
                                         | - 2 CSV loaders (Disk)      |
                                         +-----------------------------+
```

---

## 4. Preservation, Extension, and Replacement Matrix

| Component | Current State | Target State in Phase 7 | Classification | Justification |
| :--- | :--- | :--- | :---: | :--- |
| **`AIChatRequest` & `AIChatResponse`** | Pydantic v2 schemas | Unchanged | **PRESERVE** | Frozen Android contract invariant. |
| **`StandardEnvelope[T]`** | Standard response wrapper | Unchanged | **PRESERVE** | Frozen Android contract invariant. |
| **`test_ai_command_centre.py`** | 15 deterministic unit tests | Unchanged (all 15 passing) | **PRESERVE** | Continuous regression baseline for deterministic mode. |
| **`src/db/models/ai.py`** | 6 mapped ORM models | Unchanged | **PRESERVE** | Schema parity with canonical PostgreSQL migrations. |
| **`src/ai/provider.py`** | Synchronous regex classifier | Async `GeminiAIProvider` with fallback to deterministic | **EXTEND** | Introduce official `google-genai` SDK, live Gemini model inference, and structured outputs while keeping offline resilience. |
| **`src/ai/state.py`** | `CommandCentreState` | Add RAG context, citations, model metadata | **EXTEND** | Enable RAG traceability and grounding verification. |
| **`src/ai/graph.py`** | Global compiled graph with in-memory store | Async graph execution, persistent PostgreSQL checkpointer | **EXTEND** | Enable durable multi-turn conversations surviving backend restarts. |
| **`src/ai/tools.py`** | 8 service wrappers + 2 CSV loaders | Migrate CSV tools to DB queries; add pgvector retrieval tool | **EXTEND** | Eliminate file-system dependencies and enable semantic retrieval. |
| **`_AGENT_RUNS_STORE`** | Volatile Python `dict` in memory | Persistent `public.agent_runs` and `agent_actions` | **REPLACE** | Meet Kleppmann audit durability and enterprise observability requirements. |
| **`_APPROVALS_STORE`** | Volatile Python `dict` in memory | Persistent `public.approval_requests` | **REPLACE** | Ensure human approval state survives application restarts. |
| **`get_default_checkpointer()`**| Local SQLite or Memory | `AsyncPostgresSaver` backed by PostgreSQL | **REPLACE** | Establish production-grade multi-turn conversation persistence. |

---

## 5. Architectural Invariants for Phase 7

1. **Deterministic Mode Preserved:** Setting `AI_PROVIDER=deterministic` must continue to run the 15 existing unit tests in milliseconds without requiring external network connectivity or paid API tokens.
2. **Zero In-Memory Silent Fallback in Production:** In `AI_PROVIDER=gemini` mode, if Gemini or PostgreSQL is unreachable, the system must raise explicit, transparent errors rather than silently fabricating responses or storing state in volatile memory.
3. **Application-Layer Authorization Guardrails:** Because the backend connects as `postgres` (`rolbypassrls = True`), all new AI tools, vector queries, and checkpointer operations must explicitly filter on `user_id`, `roles`, and institutional visibility in Python code.
4. **Frozen APK Invariant:** The response envelope and field names of `/api/v1/ai/chat` must not change. New capabilities (citations, RAG metadata, token counts) must be placed in `meta` or optional backwards-compatible fields.

---

## 6. Audit Sign-Off

The existing AI architecture is fully audited and mapped. The proposed transitions preserve 100% backward compatibility and existing test integrity while engineering a genuinely intelligent, persistent, and secure AI subsystem.

Proceeding to **Gate 7.2: Live Gemini Model Provider Design and Implementation**.
