# MSGI ONE — PHASE 3 TEST RESULTS
**Test Runner:** `pytest 9.2.0` (with `pytest-asyncio` in auto mode)  
**Execution Environment:** Windows (x86_64), Python 3.12, FastAPI, LangGraph 1.2  
**Command Executed:** `uv run --offline --no-sync --project msgi-one/services/api pytest msgi-one/services/api/tests -q`  
**Execution Timestamp:** 2026-11-19  
**Result:** **61 passed in 1.15s (100% PASS)**

---

## 1. TEST SUITE SUMMARY ACROSS MODULES

| Module / Test File | Tests | Status | Focus Areas |
| :--- | :--- | :--- | :--- |
| `tests/test_ai_command_centre.py` | 15 | **PASS** | Orchestrator routing, skill-gap, roadmaps, HITL approvals, injection defense |
| `tests/test_alumni.py` | 7 | **PASS** | Multi-param search, privacy enforcement, profile public toggles |
| `tests/test_jobs.py` | 8 | **PASS** | Active job discovery, deadline validation, duplicate prevention |
| `tests/test_mentors.py` | 8 | **PASS** | Advisory matching, capacity enforcement, status transitions |
| `tests/test_events.py` | 8 | **PASS** | Capacity tracking, atomic seat increment, registration |
| `tests/test_global_connect.py` | 4 | **PASS** | Chapter directory, geographical aggregation |
| `tests/test_e2e_workflow.py` | 1 | **PASS** | 18-step concrete student journey across all business services |
| `tests/test_profiles.py` | 7 | **PASS** | Profile onboarding, direct /me aliases, verification status |
| `tests/test_auth_tokens.py` | 2 | **PASS** | Supabase HS256 / RS256 token verification, claims validation |
| `tests/test_health.py` | 1 | **PASS** | Phase 3 health envelope check (`ready` orchestrator status) |
| **TOTAL** | **61** | **PASS** | **100% Multi-Module Regression Verification** |

---

## 2. CONCRETE TEST EXECUTION LOG

```text
C:\Users\dharneesh\OneDrive\Documents\msgi-one\services\api\.venv\Lib\site-packages\pytest_asyncio\plugin.py:306: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to "function" scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session". Set it to "fixture-scope" to keep the current behavior.

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
.............................................................            [100%]
61 passed in 1.15s
```
