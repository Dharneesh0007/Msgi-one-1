# MSGI One — Phase 1 Integration Handoff
**Contract, Architecture & State Handoff from Phase 1 to Phase 2**

**Phase:** 1 (Application Foundation) ➔ 2 (Core Data Pipelines & Alumni Directory)  
**Date:** 2026-11-18  
**Repository:** `msgi-one/`  
**Git Checkpoint:** `feat/phase-1-foundation`  

---

## 1. Reusable System Assets Established in Phase 1

Phase 2 engineers and subagents MUST reuse the following core assets without duplicating, replacing, or rewriting them:

### A. Central Database Identity & Schema (`supabase/migrations/`)
- **Canonical Migration:** `supabase/migrations/20261118000001_initial_identity_schema.sql`
- **Identity Entities:**
  - `public.users`: Core identity table keyed to `auth.users(id)`.
  - `public.roles` & `public.user_roles`: Canonical role assignment.
  - `public.alumni_profiles`: Target profile for Phase 2 directory entries.
  - `public.skills` & `public.user_skills`: Standard skill associations.
  - `public.alumni_locations`: Geographic coordinates with `is_public` privacy guard.
- **Rules for Phase 2:**
  - Do NOT create a new `profiles` table.
  - Do NOT create alternative user tables.
  - Any schema expansion for Phase 2 (e.g. pgvector embedding column) must be added as a new timestamped migration: `supabase/migrations/20261119000001_phase_2_directory_and_embeddings.sql`.

### B. Shared Backend Security & RBAC (`services/api/src/core/`)
- **JWT Verification:** `verify_jwt_token(token)` in `src/core/security.py`.
- **Identity Dependency:** `get_current_user` in `src/core/dependencies.py`.
  - Injects `AuthenticatedUser(id, email, first_name, last_name, avatar_url, roles, is_verified, is_active)`.
- **RBAC Guard Factory:** `require_role(allowed_roles: List[str])` in `src/core/dependencies.py`.
  - Example usage for Phase 2 endpoints:
    ```python
    @router.get("/directory/export")
    def export_alumni_directory(
        current_user: AuthenticatedUser = Depends(require_role(["admin", "faculty"]))
    ):
        ...
    ```

### C. Standard API Envelope & Error Handling (`services/api/src/schemas/user.py`)
- Every response in Phase 2 MUST be wrapped in `StandardEnvelope[T]`:
  ```json
  {
    "status": "success",
    "data": { ... },
    "error": null,
    "meta": {},
    "timestamp": "2026-11-18T22:00:00Z"
  }
  ```
- Error responses MUST use standard codes (`ENTITY_NOT_FOUND`, `PERMISSION_DENIED`, `VALIDATION_ERROR`, etc.) and HTTP status codes matching the contract.

### D. Shared Mobile API Client & Auth Context (`apps/mobile/src/`)
- **Mobile API Client:** `import { api } from '@/lib/api';`
  - Automatically injects Bearer JWT from `SecureStore`.
  - Handles timeouts, retries, and unwraps the MSGI envelope.
- **Mobile Auth Context:** `import { useAuth } from '@/context/AuthContext';`
  - Access `user`, `session`, `primaryRole`, `roles`, `isProfileComplete`.
- **Mobile Design Tokens:** `import { Colors, Typography, Spacing } from '@/constants/theme';`
  - Primary Navy `#1A365D`, Gold `#D4AF37`, Slate neutrals.

---

## 2. Phase 2 Scope & Interfaces

Phase 2 will implement **Core Data Pipelines & Alumni Directory**:
1. **Module 1: Alumni Network Directory**
   - Live semantic search over alumni profiles using pgvector embeddings.
   - Filtering by department, graduation year, industry, skills, and verified badges.
   - Public contact masking respecting `is_public` and FERPA privacy settings.
2. **Module 2: Global Alumni Connect**
   - Geolocation search and chapter aggregation.
   - City-level clustering without pinpointing private residential coordinates.
3. **Data Ingestion Pipeline:**
   - Synthetic alumni profile generator and bulk ingestion script adhering strictly to `@example.msgi.edu`.

---

## 3. Strict Boundary Rules for Phase 2

1. **Rule 3 (No Duplicate Systems):** Never create an alternate auth handler or user store.
2. **Rule 7 (No Hardcoded Secrets):** Use `.env` with `SUPABASE_SERVICE_ROLE_KEY` and `OPENAI_API_KEY` for vector embedding generation.
3. **Rule 8 (No Fabricated Real Data):** Seed data for directory testing must be strictly synthetic and labeled `@example.msgi.edu`.
4. **Rule 10 (Verify Everything):** Every Phase 2 endpoint and screen must be validated via terminal tests and curl logs.
5. **Rule 15 (Human in the Loop):** Direct messaging, connection invites, and email notifications require explicit human consent before dispatch.

---

## 4. Verification Checkpoint Before Phase 2 Commencement

Run the automated verification suite at any time to verify baseline health:
```powershell
& "C:\Users\dharneesh\.local\bin\uv.exe" run --offline --no-sync --project msgi-one\services\api python msgi-one\scripts\verify_phase_1.py
& "C:\Users\dharneesh\.local\bin\uv.exe" run --offline --no-sync --project msgi-one\services\api python -m pytest msgi-one\services\api\tests -v
```
Both commands must report **100% PASS** before Phase 2 code is committed.
