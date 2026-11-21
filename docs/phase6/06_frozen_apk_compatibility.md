# MSGI ONE — FROZEN APK COMPATIBILITY SPECIFICATION (GATE 6.6)
**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** 6 — PostgreSQL Persistence, Async Repository Architecture, and Legacy Android Compatibility  
**Document ID:** `docs/phase6/06_frozen_apk_compatibility.md`  
**Execution Standard:** Executive Engineering Directive v2.0  
**Baseline Artifact ID:** `a95a7169-d48b-4730-bcfd-921500e4b8fae` (Expo SDK 52, Version 0.1.0)  
**Status:** COMPLETE / VERIFIED  

---

## 1. Frozen Android Artifact Baseline Invariant

The standalone signed Android APK `a95a7169-d48b-4730-bcfd-921500e4b8fae` is physically installed on the user's test devices and is frozen as the immutable release baseline.

**Core Directive Constraint:**
- No rebuilding of the APK.
- No modifying `apps/mobile/app.json` or native dependencies.
- Zero breaking changes to the backend HTTP API contracts.

---

## 2. Dual-Prefix Routing Architecture

### 2.1 The Double-Prefix Phenomenon
In the bundled APK configuration:
- `EXPO_PUBLIC_API_URL` is configured as: `https://msgi-one-jpkz.onrender.com/api/v1`
- Mobile API client services in `apps/mobile/src/services/` append `/api/v1/...` to the base URL:
  - e.g. `client.get('/api/v1/alumni')`
- The resulting HTTP request dispatched from the Android device reaches the backend with the path:
  ```text
  /api/v1/api/v1/alumni
  ```

### 2.2 Dual-Prefix Preservation in `main.py`
To guarantee 100% backward compatibility with both the frozen APK (sending `/api/v1/api/v1/...`) and standard REST callers (sending `/api/v1/...`), the FastAPI backend implements a dual-defense mechanism:

1. **ASGI Middleware Normalization (`DoublePrefixNormalizationMiddleware`):**
   ```python
   class DoublePrefixNormalizationMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request: Request, call_next):
           if request.url.path.startswith("/api/v1/api/v1"):
               normalized_path = request.url.path.replace("/api/v1/api/v1", "/api/v1", 1)
               request.scope["path"] = normalized_path
           return await call_next(request)
   ```
2. **Dual APIRouter Inclusion:**
   All routers are mounted twice in `src/main.py`:
   - Primary Mount: `app.include_router(..., prefix="/api/v1")`
   - Compatibility Mount: `app.include_router(..., prefix="/api/v1/api/v1", include_in_schema=False)`

This guarantees that every request succeeds identically regardless of single or double prefix!

---

## 3. Direct Alias Compatibility Endpoints

The mobile profile navigation directly targets `/api/v1/me` and `/api/v1/me/onboard` in addition to `/api/v1/users/me`.
These direct aliases are explicitly wired:
- `GET /api/v1/me` -> resolves current authenticated user profile
- `PATCH /api/v1/me` -> updates personal profile fields
- `POST /api/v1/me/onboard` -> completes initial registration onboarding

---

## 4. Standard Response Envelope Contract

Every response adheres to the immutable `StandardEnvelope[T]` format expected by the mobile response interceptor:
```json
{
  "status": "success",
  "data": { ... },
  "error": null,
  "meta": { ... },
  "timestamp": "2026-11-21T12:00:00.000000Z"
}
```

In the event of an error, the envelope provides the exact structure:
```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Resource was not found.",
    "details": {}
  },
  "meta": {},
  "timestamp": "2026-11-21T12:00:00.000000Z"
}
```

### 4.1 Frozen Error Code Registry
The mobile error handlers switch on specific error code constants:
- `ENTITY_NOT_FOUND` (404)
- `FORBIDDEN_ACTION` / `PERMISSION_DENIED` (403)
- `PROFILE_PRIVATE` (403)
- `DUPLICATE_APPLICATION` / `DUPLICATE_ENROLLMENT` (409)
- `DEADLINE_PASSED` (400)
- `MENTOR_CAPACITY_FULL` (400)
- `VALIDATION_ERROR` (422)

---

## 5. Certification

All legacy contracts, dual prefixes, and response formats are verified intact. The frozen Android APK (`a95a7169-d48b-4730-bcfd-921500e4b8fae`) operates without regressions. Gate 6.6 is formally marked **PASSED**.
