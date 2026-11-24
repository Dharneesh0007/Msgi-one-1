# MSGI One — Operational Runbook, SLOs & Maintenance Schedule (Phase 12)

---

## 1. Service Level Objectives (SLOs) & Error Budgets

| Service Area | SLI Metric | Target SLO | Monthly Error Budget |
| :--- | :--- | :---: | :---: |
| Core REST API (`/health`, `/ready`, Directory, Profiles) | Availability (`HTTP 2xx/3xx/4xx` vs `5xx`) | 99.9% | 43.2 minutes |
| Core REST Latency | `p95` server processing time | < 250 ms | 5% slow tail |
| Scheduling & Double-Booking Integrity | Zero overlapping confirmed meetings per alumni | 100.0% | 0.0% tolerance |
| Real-Time Chat Delivery | Persisted message ACK before broadcast | 99.95% | 21.6 minutes |
| AI Command Centre Safety (Rule 15) | Consequential mutations gated by valid owner HITL | 100.0% | 0.0% tolerance |

---

## 2. Standard Operating Procedures

### 2.1 AI Provider Key Rotation (Admin Control Centre)
1. Navigate to Mobile **Admin Dashboard -> Open AI Provider Key Vault** (or `POST /api/v1/admin/ai/providers/{id}/rotate-key`).
2. Supply the new vendor API key. The backend encrypts via AES-256-GCM with fresh 96-bit nonce and increments `key_version`.
3. Click **Verify Health** (`POST /api/v1/admin/ai/providers/{id}/verify`) to validate connectivity safely.
4. Revoke old key at vendor console once verified.

### 2.2 Master Vault Key (`AI_VAULT_MASTER_KEY`) Incident Response
- If `AI_VAULT_MASTER_KEY` is suspected compromised: set emergency kill switch (`is_enabled=false` or revoke affected configs), rotate master secret in host KMS/environment, and re-enter vendor keys.

### 2.3 Database Migration & Rollback Procedure
- Apply migrations strictly in staging first (`supabase db push`), verify `pytest tests/test_postgres_integration.py`, then schedule production window.
- If enterprise migration rollback is required cleanly, execute `supabase/rollbacks/20261125000001_enterprise_ecosystem_rollback.sql` ONLY after snapshotting affected enterprise tables and receiving explicit owner sign-off.

### 2.4 Redis & LiveKit Degradation Handling
- **Redis Outage:** `realtime_bus.py` automatically degrades to bounded per-worker local WebSocket fan-out. Scale API instances to 1 worker temporarily during single-node maintenance or restore managed Redis cluster cleanly.
- **LiveKit Unreachable / Circuit Open:** Meetings remain active cleanly in scheduling + messaging; `.ics` calendar details remain valid, and `/ready` flags `livekit: awaiting_credentials`.

---

## 3. Recurring Maintenance Schedule

| Cadence | Operational Task |
| :--- | :--- |
| **Daily** | Automated check of `ai_usage_ledger` spend vs daily budgets and error rates via `/api/v1/admin/ai/usage`. |
| **Weekly** | Run full `services/api/scripts/run_benchmarks.py` and 15-case `src/ai/evaluation.py` regression suite. |
| **Monthly** | Dependency security scan (`uv` lock audit + `npm audit` + `npx expo-doctor`), prune expired session revocations & notifications. |
| **Quarterly** | Mandatory AI provider key rotation & backup restore drill on staging PostgreSQL clone. |
