# MSGI ONE — FORMAL SOFTWARE REQUIREMENTS SPECIFICATION (SRS V2.0)

**Document ID:** MSGI-SRS-V2-001  
**Phase:** Phase 1 — Requirements Engineering & Unified System Architecture  
**Date:** November 24, 2026  
**Governing Textbooks:**
- Ian Sommerville, *Software Engineering*, 10th Edition (Requirements engineering, functional/non-functional classification, dependability, security engineering).
- Roger S. Pressman & Bruce R. Maxim, *Software Engineering: A Practitioner's Approach*, 9th Edition (Requirements modeling, scenario-based and class-based specification).
- Robert C. Martin, *Clean Architecture* (Use-case boundaries, Dependency Rule).
- Stuart Russell & Peter Norvig, *Artificial Intelligence: A Modern Approach*, 4th Edition (Rational agent specification, PEAS framing).
*(Note: Exact textbook chapter/page pinpoints require direct physical/digital edition lookup and are not fabricated per Directive Section D11.)*

---

## 1. Existing Module Forensic Classification (Phase 1 Requirement 1)

| Module / Capability | Current Repo State | Classification | Target Phase | Notes |
| :--- | :--- | :--- | :---: | :--- |
| Identity & JWT Auth (`core/security.py`, `core/dependencies.py`, `routers/auth.py`, `routers/users.py`) | HS256/RS256/ES256 JWT decode, `/auth/bootstrap`, `/me` aliases | **Partial / Security Fix Needed** | P3 | Fix unverified fallback on RS256/ES256 when JWKS fails; add server-side `user_roles` lookup, session revocation, and shared `PermissionChecker`. |
| Database Schema & ORM (`supabase/migrations/*`, `src/db/models/*`) | 43 DB tables (38 app + 5 LangGraph checkpoints), 10 async repositories | **Implemented (Needs Extension)** | P2 | Add 17 enterprise tables (scheduling, messaging, rooms, AI vault/ledger, push tokens, outbox, idempotency) + DB overlap protection. |
| Alumni Discovery (`alumni_service.py`, `semantic_search_service.py`) | Directory search, privacy masking, 1536-dim pgvector | **Implemented (Needs Filter Expansion)** | P4 | Expand filters (batch, department, title, mentorship availability) & DB-backed persistence. |
| Mentorship (`mentor_service.py`, `routers/mentors.py`) | Mentor search, score, requests, capacity checks | **Partial** | P4–P5 | Integrate alumni request centre actions (clarification, counter-proposals) and link to scheduling engine. |
| Meeting Scheduling | Not implemented | **Missing** | P5 | Add `alumni_availability`, `meeting_requests`, `meeting_slots`, `meetings`, exclusion constraints, state machines, calendar export. |
| Real-Time 1-on-1 Messaging | Not implemented | **Missing** | P6 | Add FastAPI WebSocket `/ws/chat`, Redis Pub/Sub fan-out, PostgreSQL durable messages, attachments, block/report, cursor recovery. |
| Audio/Video Meetings & Screen Share | Not implemented | **Missing** | P7 | Evaluate & integrate LiveKit SFU (`livekit-api`, `@livekit/react-native`), token-gated rooms, waiting room, webhooks, screen sharing. |
| CareerBridge (`jobs_service.py`, `routers/jobs.py`) | Job search, skill overlap, applications | **Implemented** | P4, P9 | Preserve contracts; connect to FlashList & TanStack Query in P9. |
| Learning & Communities (`learning_service.py`, `community_service.py`) | Course catalog, enrollments, communities, memberships | **Implemented** | P4, P9 | Modularize mobile presentation into domain components. |
| Events & Global Connect (`events_service.py`, `global_service.py`) | Events capacity, registration, chapters, geo aggregation | **Implemented** | P4, P9 | Preserve contracts & frozen APK compatibility. |
| Institutional Admin (`admin_service.py`, `routers/admin.py`) | Verification queue, audit logs, summary | **Partial** | P3–P4, P8 | Add role management, reports/moderation, announcements, AI provider vault UI, operational status. |
| Agentic AI Platform (`src/ai/*`, `routers/ai.py`) | LangGraph StateGraph, Rule 15 HITL, Gemini provider, RAG grounding | **Partial (Needs Multi-Provider + Streaming)** | P8 | Add encrypted `ai_provider_configs` (Gemini/OpenAI/Claude/DeepSeek), SSE `/ai/chat/stream`, expanded tools & evals. |
| Mobile Client (`apps/mobile`) | Expo SDK 52, RN 0.76.5, 1,446-line `index.tsx` monolith | **Requires Refactoring** | P4, P9 | Decompose `index.tsx` (P4); integrate TanStack Query, FlashList, biometrics, push, offline sync (P9). |

