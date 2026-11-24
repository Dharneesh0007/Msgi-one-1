# MSGI One — Phase 10 Integration Test & Benchmark Report

**Status:** VERIFIED_EXECUTION (In-Process FastAPI ASGI, Deterministic AI Mode, Live AES-256-GCM Vault)  
**Test Suite:** `services/api/tests/test_phase10_e2e_and_negative.py`  
**Benchmark Script:** `services/api/scripts/run_benchmarks.py`

---

## 1. End-to-End Integration Scenarios Executed

| Scenario | Description | Outcome |
| :--- | :--- | :--- |
| **Scenario A** | Alumni search -> UTC availability -> Counter-proposal -> Meeting confirmation -> `.ics` export -> Messaging `seq` + read receipt -> Early room block (`403`) -> Host/Participant LiveKit tokens -> Admit -> End -> Feedback | **PASS** |
| **Scenario B** | Candidate verification request -> Non-admin `403` guard -> Admin approval -> Encrypted OpenAI vault key save -> Zero plaintext exposure -> Immutable audit log entry | **PASS** |
| **Scenario C** | Agentic AI scheduling prompt -> `interrupted` Rule 15 approval -> Cross-user `403` block -> Owner approval -> Scheduling request created | **PASS** |
| **Scenario D** | Expo push token registration (`POST /api/v1/devices/push-token`) -> Listing -> Revocation on logout (`DELETE`) + Session JWT revocation (`POST /api/v1/auth/logout` -> `401`) | **PASS** |

---

## 2. Negative Security & Concurrency Matrix

1. **Missing / Invalid / Tampered JWT:** Rejected `401`.
2. **Revoked Logout JWT:** Rejected `401 SESSION_REVOKED`.
3. **Unauthorized Cross-User Conversation Access:** Rejected `403`.
4. **Blocked Pair Messaging:** Rejected `403`.
5. **Concurrent Slot Double-Booking Race (`threading.Barrier`):** Strictly one `200`, one `409 Conflict`.
6. **Unauthorized Non-Participant LiveKit Room Access:** Rejected `403`.
7. **Non-Host Waiting Room Admission:** Rejected `403`.
8. **Early Join Window Enforcement (Outside Meeting Window):** Rejected `403`.
9. **Approval Payload Tampering (`args_hash` Mismatch):** Rejected `409 APPROVAL_TAMPERED`.
10. **Expired Approval TTL Enforcement:** Rejected `410 APPROVAL_EXPIRED`.
11. **Cross-User Approval Decision Attempt:** Rejected `403 PERMISSION_DENIED`.
12. **Non-Admin Access to AI Vault Control Plane:** Rejected `403`.
13. **Plaintext API Key Redaction & Exclusion:** Verified zero key exposure across create/list/rotate responses.
14. **Prompt Injection & Out-of-Scope Rejection:** `status == "rejected"` enforced before downstream tool execution.
15. **WebSocket Missing / Invalid Token Handshake:** Rejected before connection acceptance.
16. **Dual-Prefix Frozen APK Contract Parity (`/api/v1` and `/api/v1/api/v1`):** Verified `200 OK` parity.

---

## 3. Reproducible Latency Benchmarks (Local In-Process ASGI)

Measured on Windows Python 3.12 (`services/api/scripts/run_benchmarks.py`, offline deterministic mode; does NOT include external WAN RTT to Supabase Postgres or third-party LLMs):

| Operation | Iterations | Min (ms) | Mean (ms) | P50 (ms) | P95 (ms) | Max (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/v1/health` | 25 | 2.78 | 4.64 | 3.29 | 3.98 | 22.81 |
| `GET /api/v1/ready` | 25 | 2.77 | 3.03 | 2.99 | 3.24 | 3.63 |
| `GET /api/v1/alumni?country=Japan` | 25 | 3.09 | 3.69 | 3.34 | 3.50 | 12.57 |
| `GET /api/v1/scheduling/availability/user-kenji-001` | 25 | 3.37 | 6.54 | 4.55 | 6.05 | 50.87 |
| `POST /api/v1/ai/chat` (deterministic orchestration) | 10 | 7.28 | 8.66 | 7.69 | 9.74 | 16.19 |
| AES-256-GCM Vault Encrypt + Decrypt | 50 | 0.01 | 0.02 | 0.01 | 0.01 | 0.89 |
