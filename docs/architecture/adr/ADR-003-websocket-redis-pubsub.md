# ADR-003: Real-Time Messaging via FastAPI WebSockets, PostgreSQL & Redis Pub/Sub

- **Status:** Accepted (Phase 1)
- **Requirement ID:** FR-CHAT-01..05, NFR-PERF-02, NFR-REL-01
- **Governing Textbooks:** Kurose & Ross (*Computer Networking*, 8th Ed.), Martin Kleppmann (*Designing Data-Intensive Applications*).
- **Decision:** Implement `/ws/chat` in FastAPI with JWT handshake authentication, PostgreSQL as the single durable message store (persisted prior to `message.accepted` ACK), per-conversation monotonic sequence numbers (`seq`) for cursor recovery, and Redis Pub/Sub for multi-worker fan-out (with local in-process fallback when Redis is absent in dev/CI).
- **Alternatives Considered:** Using Redis Pub/Sub or Streams alone without PostgreSQL persistence, or HTTP short polling. Rejected due to ephemeral message loss in Pub/Sub and excessive latency/overhead in polling.
- **Justification:** Survives worker restarts, enables deterministic reconnection recovery, and cleanly separates durable state from ephemeral fan-out.
- **Implementation Files:** `services/api/src/db/models/enterprise.py` (Phase 2), `services/api/src/routers/ws_chat.py` (Phase 6).
- **Verification Tests:** Phase 6 WebSocket, multi-worker fan-out, and reconnect cursor tests.
- **Known Limitations:** Multi-worker fan-out requires an active Redis instance in production; local single-process mode uses in-memory pub/sub.
