# MSGI One — Phase 1 Test Results & Verification Evidence
**Evidence-Based Quality Assurance & Verification Report**

**Phase:** 1 of 5 (Application Foundation)  
**Date:** 2026-11-18  
**Operating System:** Windows (PowerShell 7.x)  
**Python Runtime:** CPython 3.12.13 (Managed via uv)  
**Node.js Runtime:** v24.21.0  
**Test Framework:** pytest-9.2.0, anyio-4.16.0  
**Overall Result:** 18/18 Unit Tests PASSED (100%), 7/7 System Checks PASSED (100%)  

---

## 1. Automated Unit Test Execution Evidence

### Command Executed:
```powershell
& "C:\Users\dharneesh\.local\bin\uv.exe" run --offline --no-sync --project msgi-one\services\api python -m pytest msgi-one\services\api\tests -v
```

### Execution Terminal Log:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\dharneesh\OneDrive\Documents\msgi-one\services\api\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\dharneesh\OneDrive\Documents\msgi-one\services\api
configfile: pyproject.toml
plugins: anyio-4.16.0
collecting ... collected 18 items

msgi-one\services\api\tests\test_health.py::test_health_check_returns_success_envelope PASSED [  5%]
msgi-one\services\api\tests\test_health.py::test_root_endpoint_returns_documentation_links PASSED [ 11%]
msgi-one\services\api\tests\test_profiles.py::test_user_update_request_forbids_role_modification PASSED [ 16%]
msgi-one\services\api\tests\test_profiles.py::test_user_update_request_accepts_valid_fields PASSED [ 22%]
msgi-one\services\api\tests\test_profiles.py::test_get_my_profile_returns_envelope PASSED [ 27%]
msgi-one\services\api\tests\test_profiles.py::test_update_my_profile_persists_changes PASSED [ 33%]
msgi-one\services\api\tests\test_profiles.py::test_complete_onboarding PASSED [ 38%]
msgi-one\services\api\tests\test_profiles.py::test_public_user_profile_masks_sensitive_data PASSED [ 44%]
msgi-one\services\api\tests\test_roles.py::test_student_cannot_access_admin_endpoint PASSED [ 50%]
msgi-one\services\api\tests\test_roles.py::test_admin_can_access_admin_endpoint PASSED [ 55%]
msgi-one\services\api\tests\test_roles.py::test_multi_role_matching PASSED [ 61%]
msgi-one\services\api\tests\test_roles.py::test_recruiter_cannot_access_faculty_endpoint PASSED [ 66%]
msgi-one\services\api\tests\test_security.py::test_valid_hs256_token_verifies_successfully PASSED [ 72%]
msgi-one\services\api\tests\test_security.py::test_expired_token_raises_401 PASSED [ 77%]
msgi-one\services\api\tests\test_security.py::test_tampered_signature_raises_401 PASSED [ 83%]
msgi-one\services\api\tests\test_security.py::test_prohibited_none_algorithm_raises_401 PASSED [ 88%]
msgi-one\services\api\tests\test_security.py::test_invalid_audience_raises_401 PASSED [ 94%]
msgi-one\services\api\tests\test_security.py::test_empty_token_raises_401 PASSED [100%]

======================== 18 passed, 1 warning in 0.47s ========================
```

---

## 2. System Verification Suite Evidence

### Command Executed:
```powershell
& "C:\Users\dharneesh\.local\bin\uv.exe" run --offline --no-sync --project msgi-one\services\api python msgi-one\scripts\verify_phase_1.py
```

### Execution Terminal Log:
```text
================================================================================
MSGI ONE — PHASE 1 SYSTEM VERIFICATION SUITE
================================================================================
[PASS] Database Migration 20261118000001 - Verified 3NF tables, idempotent trigger, and RLS policies.
[PASS] Synthetic Seed Fixtures - All emails labeled @example.msgi.edu.
[PASS] JWT Dual HS256/RS256 Security - Validates audience, expiry, rejects 'none'.
[PASS] Server-Side RBAC Guard - Enforces least privilege; rejects 403.
[PASS] Schema Strict Validation - Forbids extra fields ('role', 'is_verified') in UserUpdateRequest.
[PASS] User Profile & Envelope API - Standard envelope returned; contact masked.
[PASS] Mobile Navigation & Screens - All 15 screens and modules verified present.

