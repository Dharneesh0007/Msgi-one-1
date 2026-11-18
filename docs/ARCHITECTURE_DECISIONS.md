# MSGI One — Architecture Decision Records (ADRs)

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Date:** November 18, 2026  
**Status:** ACCEPTED & LOCKED  

---

## ADR-001: Adoption of a Modular Monolith over Microservices

### Status
Accepted

### Context & Problem Statement
The MSGI One ecosystem integrates 12 functional modules (Alumni, Career, Mentorship, Events, Giving, Startups, AI Command Centre, etc.) serving 5 distinct personas. The project must produce a verified, fully operational Android-first MVP in 3 days. We must decide whether to structure the system as distributed microservices or as a modular monolith.

### Decision
We adopt a **Modular Monolith** pattern within a single monorepo (`msgi-one/`), deploying one unified FastAPI service and one PostgreSQL instance. Each domain module is implemented in its own isolated Python package/router with strict internal interface boundaries.

### Engineering Principle
- **Martin Kleppmann (*Designing Data-Intensive Applications*, Ch. 11):** Distributed systems introduce the dual-write problem, asynchronous partial failure states, and complex distributed transaction coordination.
- **Ian Sommerville (*Software Engineering*, Ch. 6):** Architectural design must optimize for cohesion and maintainability before distributing components across networks.

### Consequences & Trade-offs
- **Positive:** Enables ACID transactional consistency across related tables; eliminates network serialization latency; single migration chain; rapid end-to-end integration testing.
- **Negative / Mitigation:** Potential risk of code entanglement over time. Mitigated by strict Domain-Driven Design bounded contexts, Pydantic interface contracts, and automated dependency linting.

---

## ADR-002: React Native with Expo and Expo Router for Mobile Client

### Status
Accepted

### Context & Problem Statement
The client must run reliably on Android devices, present responsive UI, support role-specific navigation, handle deep-linking, and build cleanly under tight deadlines without brittle native Android Gradle configuration errors.

### Decision
We use **React Native with Expo SDK 52+ and Expo Router v4** in strict TypeScript mode. Build automation is delegated to Expo EAS Build with local emulator fallback.

### Engineering Principle
- **Roger S. Pressman (*Software Engineering*, Ch. 12):** Interface consistency, predictable navigational hierarchy, and single-source-of-truth component libraries minimize mobile defect density.

### Consequences & Trade-offs
- **Positive:** Type-safe file-based routing; zero manual Java/Kotlin boilerplate; rapid hot reloading; instant native UI compilation; native Android back-handler support.
- **Negative / Mitigation:** Reliance on Expo-compatible native modules. Mitigated by verifying that all required hardware integrations (camera, storage, secure store) use official, audited Expo plugins.

---

## ADR-003: FastAPI Async Python Backend with Pydantic v2 and SQLAlchemy 2.0

### Status
Accepted

### Context & Problem Statement
The backend must deliver high-concurrency REST APIs, validate strict payloads across 12 modules, and natively host LangGraph AI agent workflows without multi-process IPC serialization bottlenecks.

### Decision
We standardize on **FastAPI with Python 3.12**, utilizing **Pydantic v2** for schema enforcement and **SQLAlchemy 2.0 (Async)** with `asyncpg` for non-blocking persistence.

### Engineering Principle
- **Eric Evans (*Domain-Driven Design*, Ch. 4):** Layered architecture isolates domain models from application services and presentation endpoints.
- **Ian Sommerville (*Software Engineering*, Ch. 7):** Automated interface verification prevents runtime contract drift.

### Consequences & Trade-offs
- **Positive:** Native async event loop; sub-millisecond Rust-backed Pydantic validation; automatic OpenAPI 3.1 documentation; co-located Python AI agent graphs.
- **Negative / Mitigation:** Python CPU-bound tasks can block the async loop. Mitigated by offloading long-running AI workflow graph executions to background tasks with persistent state tracking in PostgreSQL.

---

## ADR-004: Unified PostgreSQL with pgvector and Row-Level Security

### Status
Accepted

### Context & Problem Statement
MSGI One requires relational integrity across profiles, jobs, mentors, and events, while simultaneously requiring semantic vector search for AI-driven alumni discovery, mentor matching, and job recommendations.

### Decision
We use a single **PostgreSQL 15+** database hosted on Supabase, enabling the **`pgvector`** extension for vector similarity search (1536-dimensional embeddings) alongside traditional relational tables. We enforce database-level **Row-Level Security (RLS)** for multi-tenant isolation.

### Engineering Principle
- **Silberschatz, Korth, Sudarshan (*Database System Concepts*, Ch. 2, 4, 14):** Relational integrity, foreign key constraints, and atomic transactions prevent orphaned records and inconsistent application state.
- **Martin Kleppmann (*Designing Data-Intensive Applications*, Ch. 3):** Consolidating vector embeddings directly alongside relational records avoids multi-database synchronization lag and orphaned embeddings.