---

## 2. Functional Requirements (FR)

### 2.1 Authentication, Identity & Access Control (`FR-AUTH`)
- **FR-AUTH-01:** Students, alumni, faculty, recruiters, and admins authenticate via unified Supabase Auth credentials; the backend cryptographically verifies JWT signature (`HS256`/`RS256`/`ES256`), `exp`, `aud`, and `iss` (when configured), strictly rejecting `alg=none` and unverified signatures.
- **FR-AUTH-02:** User identity (`sub`) and roles are resolved strictly server-side via `public.users` and `public.user_roles`; client-supplied `user_id` or `role` fields are never trusted for privilege grants.
- **FR-AUTH-03:** Student onboarding captures legal name, department, roll/enrollment metadata, and career interests without fabricating data (`is_profile_complete` gating).
- **FR-AUTH-04:** Alumni registration defaults base access to least-privilege until institutional verification (`verification_requests` reviewed by an authenticated `admin`) approves graduation year, degree, and major (`pending` -> `approved` / `rejected`).
- **FR-AUTH-05:** Administrators authenticate with explicit `admin` role permissions; privileged actions (verification decisions, role grants, AI key management, moderation) emit immutable `admin_audit_logs` / `audit_logs` entries.
- **FR-AUTH-06:** Session revocation, password recovery, and GDPR/DPDP account deletion (`DELETE /api/v1/users/{id}`) scrub PII while preserving anonymized referential integrity.

### 2.2 Alumni Discovery (`FR-ALUMNI`)
- **FR-ALUMNI-01:** Authenticated users search verified alumni (`verified_only` default true) by free-text query, graduation batch/year, department/major, organization/company, job title, industry, country/city, skills, and mentorship availability (`mentor_opt_in`).
- **FR-ALUMNI-02:** FERPA/GDPR privacy masking hides personal emails, phone numbers, CGPA, and exact residential coordinates from directory responses; profiles with `visibility = 'private'` or `is_profile_public = false` are excluded from discovery.
- **FR-ALUMNI-03:** Semantic alumni discovery uses 1536-dimensional L2-normalized pgvector embeddings without mixing incompatible embedding spaces.

### 2.3 Mentorship (`FR-MENTOR`)
- **FR-MENTOR-01:** Students view ranked mentors with available capacity (`current_active_mentees < max_active_mentees`) and submit mentorship requests with topic, career goal, and optional message.
- **FR-MENTOR-02:** Alumni mentors review incoming student requests in the Request Centre and transition status (`pending` -> `accepted` / `rejected` / `completed` / `cancelled`) or request clarification.
- **FR-MENTOR-03:** Duplicate active pending requests from the same student to the same mentor are prevented.

