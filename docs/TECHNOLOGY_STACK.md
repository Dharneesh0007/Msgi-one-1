# MSGI One — Technology Stack Specification

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** Principal Software Architect, Senior Full-Stack Engineer, Database Architect & DevSecOps Engineer  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Executive Summary & Stack Selection Matrix

The technology stack for MSGI One is engineered to satisfy two primary constraints:
1. Deliver an integrated, production-grade **Android-first MVP within 3 days**.
2. Establish a foundation that scales to hundreds of thousands of institutional stakeholders (Students, Alumni, Faculty, Recruiters, Administrators) without structural rewrites.

Following the principles established by **Martin Kleppmann** (*Designing Data-Intensive Applications*, Chapter 1: "Reliability, Scalability, Maintainability") and **Roger S. Pressman** (*Software Engineering: A Practitioner's Approach*, Chapter 8: "Design Concepts"), we reject distributed microservices, polyglot databases, and disconnected prototypes in favour of a **Typed Modular Monolith** with unified relational persistence and a dedicated graph-based Agentic AI orchestrator.

| Layer | Selected Technology | Version / Standard | Primary Justification |
| :--- | :--- | :--- | :--- |
| **Mobile Client** | React Native + Expo | Expo SDK 52+ / RN 0.76+ | Cross-platform native compilation, rapid Android APK generation via EAS, native UI performance. |
| **Navigation & Typing** | Expo Router + TypeScript | Expo Router v4 / TS 5.x | File-based typed routing, deep-linking, automatic Android back-button handling, zero runtime route drift. |
| **Backend Framework** | FastAPI (Python) | FastAPI 0.115+ / Python 3.12 | Async I/O, native Pydantic v2 validation, automatic OpenAPI v3.1 schema generation, native AI ecosystem integration. |
| **Data Access & ORM** | SQLAlchemy + Alembic | SQLAlchemy 2.0 (Async) / Alembic 1.14+ | Type-safe SQL generation, connection pooling, ACID transaction guarantees, deterministic database migrations. |
| **Primary Database** | PostgreSQL via Supabase | PostgreSQL 15+ | Relational integrity, ACID transactions, Row-Level Security (RLS), mature indexing (B-Tree, GIN, GiST). |
| **Vector Engine** | pgvector | pgvector 0.7+ (Postgres extension) | In-database cosine vector indexing (HNSW/IVFFlat) for semantic search, eliminating secondary vector DB operational complexity. |
| **Auth & Identity** | Supabase Auth | OAuth2 / JWT (RS256) | Battle-tested session management, secure refresh token rotation, native mobile deep-link callbacks. |
| **File Storage** | Supabase Storage | S3-Compatible Object Store | Signed URLs for sensitive documents (resumes, transcripts), public CDN for avatar/event assets, RLS-backed buckets. |
| **Realtime Engine** | Supabase Realtime | Postgres CDC (WebSockets) | Realtime notifications and status updates via PostgreSQL write-ahead log (WAL) replication, zero polling. |
| **Agentic AI Engine** | LangGraph | LangGraph 0.2+ / LangChain 0.3+ | Explicit state machine graphs, deterministic routing, cyclic reasoning, human-in-the-loop approval gates. |
| **LLM Gateway** | Google Gemini / Multi-Provider | Gemini 1.5/2.0 Flash / OpenAI API | High structured output fidelity, low latency, 1M+ context window for institutional documents, provider abstraction. |
| **DevOps & Packaging** | Expo EAS + Containerized API | Docker / EAS Build / GitHub Actions | Reproducible Android AAB/APK builds, cloud container hosting, automated CI verification. |

---

## 2. Deep-Dive Architectural Evaluation

### 2.1 Mobile Frontend: React Native with Expo and Expo Router
- **Textbook Principle (Pressman & Maxim, Ch. 12: Mobile App Design):** Mobile architectures require consistent UI hierarchy, predictable state transitions, and responsive asynchronous event handling.
- **Why Expo over Bare React Native:**
  - Modern Expo (`expo-prebuild` and Config Plugins) eliminates the maintenance burden of bare native Android `gradle` files while retaining full native build capabilities.
  - Expo Router v4 brings the battle-tested conventions of modern file-based routing to mobile: nested layouts, native stack transitions, modal sheets, and deep-linking out of the box.
  - Native gesture handling, haptics, and secure storage are standardized via official SDK modules (`expo-secure-store`, `expo-crypto`, `expo-image`).
- **Typing & UI Design System:**
  - Strict TypeScript (`strict: true`) shared with backend contract definitions.
  - UI Component System: Reusable, accessible components (Cards, Badges, Modals, Timeline items, Form fields) built on React Native StyleSheet or lightweight Tailwind tokens (NativeWind) adhering to 48dp Android touch-target standards.

### 2.2 Backend Service: FastAPI with Python 3.12, Pydantic v2 & SQLAlchemy 2.0
- **Textbook Principle (Ian Sommerville, Ch. 6: Architectural Design):** A layered, modular monolith provides high cohesion within domain modules and loose coupling between presentation and data persistence.
- **Why FastAPI over Node/Express or Django:**
  - Python is the undisputed native runtime for modern Agentic AI (LangGraph, LangChain, embeddings, PyTorch). Running the backend in Python avoids inter-process serialization overhead between an API server and a separate AI worker.
  - FastAPI is powered by Starlette and Pydantic v2 (core compiled in Rust). It benchmarks on par with Node.js and Go for I/O-bound web services while providing static typing and automated OpenAPI schema documentation.
  - Pydantic v2 handles runtime payload validation at the HTTP boundary, guaranteeing that no malformed request reaches domain logic.
- **Why SQLAlchemy 2.0 Async + Alembic:**
  - Modern SQLAlchemy 2.0 provides type-annotated declarative models (`Mapped[T]`) matching Python type hints.
  - Asynchronous query execution (`asyncpg` driver) ensures that non-blocking database queries release Python event loops during I/O.
  - Alembic guarantees deterministic, versioned database schema migrations that are tracked in Git, preventing manual database drift.

### 2.3 Persistence & Identity: PostgreSQL (Supabase) + pgvector
- **Textbook Principle (Silberschatz, Korth, Sudarshan, Ch. 2-4: Relational Model & Integrity Constraints):** Centralized relational databases enforce entity integrity, referential integrity, domain constraints, and atomic transactions.
- **Why PostgreSQL + pgvector over Polyglot Databases:**
  - Avoids Kleppmann's "Dual-Write Problem" (DDIA, Chapter 11): updating a relational user record and a standalone vector database (e.g. Pinecone) across two separate systems without distributed two-phase commits creates silent data drift.
  - Storing user profile vectors, job vectors, and institutional document chunks inside PostgreSQL via `pgvector` allows atomic relational filtering (e.g. `WHERE role = 'alumni' AND location = 'Tokyo'`) combined in a single SQL query with cosine similarity ordering (`ORDER BY embedding <=> query_vector`).
- **Why Supabase Auth:**
  - Provides battle-tested PKCE OAuth and email/password authentication with JWT issuance.
  - FastAPI validates incoming Supabase JWTs locally using public cryptographic keys (RS256/ES256), enforcing zero-network-latency stateless token authentication.

### 2.4 Agentic AI: LangGraph State Machine Architecture
- **Textbook Principle (Pressman & Maxim, Ch. 15: Component-Level Design):** Autonomous agent systems require deterministic state tracking, bounded execution loops, and verifiable post-conditions.
- **Why LangGraph over Unconstrained Autonomous Agent Frameworks:**
  - Unconstrained agent loops (e.g., bare ReAct loops) frequently suffer from infinite cycles, hallucinated tool invocations, and unpredictable costs.
  - LangGraph models multi-agent orchestration as a **StateGraph**: vertices represent explicit agent reasoning or tool execution steps; edges represent deterministic or conditional transitions.
  - **Human-in-the-Loop Interruptibility:** LangGraph natively supports state persistence and workflow checkpointing. When an agent reaches a consequential boundary (e.g. initiating an alumni contact, applying to a job), it executes an `interrupt()`, writes an approval record to PostgreSQL, and pauses until a human user signs off.

---

## 3. Cost, Complexity & Operational Trade-off Analysis

| Metric | Modular Monolith (Selected) | Microservices Architecture (Rejected) | Distributed Polyglot DB (Rejected) |
| :--- | :--- | :--- | :--- |
| **Operational Overhead** | 1 API container + 1 managed PostgreSQL. | 12+ microservice deployments, API gateway, service mesh. | Relational DB + Redis + Standalone Vector DB + Queue broker. |
| **Data Consistency** | ACID transactions across all 12 modules. | Eventual consistency, saga patterns, complex distributed rollback. | Dual-write drift, un-synchronized index deletes. |
| **Development Velocity** | Maximum: single repository, shared types, single migration chain. | Minimal: cross-repo versioning, mock service coordination. | Slow: multiple client libraries, schema duplication. |
| **Estimated Hosting Cost (MVP)** | **$0 / month (Free tier)**; scales to <$50/mo for 20k MAU. | $200 - $500 / month minimum for multi-cluster container hosting. | $150+ / month minimum for managed vector DB + cache clusters. |
| **3-Day Feasibility** | **Achievable:** verified contracts and single test suite. | **Impossible:** inter-service auth, contract testing, network glue. | **High Risk:** sync errors during demo runs. |

---

## 4. Engineering Reference Sign-Off

This stack adheres strictly to the architectural standards of Pressman, Silberschatz, Kleppmann, Sommerville, and Evans. It provides maximum speed for 3-day MVP delivery without compromising enterprise-grade reliability or security.