### Consequences & Trade-offs
- **Positive:** Hybrid queries (combining vector distance with relational filters like `WHERE location = 'Japan'`) in a single query; ACID transactions; row-level security enforced at the storage engine.
- **Negative / Mitigation:** High-dimensional vector indexing consumes RAM. Mitigated by using HNSW indexing with appropriate `m` and `ef_construction` parameters and keeping embedding generation asynchronous.

---

## ADR-005: Stateless FastAPI Token Validation with Supabase JWT & Server-Side RBAC

### Status
Accepted

### Context & Problem Statement
Five distinct personas (Student, Alumni, Faculty, Recruiter, Admin) access different modules. The client cannot be trusted to self-report roles or identities in request bodies.

### Decision
Identity is authenticated via **Supabase Auth**. The mobile client sends an `Authorization: Bearer <jwt>` header on every API call. FastAPI cryptographically verifies the RS256/ES256 signature and decodes the authenticated `sub` (user UUID). User roles and permissions are retrieved and verified server-side from `public.user_roles`. Request payloads claiming user IDs or roles are strictly discarded.

### Engineering Principle
- **Roger S. Pressman (*Software Engineering*, Ch. 9):** Security engineering requires the Principle of Least Privilege and complete mediation of every security-sensitive request.

### Consequences & Trade-offs
- **Positive:** Zero client-side role forgery; stateless verification at the API boundary; fine-grained FastAPI dependency injection (`Depends(get_current_active_user)`).
- **Negative / Mitigation:** Requires database lookup for cached role verification if not baked into custom JWT claims. Mitigated by attaching role claims into the JWT or using in-memory TTL caching for role lookups.

---

## ADR-006: LangGraph StateGraph Architecture with Human-in-the-Loop Approvals

### Status
Accepted

### Context & Problem Statement
MSGI One requires an agentic AI ecosystem to interpret student goals, recommend mentors, suggest jobs, and generate roadmaps. Autonomous agents that execute actions without validation risk hallucination, spamming alumni, or modifying institutional records.

### Decision
We implement a **LangGraph StateGraph** multi-agent orchestrator. Agents act via strictly defined Pydantic tool contracts. Any consequential action (sending mentorship requests, direct alumni messaging, applying for jobs, publishing events, financial transactions) **requires explicit user approval** via a persistent database-backed approval gate.

### Engineering Principle
- **Roger S. Pressman (*Software Engineering*, Ch. 15):** Controlled state machines with formal pre-conditions and post-conditions prevent erratic autonomous system failure.
- **Martin Kleppmann (*Designing Data-Intensive Applications*, Ch. 10):** Auditable, reproducible event flows with human checkpoints prevent unintended side effects in automated workflows.

### Consequences & Trade-offs
- **Positive:** Provable state transitions; zero accidental or hallucinated external side-effects; complete auditability of every AI action.
- **Negative / Mitigation:** Human approval introduces an asynchronous pause. Mitigated by designing UI modal approval prompts and persistent workflow checkpoints in the database.

---

## ADR-007: Realtime Architecture via PostgreSQL Change Data Capture (CDC)

### Status
Accepted

### Context & Problem Statement
Users expect instant notifications when mentor requests are accepted, events are updated, or application statuses change, without heavy polling that drains mobile battery life.

### Decision
We use **Supabase Realtime** listening to PostgreSQL Write-Ahead Log (WAL) replication for user-specific channels (e.g. `notifications:user_id`). The mobile app subscribes to its authenticated channel over WebSocket.

### Engineering Principle
- **Martin Kleppmann (*Designing Data-Intensive Applications*, Ch. 11):** Event-driven data propagation derived directly from the commit log guarantees that notifications reflect actual committed database state.

### Consequences & Trade-offs
- **Positive:** Zero client polling; instantaneous delivery; minimal server memory consumption.
- **Negative / Mitigation:** Requires active WebSocket connection. Mitigated by pairing Realtime with persistent database notification tables so offline clients receive all pending notifications upon reconnection.

---

## ADR-008: Synthetic & Anonymized Seed Data Strategy

### Status
Accepted

### Context & Problem Statement
Development and testing require rich rosters of students, alumni, faculty, mentors, jobs, and events. Real institutional records contain FERPA/GDPR/DPDP-protected student PII.

### Decision
No real student or alumni data will be imported. We use a **strictly synthetic, deterministic seed dataset** (`supabase/seed/00001_synthetic_seed.sql`) containing realistic, anonymized personas across all 12 modules, clearly labeled with `@example.msgi.edu` email domains.

### Engineering Principle
- **Pressman & Maxim (*Software Engineering*, Ch. 20):** Test data management requires representative, reproducible, and legally compliant data fixtures.

### Consequences & Trade-offs
- **Positive:** Complete regulatory compliance; zero PII leakage risk; 100% reproducible test suites across all environments.
- **Negative / Mitigation:** Synthetic data may not capture edge cases of messy legacy institutional data. Mitigated by designing strict schema validation rules that sanitize and format all incoming user data.
