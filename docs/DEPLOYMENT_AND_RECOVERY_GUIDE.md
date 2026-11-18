# MSGI ONE — DEPLOYMENT, RECOVERY & RUNBOOK GUIDE

**Document Reference:** `docs/DEPLOYMENT_AND_RECOVERY_GUIDE.md`  
**Stack Components:** FastAPI 0.115, Supabase PostgreSQL 15, LangGraph 0.2, Expo SDK 52  
**Target Environments:** Local Development, Docker Staging, Supabase Cloud Production  

---

## 1. REPRODUCIBLE LOCAL & STAGING SETUP

### 1.1 Prerequisites
- **Python:** 3.12+ managed with `uv`
- **Node.js:** 20+ with `npm` or `pnpm`
- **Expo CLI:** EAS CLI (`npm install -g eas-cli`)

### 1.2 Backend Deployment (FastAPI)
```bash
# Clone and enter backend directory
cd msgi-one/services/api

# Sync dependencies with uv
uv sync

# Run database migrations against local or staging database
# (Optional if using in-memory / SQLite durable checkpointer)
uv run python -m src.db.migrate

# Start FastAPI development server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 1.3 Database Migration & Ingestion Runbook
```bash
# 1. Apply Supabase Migrations in sequence:
#    supabase/migrations/20261118000001_initial_schema.sql
#    supabase/migrations/20261119000001_phase_2_business_modules.sql
#    supabase/migrations/20261120000001_phase_3_agentic_ai.sql
#    supabase/migrations/20261121000001_phase_4_extended_modules.sql

# 2. Ingest Synthetic Deterministic Data (Demo Mode):
cd msgi-one
uv run --project services/api python scripts/import_synthetic_data.py --mode demo

# 3. Dry-Run Validation:
uv run --project services/api python scripts/import_synthetic_data.py --dry-run
```

---

## 2. ANDROID RELEASE & EAS BUILD INSTRUCTIONS

### 2.1 Internal Preview Build (Standalone APK for Device Testing)
```bash
cd msgi-one/apps/mobile

# Build standalone APK for physical device testing
eas build --platform android --profile preview
```

### 2.2 Production App Bundle (.aab for Google Play Store)
```bash
cd msgi-one/apps/mobile

# Configure production keystore and build Google Play bundle
eas build --platform android --profile production
```

*Note on Google Play Target SDK:* Before submitting to the public Google Play Store tracks, ensure `targetSdkVersion` is updated to API 36+ by upgrading to Expo SDK 53+ or configuring a custom Gradle build plugin.

---

## 3. DISASTER RECOVERY & ROLLBACK RUNBOOK

### 3.1 Database Rollback Procedure
If a database migration causes schema incompatibility:
1. Revert to the last verified snapshot tag: `checkpoint/phase-4-handoff`.
2. Inspect the migration diff in `supabase/migrations/`.
3. Migrations in MSGI One are strictly additive; if a table entity must be dropped in an emergency, execute rollback SQL explicitly:
   ```sql
   -- Emergency rollback example
   DROP TABLE IF EXISTS public.notifications CASCADE;
   ```
4. Re-run `scripts/import_synthetic_data.py` to restore clean seed data.

### 3.2 AI Checkpointer State Recovery
If an AI agent workflow crashes or the backend process restarts during an active multi-agent conversation:
- All thread states, message histories, and pending human approvals are automatically recovered from `services/api/checkpoints.sqlite` (or `PostgresSaver` in production).
- The client resumes the conversation by re-issuing `POST /api/v1/ai/dispatch` with the original `session_id`.
- Thread isolation ensures no user can ever access another user's execution checkpoint.

---

## 4. VERIFICATION COMMANDS

To run the complete system verification suite:
```bash
cd msgi-one
uv run --offline --no-sync --project services/api python scripts/verify_phase_5.py
```
Expected output: All 4 offline verification gates PASS in under 6 seconds.
