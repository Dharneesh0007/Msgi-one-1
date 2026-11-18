# MSGI One — Comprehensive Test Strategy & Quality Assurance Plan

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** Technical QA Lead & Senior Full-Stack Engineer  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Quality Engineering Foundations

Following **Roger S. Pressman & Bruce R. Maxim** (*Software Engineering: A Practitioner's Approach*, Chapters 17–20: "Software Testing Strategies", "Testing Conventional Applications", and "Testing WebApps"):
1. **No Simulated Verification:** A phase is marked complete only when backed by reproducible, executing automated tests.
2. **Defect Containment:** Defects must be caught at the lowest possible tier in the test pyramid before reaching integration environments.
3. **Deterministic Mocking for AI Workflows:** AI agent testing combines deterministic mock responses (to test graph state transitions, tool parameters, and error recovery without incurring API cost or non-deterministic variance) alongside targeted live model evaluation.

```
       ▲
      / \        Tier 6: Mobile Component & Navigation Tests (Jest / RNTL)
     /   \       Tier 5: Agentic AI Graph & Approval Gate Tests (Pytest / Mock LLM)
    /     \      Tier 4: API Contract & RBAC Integration Tests (FastAPI TestClient)
   /       \     Tier 3: Database & Row-Level Security Tests (pgTAP / Pytest Async)
  /         \    Tier 2: Pydantic Schema & Domain Unit Tests (Pytest)
 /           \   Tier 1: Static Analysis, Typing & Linting (Mypy, Ruff, TypeScript)
 —————————————
```

---

## 2. Test Suites by Tier

### Tier 1: Static Analysis & Type Checking
- **Backend:** `ruff check .` for PEP8 enforcement; `mypy --strict` for Python 3.12 static type safety.
- **Frontend:** `tsc --noEmit` across all Expo Router TypeScript files.
- **Contracts:** Schema synchronization check between Pydantic models and TypeScript interface types.

### Tier 2: Domain Unit Tests (Pytest)
- **Scope:** Pure domain services, business validation rules, entity calculations.
- **Key Test Cases:**
  - `test_graduation_year_validation()`: Verifies boundary checks (`1950 <= year <= current_year + 5`).
  - `test_mentor_capacity_calculation()`: Verifies mentor cannot accept requests when `active_mentees >= max_mentees`.
  - `test_skill_gap_diff_logic()`: Verifies accurate set-difference calculation between candidate skills and job requirements.

### Tier 3: Database & RLS Integration Tests
- **Scope:** Verifies database schema, constraints, and Row-Level Security policies.
- **Key Test Cases:**
  - `test_alumni_profile_privacy_leak()`: Verifies that an unauthenticated or non-connected user receives zero rows for an alumnus with `visibility = 'connections_only'`.
  - `test_student_cgpa_concealment()`: Verifies that general queries cannot read private academic metrics.
  - `test_foreign_key_cascade()`: Verifies that deleting a test user cascades cleanly to child profiles without leaving orphaned records.

### Tier 4: API Contract & RBAC Tests (FastAPI TestClient)
- **Scope:** HTTP status codes, standard JSON envelopes, header validation, role guards.
- **Key Test Cases:**
  - `test_health_endpoint()`: `GET /api/v1/health` returns 200 OK with system status.
  - `test_unauthenticated_request_rejected()`: Endpoints return 401 Unauthenticated when Bearer header is missing.
  - `test_student_cannot_post_job()`: Student role receives 403 Forbidden on `POST /api/v1/jobs`.
  - `test_recruiter_can_post_job()`: Recruiter role receives 201 Created with valid schema.
  - `test_error_envelope_structure()`: Verifies RFC 7807 aligned error format on 422 Unprocessable Entity.

### Tier 5: Agentic AI & Approval Gate Tests
- **Scope:** LangGraph state graph routing, tool invocation, checkpoint persistence, and interruption resumption.
- **Key Test Cases:**
  - `test_e2e_career_roadmap_graph()`: Runs the 15-step primary integration scenario using a deterministic mock LLM; validates that all sub-agent steps complete in topological order.
  - `test_approval_gate_interruption()`: Verifies that when `draft_mentorship_request` is invoked, the graph enters `AWAITING_APPROVAL`, saves state to `agent_runs`, and does not send the request until approved.
  - `test_approval_decision_resumption()`: Submitting `decision: "approved"` successfully resumes the graph and completes the workflow.
  - `test_agent_max_step_guardrail()`: Verifies graph aborts gracefully if step limit is exceeded.

### Tier 6: Mobile UI & Navigation Smoke Tests
- **Scope:** React Native component rendering, loading skeletons, error states, and role navigation.
- **Key Test Cases:**
  - `test_student_tab_navigation()`: Verifies student persona displays Career, Mentors, and Learning tabs.
  - `test_error_state_retry_button()`: Verifies network failure displays user-friendly error card with functional retry trigger.

---

## 3. Automated Test Execution Commands

```bash
# 1. Run backend unit and integration test suite
cd services/api
uv run pytest tests/ -v --cov=src

# 2. Run Python type checking
uv run mypy src/ --strict

# 3. Run mobile client type checking
cd ../../apps/mobile
npx tsc --noEmit

# 4. Run mobile Jest unit tests
npm test -- --watchAll=false
```

---

## 4. Phase Acceptance Gate Policy

Every subsequent phase (Phase 1 through Phase 5) must satisfy this mandatory QA gate:
1. **Zero Failing Tests:** All unit and integration tests must pass with 100% success.
2. **Contract Consistency:** No endpoint may deviate from `docs/API_CONTRACT.md`.
3. **Database Integrity:** Migrations must apply cleanly (`alembic upgrade head`) and roll back cleanly (`alembic downgrade -1`).
4. **Evidence-Based Reporting:** Phase completion reports must include terminal execution logs verifying test passage.
