# MSGI ONE — REQUIREMENTS TRACEABILITY MATRIX (RTM)

**Document ID:** MSGI-RTM-001  
**Last Updated:** November 24, 2026 (Phase 1 Baseline)  

| Req ID | Description Summary | Phase | Design / ADR | Implementation Target | Verification Test Target | Status |
| :--- | :--- | :---: | :--- | :--- | :--- | :---: |
| `FR-AUTH-01` | Cryptographic JWT verification (no `verify_signature=False` fallback) | P3 | `THREAT_MODEL.md` | `core/security.py` | `test_security.py`, `test_phase3_security.py` | IN_PROGRESS |
| `FR-AUTH-02` | Server-side role resolution (`user_roles`), no client role tampering | P3 | `SYSTEM_ARCHITECTURE_V2.md` | `core/dependencies.py`, `services/auth_service.py` | `test_roles.py`, `test_phase3_security.py` | IN_PROGRESS |
| `FR-AUTH-03` | Student onboarding & profile lifecycle | P3–P4 | `API_CONTRACT_V2.md` | `routers/users.py`, `(auth)/complete-profile.tsx` | `test_profiles.py` | IMPLEMENTED |
| `FR-AUTH-04` | Alumni registration & institutional verification workflow | P3–P4 | `API_CONTRACT_V2.md` | `services/verification_service.py`, `routers/verifications.py` | `test_phase3_security.py`, `test_phase4_portals.py` | IN_PROGRESS |
| `FR-AUTH-05` | Admin auth, privileged action auditing | P3–P4 | `THREAT_MODEL.md` | `services/admin_service.py`, `routers/admin.py` | `test_phase_4_modules.py` | IMPLEMENTED |
| `FR-AUTH-06` | Session revocation & GDPR/DPDP erasure | P3 | `API_CONTRACT_V2.md` | `services/auth_service.py`, `routers/users.py` | `test_phase3_security.py` | IN_PROGRESS |
| `FR-ALUMNI-01` | Multi-filter alumni discovery (batch, dept, org, title, industry, location, skills, mentor) | P4 | `API_CONTRACT_V2.md` | `services/alumni_service.py`, `network.tsx` | `test_alumni.py`, `test_phase4_portals.py` | IN_PROGRESS |
| `FR-ALUMNI-02` | FERPA/GDPR privacy masking | P3–P4 | `THREAT_MODEL.md` | `services/alumni_service.py` | `test_phase_5_security_compliance.py` | IMPLEMENTED |
| `FR-ALUMNI-03` | 1536-dim pgvector semantic search & re-index policy | P2, P8 | `SYSTEM_ARCHITECTURE_V2.md` | `services/semantic_search_service.py` | `test_pgvector_search.py` | IMPLEMENTED |
| `FR-MENTOR-01` | Ranked mentor discovery & request submission | P4–P5 | `API_CONTRACT_V2.md` | `services/mentor_service.py` | `test_mentors.py` | IMPLEMENTED |
| `FR-MENTOR-02` | Alumni request centre (accept, decline, clarify) | P4–P5 | `API_CONTRACT_V2.md` | `services/mentor_service.py`, `AlumniDashboard.tsx` | `test_phase4_portals.py` | IN_PROGRESS |
| `FR-MEETING-01..06` | Availability, multi-slot requests, counter-proposals, overlap exclusion, `.ics` | P2, P5 | `ADR-002` | `models/enterprise.py`, P5 `scheduling_service.py` | `test_postgres_integration.py` (schema), P5 tests | SCHEMA_P2 / LOGIC_P5 |
| `FR-CHAT-01..05` | 1-on-1 WS messaging, Redis Pub/Sub, cursor recovery, block/report | P2, P6 | `ADR-003` | `models/enterprise.py`, P6 `ws_chat.py` | `test_postgres_integration.py` (schema), P6 tests | SCHEMA_P2 / LOGIC_P6 |
| `FR-RTC-01..04` | LiveKit SFU rooms, short-lived tokens, webhooks, mobile UI & screen share | P2, P7 | `ADR-004` | `models/enterprise.py`, P7 `rooms.py` | `test_postgres_integration.py` (schema), P7 tests | SCHEMA_P2 / LOGIC_P7 |
| `FR-ADMIN-01..02` | Verification, role mgmt, moderation, announcements, AI vault admin | P4, P8 | `ADR-005` | `routers/admin.py`, `services/admin_service.py` | `test_phase4_portals.py`, P8 tests | IN_PROGRESS |
| `FR-AI-01..06` | Bounded LangGraph, authorized tools, Rule 15 HITL, encrypted multi-provider vault, SSE, RAG | P2, P8 | `AGENTIC_AI_ARCHITECTURE.md`, `ADR-005` | `src/ai/*`, `models/enterprise.py` | `test_ai_command_centre.py`, `test_rag_grounding.py`, P8 tests | BASELINE / EXT_P8 |
| `NFR-REL-02` | Dual-prefix `/api/v1` and `/api/v1/api/v1` frozen APK compatibility | P1–P12 | `API_CONTRACT_V2.md` | `src/main.py` | `test_frozen_apk_contracts.py` | VERIFIED_EXECUTION |
| `NFR-MAINT-01` | Mobile dashboard decomposition & strict TypeScript | P4, P9 | `SYSTEM_ARCHITECTURE_V2.md` | `apps/mobile/src/components/dashboard/*` | `tsc --noEmit`, `expo export` | IN_PROGRESS |