================================================================================
VERIFICATION SUMMARY: 7/7 PASSED (0 FAILED)
================================================================================
```

---

## 3. Detailed Test Case Matrix

| ID | Test Category | Target Functionality | Input / Condition | Expected Behavior | Actual Result |
|:---|:---|:---|:---|:---|:---:|
| TC-01 | Health API | `/health` endpoint | Direct GET invocation | 200 OK, `{ status: "success", data: { status: "healthy" } }` | **PASS** |
| TC-02 | Documentation API | `/` root endpoint | Direct GET invocation | 200 OK with documentation URLs and version | **PASS** |
| TC-03 | Security - RBAC | Privileged Access | User with role `['student']` calling admin endpoint | HTTP 403 Forbidden with `code: "PERMISSION_DENIED"` | **PASS** |
| TC-04 | Security - RBAC | Admin Access | User with role `['admin']` calling admin endpoint | Allowed through dependency; user object returned | **PASS** |
| TC-05 | Security - RBAC | Multi-Role Matching | User with role `['alumni']` calling `['faculty', 'alumni']` | Allowed through dependency | **PASS** |
| TC-06 | Security - RBAC | Recruiter Boundary | Recruiter requesting faculty resource | HTTP 403 Forbidden with `code: "PERMISSION_DENIED"` | **PASS** |
| TC-07 | Security - JWT | Valid Token Verification | Valid HS256 signed token with audience `authenticated` | Signature verified; subject and claims decoded | **PASS** |
| TC-08 | Security - JWT | Expiration Enforcement | Expired JWT (`exp` in the past) | HTTP 401 Unauthorized with `code: "TOKEN_EXPIRED"` | **PASS** |
| TC-09 | Security - JWT | Tampered Signature | Altered signature bytes on valid payload | HTTP 401 Unauthorized with `code: "INVALID_SIGNATURE"` | **PASS** |
| TC-10 | Security - JWT | Insecure Algorithm Rejection | Token encoded with algorithm `none` | HTTP 401 Unauthorized with `code: "ALGORITHM_MISMATCH"` | **PASS** |
| TC-11 | Security - JWT | Audience Verification | Token issued for invalid audience | HTTP 401 Unauthorized with `code: "INVALID_AUDIENCE"` | **PASS** |
| TC-12 | Security - JWT | Empty Token Rejection | Empty string passed to verification engine | HTTP 401 Unauthorized with `code: "INVALID_TOKEN"` | **PASS** |
| TC-13 | Schema Validation | Role Tampering Protection | Payload containing unexpected `role="admin"` | Pydantic `ValidationError` raised; `extra="forbid"` | **PASS** |
| TC-14 | Schema Validation | Field Acceptance | Valid `first_name`, `last_name`, `avatar_url` | Validates successfully without mutation | **PASS** |
| TC-15 | User Profiles | Full Profile Retrieval | `get_my_profile()` with authenticated context | MSGI Standard Envelope with role & completion state | **PASS** |
| TC-16 | User Profiles | Profile Modification | `update_my_profile()` updating permitted names | Updates applied; refreshed profile returned in envelope | **PASS** |
| TC-17 | Onboarding | Two-Stage Onboarding | `complete_onboarding()` submitting name & dept | Profile updated; `is_profile_complete = true` | **PASS** |
| TC-18 | Privacy & Compliance | Public Directory Masking | `get_public_user_profile()` on alumni member | Direct email & phone masked; public headline shown | **PASS** |

---

## 4. Verification of the 8 Phase 0 Resolutions

1. **Migration System Conflict:** Verified that `supabase/migrations/20261118000001_initial_identity_schema.sql` is the canonical schema owner. Alembic was safely uninstalled and omitted.
2. **Role Self-Assignment:** Verified that client registration only records `requested_role`. The database trigger sets the initial active role to `student`. Privileged role switches require administrative verification.
3. **JWT Verification Engine:** Verified support for both `HS256` and `RS256` key verification, rejecting unapproved algorithms.
4. **User Bootstrap & Onboarding:** Two-stage onboarding implemented without fabricating dummy names. `first_name` and `last_name` default to `NULL` until submitted via `/api/v1/users/me/onboard`.
5. **Privacy & Consent:** Geolocation sharing in `alumni_locations` defaults to `is_public = FALSE`. Public user profile endpoint masks email and phone numbers.
6. **Expo SDK 52 Compatibility:** Project configuration pinned to Expo SDK 52, React Native 0.76.5, and Expo Router v4.
7. **Windows Android Build Strategy:** EAS Cloud Build configured in `app.json` rather than relying on unsupported local Windows containers.
8. **Standard Envelope Contract:** All REST endpoints return `{ status, data, error, meta, timestamp }` with standardized error schemas.

---

## 5. QA Lead Sign-Off

All tests and security validations have been executed in the actual terminal environment and passed with zero regressions. Phase 1 is certified ready for Phase 2 integration.
