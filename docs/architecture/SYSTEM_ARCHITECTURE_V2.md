# MSGI ONE — UNIFIED SYSTEM ARCHITECTURE V2.0

**Document ID:** MSGI-ARCH-V2-001  
**Phase:** Phase 1 — Requirements Engineering & Unified System Architecture  
**Date:** November 24, 2026  
**Governing Textbooks:**
- Ian Sommerville, *Software Engineering*, 10th Ed. (Architectural views, layered & repository patterns, dependability).
- Roger S. Pressman & Bruce R. Maxim, *Software Engineering: A Practitioner's Approach*, 9th Ed. (Architectural design, component cohesion).
- Robert C. Martin, *Clean Architecture* (Dependency Rule, SOLID, boundary interfaces).
- Martin Kleppmann, *Designing Data-Intensive Applications* (Replication, transactions, outbox, Pub/Sub vs durable logs).

---

## 1. Architectural Style: Modular Monolith (7-Layer Clean Architecture)

MSGI One retains the **FastAPI Modular Monolith** backed by **PostgreSQL 17 (Supabase) + pgvector**, **Redis** (ephemeral Pub/Sub, presence, rate-limit counters), **LiveKit SFU** (WebRTC media forwarding), and **LangGraph** (bounded agentic AI orchestration).

All entrypoints — Mobile REST, WebSockets (`/ws/chat`), LiveKit room authorization, SSE AI streaming (`/api/v1/ai/chat/stream`), and AI Agent Tools — converge on the same authorized **Application Use-Case & Domain Service Layer** so business rules and authorization checks are never duplicated or bypassed.

---

## 2. C4 & Architectural Diagrams

### 2.1 System Context Diagram
```mermaid
flowchart LR
    Student["Student Mobile User"] -->|HTTPS / WSS / WebRTC| MSGI["MSGI One Platform"]
    Alumni["Alumni Mobile User"] -->|HTTPS / WSS / WebRTC| MSGI
    Admin["Institutional Admin"] -->|HTTPS / WSS| MSGI

    MSGI -->|Auth & JWKS| SupabaseAuth["Supabase Auth"]
    MSGI -->|ACID SQL & pgvector| Postgres["PostgreSQL 17 + pgvector"]
    MSGI -->|Pub/Sub & Ephemeral State| Redis["Redis"]
    MSGI -->|SFU Room Tokens & Webhooks| LiveKit["LiveKit WebRTC SFU"]
    MSGI -->|Push Delivery| ExpoPush["Expo / FCM / APNs"]
    MSGI -->|Encrypted Adapter Calls| AIProviders["External AI Providers (Gemini / OpenAI / Claude / DeepSeek)"]
```

### 2.2 Container Architecture Diagram
```mermaid
flowchart TB
    subgraph Mobile ["Mobile Client (Expo SDK 52 / RN 0.76.5)"]
        Nav["Expo Router v4 (Student / Alumni / Admin Portals)"]
        RQ["TanStack Query + Offline Queue + SecureStore"]
        WSClient["WebSocket Chat Client"]
        LKClient["LiveKit React Native Client"]
    end

    subgraph Backend ["FastAPI Modular Monolith (Python 3.12)"]
        DualPfx["Dual-Prefix Middleware (/api/v1 & /api/v1/api/v1)"]
        AuthGW["Auth & PermissionChecker (JWT + Server Roles)"]
        RestAPI["Domain REST Routers"]
        WSRouter["WebSocket Router (/ws/chat)"]
        SSE["AI SSE Router (/api/v1/ai/chat/stream)"]
        Services["Domain Services & Outbox"]
        Repos["Async SQLAlchemy 2.0 Repositories"]
        LangGraph["LangGraph Orchestrator + HITL Gate + Provider Vault"]
    end

    Mobile --> DualPfx
    Mobile --> WSRouter
    Mobile --> LKClient
    DualPfx --> AuthGW --> RestAPI --> Services --> Repos
    AuthGW --> SSE --> LangGraph --> Services
    AuthGW --> WSRouter --> Services
    Repos --> PG[("PostgreSQL 17 + pgvector")]
    WSRouter <--> Redis[("Redis Pub/Sub")]
    Services --> LiveKit["LiveKit SFU API"]
    LangGraph --> AIProviders["Gemini / OpenAI / Anthropic / DeepSeek"]
```