### 2.4 Meeting Scheduling (`FR-MEETING`)
- **FR-MEETING-01:** Verified alumni configure recurring weekly availability windows (`alumni_availability`), IANA timezone, slot duration, buffer minutes, and date-specific exceptions.
- **FR-MEETING-02:** Students select a verified alumni profile and propose up to 3 candidate UTC time slots with meeting title, purpose/description, and duration (`PENDING`).
- **FR-MEETING-03:** Alumni can accept one proposed slot (atomically creating a `SCHEDULED` meeting), decline with optional reason (`DECLINED`), or propose alternative slots (`COUNTER_PROPOSED`).
- **FR-MEETING-04:** Students confirm a counter-proposed slot to finalize booking; invalid state transitions are rejected (`409 Conflict` / `422`).
- **FR-MEETING-05:** Database-level exclusion constraints (`EXCLUDE USING gist`) and transactional locking prevent overlapping confirmed meetings for the same alumnus or participant under concurrent load; idempotency keys prevent duplicate submissions.
- **FR-MEETING-06:** Supports meeting calendar views, iCalendar (`.ics`) export, rescheduling (explicit replacement linkage), cancellation, reminders, no-show marking, and post-meeting feedback.

### 2.5 Real-Time Messaging (`FR-CHAT`)
- **FR-CHAT-01:** Authorized users engage in 1-on-1 private conversations persisted durably in PostgreSQL (`conversations`, `conversation_participants`, `messages`, `message_attachments`).
- **FR-CHAT-02:** FastAPI WebSocket `/ws/chat` delivers versioned events (`connection.ready`, `message.send`, `message.accepted`, `message.created`, `message.delivered`, `message.read`, `typing.started`, `typing.stopped`, `presence.changed`, `conversation.updated`, `connection.error`).
- **FR-CHAT-03:** Redis Pub/Sub fans out events across API workers without acting as durable storage; messages are persisted in PostgreSQL before durable acknowledgement.
- **FR-CHAT-04:** Cursor-based recovery fetches missed messages upon reconnection; client-generated idempotency keys deduplicate retries.
- **FR-CHAT-05:** Users can block (`user_blocks`) or report (`user_reports`) other users; blocked users cannot initiate messages or read blocked presence/receipts. Attachments undergo size, MIME/magic-byte, and security validation.

### 2.6 Audio, Video & Screen Sharing (`FR-RTC`)
- **FR-RTC-01:** Confirmed meetings (`SCHEDULED` / `IN_PROGRESS`) allocate a LiveKit SFU room (`meeting_rooms`) and track participants (`meeting_participants`).
- **FR-RTC-02:** Only authorized participants within the permitted joining window (not blocked, meeting not cancelled) receive short-lived signed LiveKit join tokens.
- **FR-RTC-03:** Mobile UI provides pre-join lobby (camera/mic preview), mute/unmute, camera toggle, speaker/Bluetooth routing, participant grid, active speaker view, raise hand, in-meeting text chat, waiting room admission/removal (host controls), network quality indicator, and screen sharing (subject to native SDK/build verification).
- **FR-RTC-04:** Signed LiveKit webhooks are cryptographically verified and deduplicated; meetings are never recorded by default.

### 2.7 Career, Learning & Events (`FR-CAREER`, `FR-LEARN`, `FR-EVENTS`)
- **FR-CAREER-01:** Students browse verified jobs/internships with deterministic skill-overlap analysis and submit deduplicated applications; alumni/recruiters/admins post jobs.
- **FR-LEARN-01:** Students enroll in learning resources and track milestone progress (0–100%).
- **FR-EVENTS-01:** Users view institutional events, register within atomic capacity bounds, receive ticket codes, and cancel registrations.

### 2.8 Administration (`FR-ADMIN`)
- **FR-ADMIN-01:** Admins review verification queues, assign/revoke roles, moderate user reports, publish institutional announcements, manage events, inspect audit logs, and monitor operational health.
- **FR-ADMIN-02:** Admins configure external AI providers (`gemini`, `openai`, `anthropic`, `deepseek`), test connectivity, manage daily/monthly budgets, and view masked key metadata and usage/cost analytics—never retrieving plaintext keys.

