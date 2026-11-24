# MSGI ONE — INTERNATIONAL TEXTBOOK TRACEABILITY MATRIX

**Document ID:** MSGI-TTM-001  
**Compliance Policy (Directive Section D11):** Every architecture decision traces to its governing textbook, concept, implementation, and tests. Exact chapter/page numbers and verbatim quotations are omitted unless directly verified from an accessible source copy (marked `SOURCE_PINPOINT_REQUIRES_BOOK_VERIFICATION` where appropriate).

---

## 1. Governing Textbook Canon

| Code | Author(s) | Title & Edition | Core Governed Domains |
| :---: | :--- | :--- | :--- |
| **TB-SOM** | Ian Sommerville | *Software Engineering*, 10th Ed. | Requirements engineering, dependable architecture, security engineering, V-model testing, software evolution. |
| **TB-PM** | Roger S. Pressman & Bruce R. Maxim | *Software Engineering: A Practitioner's Approach*, 9th Ed. | Process models, SRS modeling, component cohesion, UI design, QA & verification. |
| **TB-RCM** | Robert C. Martin | *Clean Architecture* | Dependency Rule, SOLID principles, use-case boundaries, interface adapters, component coupling. |
| **TB-EN** | Ramez Elmasri & Shamkant B. Navathe | *Fundamentals of Database Systems*, 7th Ed. | ER modeling, 3NF/BCNF normalization, integrity constraints, transactions, concurrency control, indexing. |
| **TB-MK** | Martin Kleppmann | *Designing Data-Intensive Applications* (repo baseline edition) | Storage & retrieval, transactions & isolation, distributed failure modes, transactional outbox, Pub/Sub vs durable logs. |
| **TB-KR** | James F. Kurose & Keith W. Ross | *Computer Networking: A Top-Down Approach*, 8th Ed. | Application/transport protocols, HTTP/WebSockets, multimedia networking, network security, latency/congestion. |
| **TB-SGG** | Abraham Silberschatz, Peter B. Galvin & Greg Gagne | *Operating System Concepts*, 10th Ed. | Concurrency, synchronization, resource management, deadlock prevention, scheduling. |
| **TB-WRTC** | *WebRTC for the Curious* | *WebRTC for the Curious* | Signaling, SDP negotiation, ICE/STUN/TURN, RTP/RTCP, DTLS/SRTP, SFU media forwarding. |
| **TB-CH-ML** | Chip Huyen | *Designing Machine Learning Systems* | End-to-end ML design, data quality, evaluation, monitoring, production reliability. |
| **TB-CH-AI** | Chip Huyen | *AI Engineering* | Foundation-model apps, RAG, agent architecture, prompt engineering, tool integration, evaluation, guardrails. |
| **TB-RN** | Stuart Russell & Peter Norvig | *Artificial Intelligence: A Modern Approach*, 4th Ed. | Intelligent/rational agents, planning, knowledge representation, uncertainty, multi-agent coordination. |

---

## 2. Traceability Matrix