### 2.3 Component Architecture (Clean Architecture Dependency Rule)
```mermaid
flowchart LR
    Routers["Routers / WS / SSE Adapters"] --> UseCases["Application Services (Use Cases)"]
    AITools["Agent Tool Registry"] --> UseCases
    UseCases --> Policy["Authorization & PermissionChecker"]
    UseCases --> RepoInt["Repository Interfaces"]
    RepoImpl["Async SQLAlchemy Repositories"] --> RepoInt
    RepoImpl --> ORM["SQLAlchemy 2.0 Models"]
    Providers["AI Provider Adapters & AES-256-GCM Vault"] --> UseCases
```

### 2.4 Deployment Architecture
```mermaid
flowchart TB
    MobileApp["Android APK / iOS IPA (EAS Build)"] -->|TLS 1.3| LB["HTTPS / WSS Ingress"]
    LB --> API1["FastAPI Worker 1 (Uvicorn)"]
    LB --> API2["FastAPI Worker N (Uvicorn)"]
    API1 & API2 --> PG[("Supabase PostgreSQL 17 + pgvector")]
    API1 & API2 <--> Redis[("Redis (Pub/Sub, Rate Limit, Presence)")]
    API1 & API2 --> LK["LiveKit SFU (Cloud or Self-Hosted)"]
    MobileApp <-->|ICE / DTLS / SRTP| LK
    API1 --> PushWorker["Outbox & Push Notification Worker"]
    PushWorker --> ExpoPush["Expo Push / FCM / APNs"]
```

### 2.5 Extended Entity-Relationship (ER) Overview
```mermaid
erDiagram
    users ||--o{ user_roles : has
    users ||--o| student_profiles : extends
    users ||--o| alumni_profiles : extends
    users ||--o{ alumni_availability : configures
    users ||--o{ meeting_requests : submits_or_receives
    meeting_requests ||--o{ meeting_slots : proposes
    meeting_requests ||--o| meetings : confirms
    meetings ||--o| meeting_rooms : allocates
    meeting_rooms ||--o{ meeting_participants : tracks
    conversations ||--o{ conversation_participants : includes
    conversations ||--o{ messages : stores
    messages ||--o{ message_attachments : attaches
    users ||--o{ user_blocks : blocks
    users ||--o{ user_reports : reports
    users ||--o{ ai_provider_configs : configures
    ai_provider_configs ||--o{ ai_usage_ledger : records
    users ||--o{ push_device_tokens : registers
    outbox_events }o--|| users : references_actor
```

### 2.6 Data-Flow & Trust-Boundary Diagram
```mermaid
flowchart LR
    subgraph TB1 ["Trust Boundary 1: Untrusted Mobile Client"]
        Client["Mobile App (Anon Key + User JWT only)"]
    end
    subgraph TB2 ["Trust Boundary 2: Auth & API Perimeter"]
        JWTVerify["JWT Sig/Exp/Aud/Iss + Revocation Check"]
        RBAC["Server-Side Role & Object Policy"]
    end
    subgraph TB3 ["Trust Boundary 3: Trusted Domain & Data"]
        Services["Domain Services & HITL Gate"]
        Vault["AES-256-GCM Encrypted AI Keys"]
        DB[("PostgreSQL (BYPASSRLS Backend or RLS Runtime Role)")]
    end
    subgraph TB4 ["Trust Boundary 4: External Services"]
        ExtAI["External AI Providers (PII-Sanitized Prompts)"]
        LK["LiveKit SFU (Short-Lived Room JWT)"]
    end

    Client -->|Untrusted Input| TB2
    TB2 -->|Verified Identity + Roles| TB3
    TB3 -->|Sanitized Prompts| ExtAI
    TB3 -->|Scoped Room Grant| LK
```

### 2.7 Agent Orchestration Diagram
```mermaid
flowchart TD
    Goal["User Goal"] --> Auth["Authenticate & Resolve Permissions"]
    Auth --> Ctx["Context & Thread Ownership Check"]
    Ctx --> Intent["Intent Classification & Bounded Plan"]
    Intent --> Sup["Supervisor Routing"]
    Sup --> Spec["Specialized Capability (Alumni/Mentor/Career/Learning/Meeting/Comms/Events/RAG/Admin)"]
    Spec --> ToolAuth["Tool Selection + Backend Authorization"]
    ToolAuth --> Exec["Execute Read-Only Tool OR Prepare Consequential Action"]
    Exec --> Gate{"Consequential Mutation?"}
    Gate -->|Yes| Interrupt["Persist Checkpoint + Create ApprovalRequest (Rule 15)"]
    Interrupt -->|User Approves Exact Args| Revalidate["Revalidate Auth & Domain State -> Execute Domain Service"]
    Gate -->|No| Synth["Grounded Synthesis + Citation Validation"]
    Revalidate --> Synth
    Synth --> Out["Stream SSE / Envelope Response + Log AgentRun & Ledger"]
```