### 2.9 Agentic AI & External Providers (`FR-AI`)
- **FR-AI-01:** Bounded LangGraph orchestrator routes user goals across Supervisor and specialized domain capabilities (Alumni, Mentorship, Career, Learning, Meeting Coordination, Communication Assistance, Events/Opportunities, Institutional Knowledge, Admin Assistance).
- **FR-AI-02:** Agents execute only registered, user-authorized backend tools; no unrestricted SQL or arbitrary HTTP access.
- **FR-AI-03:** Consequential actions (sending mentor/meeting requests, confirming/rescheduling/cancelling meetings, sending messages, applying to jobs, event commitments, admin mutations) trigger Rule 15 HITL approval interruptions bound to exact validated arguments, user identity, expiration, and idempotency key.
- **FR-AI-04:** Multi-provider abstraction supports Gemini, OpenAI, Anthropic Claude, and DeepSeek with AES-256-GCM encrypted credentials (`ai_provider_configs`), capability metadata, circuit breakers, budget limits, and usage ledger (`ai_usage_ledger`).
- **FR-AI-05:** `/api/v1/ai/chat/stream` streams real SSE events (`run.started`, `agent.status`, `tool.started`, `tool.completed`, `approval.required`, `response.delta`, `citation`, `usage`, `response.completed`, `run.error`) without leaking internal chain-of-thought or secrets.
- **FR-AI-06:** RAG pipeline enforces provenance, metadata/authorization filtering, citation verification, prompt-injection neutralization, and abstention when evidence is insufficient.

---

## 3. Non-Functional Requirements (NFR)

| ID | Category | Measurable Target / Constraint | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-SEC-01** | Security | Zero unverified JWT acceptance, zero cross-user PII/chat/approval leakage, AES-256-GCM at rest for AI keys, zero client-side AI secrets. | Security regression tests, secret scan |
| **NFR-SEC-02** | Authorization | Complete mediation across REST, WebSocket, LiveKit tokens, and AI tools; server-side role resolution. | Negative RBAC & object-level tests |
| **NFR-PERF-01** | API Latency | p95 < 250 ms for standard REST directory/profile queries under nominal load. | Automated benchmark suite (P10) |
| **NFR-PERF-02** | Messaging Latency | Target < 150 ms message acceptance & WebSocket fan-out under documented benchmark workload (target requiring validation). | WebSocket latency benchmark (P10) |
| **NFR-PERF-03** | AI Streaming | Target < 500 ms time-to-first-token (provider-dependent, measured and reported under test conditions). | Streaming benchmark (P8/P10) |
| **NFR-PERF-04** | Mobile UI | Smooth virtualized scrolling (target 60 FPS on representative device, measured with FlashList). | Device profiling (P9/P10) |
| **NFR-REL-01** | Reliability | Zero double-booking under concurrent scheduling writes; durable message & checkpoint recovery across worker restarts. | Concurrency & restart recovery tests |
| **NFR-REL-02** | Backward Compat | 100% preservation of `/api/v1` and `/api/v1/api/v1` dual-prefix contracts for frozen APK `a95a7169-d48b-4730-bcfd-921500e4b8fae`. | `test_frozen_apk_contracts.py` |
| **NFR-DATA-01** | Data Integrity | 3NF/BCNF schema, explicit FK cascades, 1536-dim pgvector consistency, transactional outbox for durable events. | Schema & constraint integration tests |
| **NFR-ACC-01** | Accessibility | WCAG AA contrast (>= 4.5:1), accessible labels/roles on interactive mobile elements, dark/light theme support. | Mobile UI inspection & component checks |
| **NFR-COST-01** | AI Cost Control | Per-request token bounds, daily/monthly provider budgets, accurate `ai_usage_ledger` accounting. | Cost & budget unit/integration tests |
| **NFR-MAINT-01** | Maintainability | TypeScript `strict: true` (0 errors), modular domain services/repositories, decomposed UI components (< 400 lines per file target). | `tsc --noEmit`, ruff, code review |
