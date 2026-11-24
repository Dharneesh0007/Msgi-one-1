# ADR-001: Retain FastAPI Modular Monolith with PostgreSQL & Supabase

- **Status:** Accepted (Phase 1)
- **Requirement ID:** NFR-MAINT-01, NFR-REL-01, NFR-REL-02
- **Governing Textbooks:** Robert C. Martin (*Clean Architecture*), Ian Sommerville (*Software Engineering*, 10th Ed.).
- **Decision:** Retain the single FastAPI modular monolith (`services/api`) organized into Routers -> Domain Services -> Repository Interfaces -> SQLAlchemy 2.0 Async Repositories -> PostgreSQL 17, preserving dual-prefix compatibility (`/api/v1` and `/api/v1/api/v1`) for frozen APK `a95a7169-d48b-4730-bcfd-921500e4b8fae`.
- **Alternatives Considered:** Splitting into separate microservices for scheduling, messaging, and AI. Rejected because current operational scale does not justify distributed transaction overhead, network hops, or duplicate auth gateways.
- **Justification:** Single transactional boundary across mentorship, scheduling, notifications, and AI approvals; zero duplication of domain authorization.
- **Implementation Files:** `services/api/src/main.py`, `services/api/src/services/*`, `services/api/src/repositories/*`.
- **Verification Tests:** `test_frozen_apk_contracts.py`, `test_postgres_integration.py`.
- **Known Limitations:** Horizontal scaling requires stateless API workers + Redis Pub/Sub for WebSocket fan-out (ADR-003).
