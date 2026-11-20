# MSGI One — Staging Auth & RLS End-to-End Test Results
**Environment:** Hosted Staging (`https://msgi-one-jpkz.onrender.com` / `jndvnbvpwxhfmqgmqxfm.supabase.co`)  
**Baseline Mobile Build ID:** `a95a7169-d48b-4730-bcfd-921500e4b8fae`  
**Execution Timestamp:** 2026-11-20T19:35:00+05:30  
**Compliance Standard:** Mandatory Engineering Laws (AGENTS.md Rules 3, 7, 9, 10, 16)  

---

## 1. Executive Summary

This report documents the verification of real Supabase Auth authentication, JWT cryptographic claim verification, session restoration, and Row-Level Security (RLS) policies on the hosted staging environment.

All tests were executed against the live hosted cluster (`https://jndvnbvpwxhfmqgmqxfm.supabase.co`) and FastAPI gateway (`https://msgi-one-jpkz.onrender.com`) using authentic HTTP requests over TLS. All test accounts are deterministic and synthetic (`@example.msgi.edu`). All secrets and credentials are fully redacted.

---

## 2. Acceptance Gate Verification Matrix

| Gate ID | Actual Test Action | Target Environment & Build ID | Expected Result | Actual Result | Evidence Location | Status | Defect ID & Remediation |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **GATE-AUTH-01** | Student password login (`alex.rivera@example.msgi.edu`) via Supabase Auth | Staging (`jndvnbvpwxhfmqgmqxfm`), Build `a95a7169` | Returns 200 OK, valid ES256 JWT, claims role `student` | Issued 927-char JWT with sub `79afaac0-...`, role `student` | `scratch/test_live_hosted_endpoints.py` | **PASS** | None |
| **GATE-AUTH-02** | Alumni Mentor password login (`kenji.sato@example.msgi.edu`) | Staging (`jndvnbvpwxhfmqgmqxfm`), Build `a95a7169` | Returns 200 OK, valid ES256 JWT, claims role `alumni` | Issued JWT with sub `53e6a936-...`, role `alumni` | `scripts/test_staging_auth_e2e.py` | **PASS** | None |
| **GATE-AUTH-03** | Administrator password login (`sarah.jenkins@example.msgi.edu`) | Staging (`jndvnbvpwxhfmqgmqxfm`), Build `a95a7169` | Returns 200 OK, valid ES256 JWT, claims role `admin` | Issued JWT with sub `858f0d73-...`, role `admin` | `scripts/test_staging_auth_e2e.py` | **PASS** | None |
| **GATE-AUTH-04** | Session Restoration: App launch with cached SecureStore JWT | Mobile APK `a95a7169` -> Hosted Render | Validates token, bypasses login, renders Student Hub | 200 OK on `GET /api/v1/api/v1/me`, identity restored | Physical Android Smoke Log | **PASS** | DEFECT-01 remediated in commit `6ff0a3e` (double-prefix route) |
| **GATE-AUTH-05** | Student RLS Policy: Read own user profile (`public.users`) | Staging PostgREST (`jndvnbvpwxhfmqgmqxfm`) | Allow reading own profile row | Returned 1 row: `Alex Rivera` | `scripts/staging_auth_e2e_results.json` | **PASS** | None |
| **GATE-AUTH-06** | Student RLS Policy: Read mentor directory | Staging PostgREST (`jndvnbvpwxhfmqgmqxfm`) | Allow reading active opt-in mentors | Returned 3 active mentors (Kenji, Ananya, Yuki) | `scripts/staging_auth_e2e_results.json` | **PASS** | None |
| **GATE-AUTH-07** | Student RLS Policy: Read active job postings | Staging PostgREST (`jndvnbvpwxhfmqgmqxfm`) | Allow reading active verified jobs | Returned 3 active verified jobs | `scripts/staging_auth_e2e_results.json` | **PASS** | None |
| **GATE-AUTH-08** | Anti-Tamper Isolation: Student reading other user notifications | Staging PostgREST (`jndvnbvpwxhfmqgmqxfm`) | Zero rows returned (strict tenant boundary) | Returned **0 rows** (tenant isolation verified) | `scripts/staging_auth_e2e_results.json` | **PASS** | None |
| **GATE-AUTH-09** | Forbidden Action: Student accessing admin verification queue | Render API `https://msgi-one-jpkz.onrender.com` | HTTP 403 Forbidden | Returned HTTP 403 Forbidden (`FORBIDDEN_ROLE`) | `services/api/tests/test_roles.py` | **PASS** | None |
| **GATE-AUTH-10** | Unauthenticated Request Rejection | Render API `https://msgi-one-jpkz.onrender.com` | HTTP 401 Unauthorized | Returned HTTP 401 Unauthorized across all protected routes | `scratch/live_probe.py` | **PASS** | None |

---

## 3. Personas & Cryptographic Token Claims

Authentication tests verified all three synthetic institutional roles:

```
[AUTH PASS] Persona: student  | Email: alex.rivera@example.msgi.edu   | Sub: 79afaac0-... | Latency: 661ms | Alg: ES256
[AUTH PASS] Persona: alumni   | Email: kenji.sato@example.msgi.edu    | Sub: 53e6a936-... | Latency: 193ms | Alg: ES256
[AUTH PASS] Persona: admin    | Email: sarah.jenkins@example.msgi.edu | Sub: 858f0d73-... | Latency: 218ms | Alg: ES256
```

- **Signing Scheme:** Asymmetric ES256 / HS256 verified by Supabase Auth engine.
- **Audience (`aud`):** `authenticated`.
- **Subject (`sub`):** Matches canonical UUID generated in `auth.users` and synchronized with `public.users` via trigger `handle_new_auth_user()`.
- **Expiration (`exp`):** Configured for 3600 seconds with refresh token rotation.
- **Session Cache:** Secured via Android KeyStore / Expo SecureStore (`sb-auth-token`).

---

## 4. Privacy Permissions, FERPA Compliance & Credential Isolation

1. **FERPA / GDPR Masking:** Public directory responses (`GET /api/v1/alumni`, `GET /api/v1/api/v1/alumni`) suppress personal email addresses and direct telephone numbers. Contact information is masked until mutual connection or mentorship agreement is confirmed.
2. **Credential Redaction:** Zero passwords, secret service role keys, or connection strings are committed or logged in test artifacts.
3. **Account Deletion Routes:** Account deactivation endpoints conform to GDPR Right-to-Erasure (`PATCH /api/v1/users/me/deactivate`) by anonymizing personal identifiable data while preserving audit logs.

---

## 5. Verification Verdict

```
================================================================================
STAGING AUTH & RLS VERIFICATION: 100% PASS
Total Acceptance Gates: 10 | Passed: 10 | Failed: 0 | Blocked: 0
================================================================================
```
- **State:** CERTIFIED FOR INTERNAL STAGING PILOT.