---

## 3. Sequence Diagrams (12 Mandatory Lifecycles)

### 3.1 Student Login & Alumni Login
```mermaid
sequenceDiagram
    actor U as Student / Alumnus
    participant M as Mobile App
    participant SA as Supabase Auth
    participant API as FastAPI AuthGW
    participant DB as PostgreSQL
    U->>M: Enter credentials (+ optional biometric unlock)
    M->>SA: signInWithPassword()
    SA-->>M: Access JWT + Refresh Token
    M->>API: GET /api/v1/users/me (Bearer JWT)
    API->>API: Verify JWT sig, exp, aud, revocation
    API->>DB: Resolve public.users + public.user_roles
    DB-->>API: Verified roles & profile completeness
    API-->>M: StandardEnvelope(UserProfileResponse)
```

### 3.2 Alumni Verification
```mermaid
sequenceDiagram
    actor Al as Unverified Alumnus
    actor Ad as Institutional Admin
    participant API as FastAPI Verification/Admin Service
    participant DB as PostgreSQL
    Al->>API: POST /api/v1/verifications/me (grad year, degree, evidence)
    API->>DB: Insert verification_requests (status='pending')
    Ad->>API: GET /api/v1/admin/verifications
    Ad->>API: POST /api/v1/admin/verifications/{id}/decision (approved)
    API->>DB: Update status, grant 'alumni' role in user_roles, write admin_audit_logs, outbox notification
    API-->>Ad: StandardEnvelope(VerificationRequestItem)
```

### 3.3 Mentorship Requests
```mermaid
sequenceDiagram
    actor S as Student
    actor A as Alumni Mentor
    participant API as MentorService
    participant DB as PostgreSQL
    S->>API: POST /api/v1/mentor-requests (mentor_id, topic, career_goal)
    API->>DB: Check capacity & no active pending duplicate
    API->>DB: Insert mentor_requests (pending) + notification
    A->>API: PATCH /api/v1/mentor-requests/{id} (accepted/rejected/clarify)
    API->>DB: Validate transition, update capacity if accepted, notify student
```

### 3.4 Meeting Requests, Acceptance & Counter-Proposals
```mermaid
sequenceDiagram
    actor S as Student
    actor A as Alumnus
    participant API as SchedulingService
    participant DB as PostgreSQL
    S->>API: POST /api/v1/meetings/requests (title, purpose, duration, up to 3 UTC slots)
    API->>DB: Validate slots vs alumni_availability & conflicts -> insert PENDING
    A->>API: POST /api/v1/meetings/requests/{id}/accept (slot_id)
    API->>DB: BEGIN TX -> lock alumni row -> check overlap -> insert meetings (SCHEDULED) -> COMMIT
    alt Counter-proposal
        A->>API: POST /api/v1/meetings/requests/{id}/counter-propose (alt_slots)
        API->>DB: Update request -> COUNTER_PROPOSED + insert new meeting_slots
        S->>API: POST /api/v1/meetings/requests/{id}/confirm (slot_id)
        API->>DB: Atomic conflict check -> insert meetings (SCHEDULED)
    end
```

### 3.5 Chat Delivery
```mermaid
sequenceDiagram
    actor U1 as Sender
    actor U2 as Recipient
    participant WS1 as FastAPI WS Worker 1
    participant DB as PostgreSQL
    participant R as Redis Pub/Sub
    participant WS2 as FastAPI WS Worker 2
    U1->>WS1: message.send (conversation_id, body, idempotency_key)
    WS1->>DB: Verify membership & not blocked -> INSERT messages (dedupe by key)
    WS1-->>U1: message.accepted (server_id, seq)
    WS1->>R: PUBLISH chat:{conversation_id} (message.created)
    R-->>WS2: Deliver event
    WS2-->>U2: message.created
    U2->>WS2: message.read (message_id)
    WS2->>DB: Update read pointer -> PUBLISH message.read
```

