# ADR-005: Multi-Provider AI Abstraction, AES-256-GCM Encrypted Vault & SSE Streaming

- **Status:** Accepted (Phase 1)
- **Requirement ID:** FR-AI-01..06, FR-ADMIN-02, NFR-SEC-01, NFR-COST-01
- **Governing Textbooks:** Chip Huyen (*Designing Machine Learning Systems*, *AI Engineering*), Russell & Norvig (*AIMA*, 4th Ed.), Robert C. Martin (*Clean Architecture*).
- **Decision:** Extend `src/ai/` with a unified provider interface supporting Google Gemini (preserved compatibility), OpenAI, Anthropic Claude, and DeepSeek. Store provider credentials in `ai_provider_configs` encrypted with AES-256-GCM (unique 96-bit nonce + AAD, server-side `AI_VAULT_MASTER_KEY` env/KMS), log usage in `ai_usage_ledger`, enforce Rule 15 HITL argument hashing, and expose real async token streaming at `POST /api/v1/ai/chat/stream`.
- **Alternatives Considered:** Storing keys in environment variables only or returning keys to admin UI. Rejected because admins need runtime multi-provider management without key exposure.
- **Justification:** Zero plaintext keys in DB, logs, or mobile client; supports provider failover governed by privacy/capability policies.
- **Implementation Files:** `services/api/src/db/models/enterprise.py` (Phase 2), `services/api/src/ai/*` (Phase 8).
- **Verification Tests:** Phase 8 vault encryption, SSE streaming, HITL tamper-resistance, and mocked multi-provider tests.
- **Known Limitations:** Live external API verification requires authorized provider API keys; mocked CI suites run deterministically without keys.
