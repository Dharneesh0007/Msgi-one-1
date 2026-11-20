# MSGI One — Staging Deployment & Operations Handoff Guide
**Environment:** STAGING ONLY  
**Branch:** `deploy/staging-hosted`  
**Supabase Reference:** `jndvnbvpwxhfmqgmqxfm`  
**Execution Timestamp:** 2026-11-20T13:46:00+05:30  
**Compliance Standard:** Mandatory Engineering Laws (AGENTS.md Rules 7, 10, 16, 19, 20)  

---

## 1. Executive Summary & Purpose

This handoff guide provides engineering, QA, and DevOps teams with the complete operational procedures required to run, monitor, maintain, and troubleshoot the MSGI One platform in the hosted staging environment.

---

## 2. Infrastructure Endpoints & Service Topology

| Component | Target URL / Host | Protocol | Authentication / Port |
| :--- | :--- | :---: | :--- |
| **Supabase REST / PostgREST** | `https://jndvnbvpwxhfmqgmqxfm.supabase.co/rest/v1` | HTTPS | `apikey` + Bearer JWT |
| **Supabase Auth (GoTrue)** | `https://jndvnbvpwxhfmqgmqxfm.supabase.co/auth/v1` | HTTPS | ES256 Asymmetric JWKS |
| **Supabase Realtime** | `wss://jndvnbvpwxhfmqgmqxfm.supabase.co/realtime/v1/websocket`| WSS | Phoenix Channels v1.0.0 |
| **PostgreSQL Pooler (PgBouncer)** | `aws-1-ap-south-1.pooler.supabase.com:6543/postgres` | TLS | `asyncpg` (`statement_cache_size=0`) |
| **FastAPI Backend (Staging)** | `http://localhost:8000` (or `https://api-staging.msgi.edu`) | HTTPS/HTTP | Bearer JWT (FastAPI Complete Mediation) |
| **Mobile Client** | `apps/mobile` (Expo SDK 52) | Hermes `.hbc` | Profile: `staging` (`apps/mobile/eas.json`) |

---

## 3. Environment Variable Injection Template (`.env.staging`)

```bash
# ==========================================
# 1. APPLICATION ENVIRONMENT
# ==========================================
ENVIRONMENT=staging
DEBUG=False
API_V1_STR=/api/v1
PROJECT_NAME="MSGI One — Agentic AI Institutional Alumni Ecosystem (Staging)"

# ==========================================
# 2. SUPABASE HOSTED INFRASTRUCTURE
# ==========================================
SUPABASE_URL=https://jndvnbvpwxhfmqgmqxfm.supabase.co
EXPO_PUBLIC_SUPABASE_URL=https://jndvnbvpwxhfmqgmqxfm.supabase.co
SUPABASE_ANON_KEY=<staging-publishable-anon-key>
EXPO_PUBLIC_SUPABASE_ANON_KEY=<staging-publishable-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<staging-secret-service-role-key>

DATABASE_URL=postgresql+asyncpg://postgres.jndvnbvpwxhfmqgmqxfm:<db-password>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ==========================================
# 3. AGENTIC AI & PERSISTENCE
# ==========================================
LANGGRAPH_CHECKPOINT_MODE=sqlite
GEMINI_API_KEY=<gemini-api-key>

# ==========================================
# 4. BACKEND HOSTING & CORS
# ==========================================
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_CORS_ORIGINS=["http://localhost:8081","http://localhost:19006","http://10.0.2.2:8000","https://api-staging.msgi.edu"]
EXPO_PUBLIC_API_URL=https://api-staging.msgi.edu/api/v1
```

---

## 4. Operational Runbooks

### 4.1 Running the Staging Backend
```powershell
cd msgi-one
.\services\api\.venv\Scripts\uvicorn.exe src.main:app --host 0.0.0.0 --port 8000 --app-dir services/api
```

### 4.2 Re-Running Automated Staging Verification Suite
```powershell
cd msgi-one
# Verify database schema & tables
.\services\api\.venv\Scripts\python.exe scripts/apply_staging_migrations.py

# Verify live auth & RLS
.\services\api\.venv\Scripts\python.exe scripts/test_staging_auth_e2e.py

# Verify backend endpoints
.\services\api\.venv\Scripts\python.exe scripts/test_staging_backend_api.py

# Verify AI durable checkpoints
.\services\api\.venv\Scripts\python.exe scripts/verify_ai_persistence.py

# Verify Supabase Realtime WebSocket
.\services\api\.venv\Scripts\python.exe scripts/verify_realtime_staging.py
```

### 4.3 Rebuilding the Mobile Staging Client
```powershell
cd msgi-one/apps/mobile
$env:EXPO_NO_TELEMETRY="1"
npx expo export --platform android
```

---

## 5. Rollback & Disaster Recovery Procedures

1. **Database Rollback:**
   - PostgreSQL schema is strictly additive across migrations `20261118000001` through `20261121000001`.
   - Point-in-time recovery (PITR) is managed through the Supabase Dashboard for project `jndvnbvpwxhfmqgmqxfm`.
   - Per AGENTS.md Rule 13, destructive commands (`DROP TABLE`, `TRUNCATE`) must never be automated.
2. **Backend Rollback:**
   - Revert commit on branch `deploy/staging-hosted` to `d2cccac` (tag `checkpoint/phase-5-handoff`).
3. **Mobile Rollback:**
   - Redeploy the preceding verified bytecode bundle or OTA update via Expo EAS update channel `staging`.

---

## 6. Handoff Sign-Off

All 12 staging documents have been produced, verified against actual terminal evidence, and committed to Git on branch `deploy/staging-hosted`.

The hosted staging system is healthy, fully integrated, and ready for institutional demonstration.