### 3.6 Video Meeting Admission & Screen Sharing
```mermaid
sequenceDiagram
    actor S as Student
    actor A as Alumni Host
    participant API as MeetingRoomService
    participant LK as LiveKit SFU
    S->>API: POST /api/v1/rooms/{meeting_id}/token
    API->>API: Verify confirmed meeting, participant membership, join window, not blocked
    API-->>S: Short-lived LiveKit JWT (role=participant, canPublish, waitingRoom)
    A->>API: POST /api/v1/rooms/{meeting_id}/token
    API-->>A: Short-lived LiveKit JWT (role=host, roomAdmin)
    S->>LK: Connect with JWT
    A->>LK: Admit participant / publish audio+video
    A->>LK: Publish screen share track (native Android foreground service / ReplayKit)
    LK-->>S: Forward screen share track via SFU
```

### 3.7 AI Mentor Recommendation, Scheduling with Approval & Provider Invocation
```mermaid
sequenceDiagram
    actor S as Student
    participant AI as LangGraph Orchestrator
    participant Vault as Encrypted Provider Vault
    participant LLM as External Provider (Gemini/OpenAI/Claude/DeepSeek)
    participant Sched as SchedulingService
    S->>AI: POST /api/v1/ai/chat/stream ("Find SE alumnus & arrange meeting")
    AI->>Vault: Decrypt active provider key (AES-256-GCM, server-only)
    AI->>LLM: Stream inference with sanitized prompt + authorized tools
    LLM-->>AI: Tool calls: search_alumni, find_mentors, get_alumni_availability
    AI->>Sched: Read permitted availability
    AI-->>S: SSE approval.required (draft_meeting_request + exact args)
    S->>AI: POST /api/v1/ai/approvals/{id}/decision (approved)
    AI->>AI: Verify user, expiration, exact args hash
    AI->>Sched: Execute create_meeting_request() via canonical service
    AI-->>S: Final confirmation + citations + usage ledger recorded
```

---

## 4. Canonical State Machines

### 4.1 Meeting Request State Machine
- `PENDING` -> `ACCEPTED` (triggers atomic `meetings` creation)
- `PENDING` -> `DECLINED`
- `PENDING` -> `COUNTER_PROPOSED`
- `PENDING` -> `CANCELLED` (by student)
- `PENDING` -> `EXPIRED` (slots elapsed)
- `COUNTER_PROPOSED` -> `ACCEPTED` (student confirms counter slot)
- `COUNTER_PROPOSED` -> `DECLINED`
- `COUNTER_PROPOSED` -> `CANCELLED`
- `COUNTER_PROPOSED` -> `EXPIRED`
Terminal states: `ACCEPTED`, `DECLINED`, `CANCELLED`, `EXPIRED`.

### 4.2 Confirmed Meeting State Machine
- `SCHEDULED` -> `IN_PROGRESS` (first participant/host joins room)
- `SCHEDULED` -> `CANCELLED` (explicit actor & reason)
- `SCHEDULED` -> `NO_SHOW` (window elapsed without join)
- `IN_PROGRESS` -> `COMPLETED` (host ends or timeout)
- `IN_PROGRESS` -> `CANCELLED` (aborted)
Rescheduling creates a new `meeting_requests` / `meetings` linked via `rescheduled_from_meeting_id` and marks the superseded meeting `CANCELLED` atomically.

### 4.3 Meeting Room State Machine
- `WAITING` -> `ACTIVE` -> `ENDED` (plus `EXPIRED` on room TTL).

### 4.4 Message Delivery State Machine
- Client local: `QUEUED_OFFLINE` -> `SENDING` -> Server durable: `SENT` -> `DELIVERED` -> `READ` (or `FAILED_RETRYABLE`).

### 4.5 AI Approval State Machine
- `pending` -> `approved` -> `executed` (or `execution_failed`)
- `pending` -> `rejected`
- `pending` -> `expired`
Arguments are SHA-256 hashed (`args_hash`) at creation and verified upon execution so modified arguments are rejected.

---

## 5. Architectural Decisions Summary (ADRs)
See `docs/architecture/adr/` for full ADRs approving:
- **ADR-001:** Retain FastAPI Modular Monolith + PostgreSQL/Supabase.
- **ADR-002:** PostgreSQL GIST Exclusion Constraints & Transactional Outbox for Scheduling.
- **ADR-003:** FastAPI WebSocket + Redis Pub/Sub (PostgreSQL as Durable Store).
- **ADR-004:** LiveKit SFU & Expo SDK 52 Native Compatibility Policy.
- **ADR-005:** Multi-Provider AI Abstraction, AES-256-GCM Encrypted Vault & SSE Streaming.
