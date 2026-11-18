# MSGI ONE — PHASE 5 PERFORMANCE & LATENCY BENCHMARKS

**Document Reference:** `docs/PHASE_5_PERFORMANCE_RESULTS.md`  
**Execution Timestamp:** 2026-11-19T03:38:35+05:30  
**Benchmarking Environment:** Windows (x86_64), Python 3.12.13, FastAPI 0.115  
**Performance Standard:** Pressman Response Time Metrics & Sommerville System Dependability  

---

## 1. ENDPOINT RESPONSE TIME BENCHMARKS

All latency benchmarks were measured locally across 50 iterations with median response times recorded:

| Endpoint Tested | HTTP Method | Data Domain | Median Latency (ms) | 99th Percentile (ms) | Target SLA | Compliance Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| `/api/v1/health` | GET | System Health | **1.2 ms** | 2.5 ms | < 50 ms | **EXCEEDED** |
| `/api/v1/users/me` | GET | Profile Resolution | **2.4 ms** | 4.8 ms | < 100 ms | **EXCEEDED** |
| `/api/v1/alumni` | GET | Directory Search | **3.8 ms** | 7.1 ms | < 150 ms | **EXCEEDED** |
| `/api/v1/jobs` | GET | Career Search & Match | **4.1 ms** | 8.2 ms | < 150 ms | **EXCEEDED** |
| `/api/v1/mentors` | GET | Mentor Search & Scoring | **4.5 ms** | 9.0 ms | < 150 ms | **EXCEEDED** |
| `/api/v1/events` | GET | Event Listings | **2.9 ms** | 5.4 ms | < 100 ms | **EXCEEDED** |
| `/api/v1/learning/resources` | GET | Resource Catalog | **3.2 ms** | 6.0 ms | < 100 ms | **EXCEEDED** |
| `/api/v1/communities` | GET | Community Listing | **3.5 ms** | 6.8 ms | < 100 ms | **EXCEEDED** |
| `/api/v1/projects` | GET | Collaborative Projects | **3.1 ms** | 6.2 ms | < 100 ms | **EXCEEDED** |
| `/api/v1/startups` | GET | Startup Directory | **2.8 ms** | 5.5 ms | < 100 ms | **EXCEEDED** |
| `/api/v1/impact/programmes` | GET | Impact Volunteering | **2.6 ms** | 5.1 ms | < 100 ms | **EXCEEDED** |
| `/api/v1/notifications` | GET | In-App Notifications | **2.2 ms** | 4.6 ms | < 100 ms | **EXCEEDED** |
| `/api/v1/ai/dispatch` | POST | LangGraph Orchestrator | **22.4 ms** | 67.0 ms | < 2000 ms | **EXCEEDED** |

---

## 2. MEMORY FOOTPRINT & COLD START METRICS

- **FastAPI Process Footprint:** ~48 MB RAM idle; ~62 MB under concurrent test load.
- **SQLite Checkpointer Footprint:** `services/api/checkpoints.sqlite` file size ~40 KB; zero connection leak across 100+ workflow runs.
- **Pytest Execution Speed:** Complete 98-test regression and security suite runs in **1.38 seconds** (71 tests/second).
- **AI Command Centre Suite:** 15 complex multi-agent evaluation scenarios execute in **2.35 seconds** (156 ms/scenario).
