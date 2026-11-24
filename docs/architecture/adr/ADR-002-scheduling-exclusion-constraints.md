# ADR-002: Database-Level Scheduling Conflict Prevention & Transactional Outbox

- **Status:** Accepted (Phase 1)
- **Requirement ID:** FR-MEETING-05, NFR-DATA-01, NFR-REL-01
- **Governing Textbooks:** Elmasri & Navathe (*Fundamentals of Database Systems*, 7th Ed.), Martin Kleppmann (*Designing Data-Intensive Applications*).
- **Decision:** Model scheduling with `alumni_availability`, `meeting_requests`, `meeting_slots`, and `meetings`. Enforce zero overlapping confirmed meetings in PostgreSQL using `btree_gist` + `EXCLUDE USING gist (alumni_id WITH =, tstzrange(scheduled_start, scheduled_end, '[)') WITH &&) WHERE (status IN ('scheduled', 'in_progress'))`, combined with row-level locking and `idempotency_keys` + `outbox_events` in the same ACID transaction.
- **Alternatives Considered:** Application-only overlap checks without DB constraints. Rejected due to race conditions under concurrent acceptance requests.
- **Justification:** Guarantees linearizable booking integrity even across concurrent workers; transactional outbox ensures notifications reflect committed state.
- **Implementation Files:** `supabase/migrations/20261125000001_enterprise_ecosystem.sql`, `services/api/src/db/models/enterprise.py`, `services/api/src/repositories/enterprise_repositories.py`.
- **Verification Tests:** `test_enterprise_schema.py`, Phase 5 concurrency tests.
- **Known Limitations:** SQLite test environments do not support PostgreSQL `EXCLUDE USING gist`, so unit tests verify application-level locking/overlap queries while PostgreSQL DDL enforces GIST exclusion.
