# MSGI ONE — SECURITY ARCHITECTURE & THREAT MODEL

**Document ID:** MSGI-THREAT-001  
**Phase:** Phase 1 — Requirements Engineering & Unified System Architecture  
**Governing Textbooks:** Ian Sommerville (*Software Engineering*, Security Engineering); Roger S. Pressman & Bruce R. Maxim; Robert C. Martin (*Clean Architecture*).

---

## 1. System Trust Boundaries
1. **TB-1 (Client Boundary):** Mobile device (`apps/mobile`) holds only `SUPABASE_ANON_KEY`, short-lived user JWT, and biometric unlock state. Zero AI API keys, zero `service_role` keys, zero master encryption keys.
2. **TB-2 (API / WebSocket / SSE Gateway):** Validates JWT cryptographic signature (`HS256`/`RS256`/`ES256` with JWKS/public key — **no unverified signature fallback**), `exp`, `aud`, `iss`, session revocation, rate limits, and server-side roles.
3. **TB-3 (Domain & Data Boundary):** Domain services enforce object-level authorization (`PermissionChecker`). Backend currently connects as `postgres` (`rolbypassrls=True`); therefore FastAPI domain services and repositories are the primary enforcement boundary, reinforced by RLS policies for `authenticated` and a prepared least-privilege runtime DB role migration.
4. **TB-4 (AI & Real-Time Media Boundary):** Prompts are PII-masked before leaving TB-3. External AI keys are encrypted at rest with AES-256-GCM and decrypted only inside the server-side provider adapter. LiveKit room tokens are short-lived and scoped to confirmed meeting participants.

---

## 2. STRIDE Threat Analysis & Mitigations

| Threat Category | Threat Scenario | Existing / Target Mitigation | Verification |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Forged `RS256`/`ES256` JWT accepted if JWKS lookup fails (`verify_signature=False` defect found in `core/security.py`). | **P3 Fix:** Remove `verify_signature=False` fallback completely; require valid JWKS or configured asymmetric public key; reject `alg=none`. | `test_security.py`, `test_phase3_security.py` |
| **Spoofing / Tampering** | Client sends `role: "admin"` or `user_id` in JSON payload or `user_metadata`. | Derive `user_id` strictly from verified JWT `sub`; resolve roles server-side from `public.user_roles` / trusted app claims; forbid extra fields on schemas. | `test_profiles.py`, `test_roles.py` |
| **Tampering** | User modifies arguments after AI Rule 15 approval is issued or replays expired approval. | Compute SHA-256 `args_hash` over canonical action & arguments; bind approval to `user_id`, `expires_at`, and `idempotency_key`; revalidate domain state on execution. | `test_ai_command_centre.py`, P8 tests |
| **Repudiation** | Admin approves unverified alumnus or changes AI provider without trace. | Immutable `admin_audit_logs` and `audit_logs` recording actor, target, action, previous/new state, and UTC timestamp. | `test_phase_4_modules.py` |
| **Info Disclosure** | Alumni private email/phone/location leaked in directory or RAG; plaintext AI key returned to admin UI or logged. | FERPA DTO projection; RAG privacy filter & `user_skills` RLS gate; AES-256-GCM vault returns masked hint only (`...last4`); log redactor strips secrets/tokens/PII. | `test_phase_5_security_compliance.py`, `test_phase3_security.py` |
| **Info Disclosure** | Unauthorized user joins LiveKit meeting room or subscribes to another user's chat conversation. | `PermissionChecker` verifies conversation membership, block list, confirmed meeting participant, and join window before issuing WS subscription or LiveKit token. | P6/P7 authorization tests |
| **Denial of Service** | Unbounded AI token spend, concurrent meeting double-booking, WebSocket flood. | Request/daily/monthly token budgets, circuit breakers, rate limits, bounded WS queues, PostgreSQL GIST exclusion constraints & idempotency keys. | `test_ai_security_and_costs.py`, P5/P6/P10 tests |
| **Elevation of Privilege** | Unverified alumnus accesses verified-alumni mentor/posting privileges; prompt injection invokes admin tools. | Explicit verification status checks (`is_verified` + `alumni` role); agents have zero direct DB/SQL access and execute only user-scoped tools with Rule 15 HITL gates. | `test_postgres_authorization.py`, `test_rag_grounding.py` |