| Req ID | Phase | Textbook | Verified Concept (Pinpoint Status) | Architectural Decision | Implementation Files | Verification Tests | Known Limitations |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-ALL`, `NFR-ALL` | P1 | **TB-SOM**, **TB-PM** | Formal SRS, requirements classification, traceability matrices (*pinpoint: requires source verification*) | Author formal SRS V2, RTM, Threat Model, and ADRs prior to schema/code extension | `docs/architecture/SRS_FORMAL_SPECIFICATION.md`, `REQUIREMENTS_TRACEABILITY_MATRIX.md` | Baseline pytest + doc cross-check | Textbook chapter/page numbers not fabricated |
| `NFR-MAINT-01` | P1–P4 | **TB-RCM** | Dependency Rule, Single Responsibility Principle, Interface Adapters (*pinpoint: requires source verification*) | Retain FastAPI modular monolith; keep domain rules out of routers; decompose `index.tsx` | `services/api/src/services/*`, `services/api/src/repositories/*`, `apps/mobile/src/components/dashboard/*` | `test_postgres_integration.py`, `tsc --noEmit` | Some legacy P0–P4 services still hold in-memory dev stores alongside DB repos |
| `NFR-DATA-01`, `FR-MEETING-05` | P2, P5 | **TB-EN**, **TB-MK** | 3NF normalization, integrity constraints, isolation, transactional outbox (*pinpoint: requires source verification*) | Add 17 enterprise tables in `20261125000001_enterprise_ecosystem.sql`; GIST exclusion constraint on overlapping meetings; `outbox_events` & `idempotency_keys` | `supabase/migrations/20261125000001_enterprise_ecosystem.sql`, `services/api/src/db/models/*`, `services/api/src/repositories/*` | `test_postgres_integration.py`, `test_enterprise_schema.py` | Remote DDL execution gated on explicit owner approval; SQLite tests emulate exclusion via app lock + query |
| `FR-AUTH-*`, `NFR-SEC-*` | P3 | **TB-SOM**, **TB-PM**, **TB-RCM** | Complete mediation, least privilege, trust boundaries (*pinpoint: requires source verification*) | Remove unverified RS256/ES256 fallback; server-side role resolution; shared `PermissionChecker`; session revocation; log redaction | `services/api/src/core/security.py`, `services/api/src/core/dependencies.py`, `services/api/src/core/permissions.py`, `services/api/src/services/auth_service.py` | `test_security.py`, `test_postgres_authorization.py`, `test_phase3_security.py` | Remote `postgres` runtime role remains `BYPASSRLS`; local least-privilege migration prepared |
| `FR-ALUMNI-*`, `FR-ADMIN-*` | P4 | **TB-PM**, **TB-RCM** | Role-specific presentation, separation of concerns (*pinpoint: requires source verification*) | Separate Student, Alumni, Admin portal views & hooks; unified domain contracts | `apps/mobile/src/components/dashboard/*`, `apps/mobile/src/app/(tabs)/*`, `services/api/src/routers/*` | `tsc --noEmit`, `expo export`, backend portal tests | Device UI visual test requires connected Android device/emulator |
| `FR-CHAT-*`, `NFR-PERF-02` | P6 | **TB-KR**, **TB-MK** | WebSocket transport, durable DB before ack, Redis Pub/Sub fan-out (*pinpoint: requires source verification*) | PostgreSQL authoritative store; Redis Pub/Sub fan-out; cursor recovery; block/report enforcement | Planned P6 (`services/api/src/routers/ws_chat.py`, `services/api/src/services/messaging_service.py`) | Planned P6/P10 WS & restart tests | Implemented in Checkpoint B |
| `FR-RTC-*` | P7 | **TB-KR**, **TB-WRTC**, **TB-SGG** | SFU topology, ICE/STUN/TURN, DTLS/SRTP, token-gated room admission (*pinpoint: requires source verification*) | LiveKit SFU with short-lived backend tokens, signed webhook dedupe, Expo SDK 52 compatibility guard | Planned P7 (`services/api/src/routers/rooms.py`, `services/api/src/services/room_service.py`) | Planned P7/P10 room auth & native tests | Hardware A/V & screen share require native device builds |
| `FR-AI-*`, `NFR-COST-01` | P8 | **TB-CH-ML**, **TB-CH-AI**, **TB-RN**, **TB-MK** | Rational tool-using agents, RAG grounding, evaluation, provider circuit breakers (*pinpoint: requires source verification*) | Bounded LangGraph + Rule 15 HITL + AES-256-GCM provider vault + SSE `/ai/chat/stream` | `services/api/src/ai/*`, planned P8 vault & streaming extensions | `test_ai_command_centre.py`, `test_ai_security_and_costs.py`, `test_rag_grounding.py` | Live external provider tests gated on authorized API keys |
