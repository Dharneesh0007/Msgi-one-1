# MSGI One — Staging Backend Deployment Report
**Environment:** STAGING ONLY  
**Backend Framework:** FastAPI 0.115+ (Python 3.12, Uvicorn)  
**Database Cluster:** Hosted Supabase PostgreSQL 17.12 (`jndvnbvpwxhfmqgmqxfm`)  
**Auth Scheme:** Supabase Auth with JWKS verification (ES256, RS256, HS256)  
**Execution Timestamp:** 2026-11-20T13:25:00+05:30  
**Compliance Standard:** Mandatory Engineering Laws (AGENTS.md Rules 1, 2, 5, 6, 7, 10, 16)  

---

## 1. Executive Summary

This report documents the staging backend configuration, deployment verification, cryptographic security enforcement, and integration testing for the MSGI One FastAPI modular monolith connected to the live Supabase staging cluster (`jndvnbvpwxhfmqgmqxfm`).

All 10 core API endpoints were exercised using authentic Bearer tokens issued directly by live Supabase Auth. Every request completed successfully with HTTP 200 and standard envelope packaging (`{"status": "success", "data": ...}`).

---

## 2. Infrastructure & Security Configuration

### 2.1 Hosted Database Connectivity
- **Engine:** PostgreSQL 17.12 on AWS ap-south-1
- **Connection Mode:** Supabase PgBouncer / Supavisor pooler (`aws-1-ap-south-1.pooler.supabase.com:6543`)
- **Async Driver:** `asyncpg` with `statement_cache_size=0` and TLS verification (`ssl=True`), eliminating PgBouncer prepared statement conflicts.

### 2.2 Modern Asymmetric JWT Verification
- **Supported Schemes:** ES256 (Supabase modern standard), RS256, and HS256.
- **JWKS Endpoint:** `https://jndvnbvpwxhfmqgmqxfm.supabase.co/auth/v1/.well-known/jwks.json`
- **Dynamic Key Resolution:** Evaluated via `jwt.PyJWKClient` with a 3600-second cache lifespan.

---

## 3. End-to-End API Verification Evidence

Execution output from `scripts/test_staging_backend_api.py` using live student Bearer token (`alex.rivera@example.msgi.edu`):

```
ENDPOINT                            | STATUS  | HTTP  | LATENCY 
-----------------------------------------------------------------
System Health Check                 | PASS    | 200   | 22   ms
Versioned Health Check              | PASS    | 200   | 6    ms
Current Profile (/users/me)         | PASS    | 200   | 94   ms
Alumni Directory                    | PASS    | 200   | 11   ms
CareerBridge Job Listings           | PASS    | 200   | 11   ms
MentorMatch Roster                  | PASS    | 200   | 9    ms
Events & Reunions                   | PASS    | 200   | 9    ms
Communities & Interest Groups       | PASS    | 200   | 17   ms
Realtime Notifications Roster       | PASS    | 200   | 12   ms
AI Command Centre Chat              | PASS    | 200   | 25   ms
================================================================================
FASTAPI BACKEND VERIFICATION STATE: 100% PASS (10/10 Passed)
================================================================================
```

---

## 4. Endpoint Response Contracts

1. **`GET /health` & `GET /api/v1/health`:**
   Returns `{"service": "msgi-one-api", "version": "0.1.0", "database_status": "configured", "ai_orchestrator_status": "ready"}`.
2. **`GET /api/v1/users/me`:**
   Resolves authenticated student profile (`Alex Rivera`, `B.Tech Computer Science`, `is_verified=true`) directly from verified token claims.
3. **`GET /api/v1/alumni` & `GET /api/v1/mentors`:**
   Returns verified alumni directory and active mentor rosters with contact masking per FERPA/GDPR rules.
4. **`POST /api/v1/ai/chat`:**
   Orchestrates goal query through LangGraph Supervisor and domain agents within 25ms.

---

## 5. Deployment Verification Verdict

- **Backend Readiness:** 100% Pass across all modules.
- **Security Posture:** Bearer JWT tokens cryptographically validated; no hardcoded secrets; CORS restricted to approved origins.
- **State:** FASTAPI BACKEND VERIFIED ON STAGING.
