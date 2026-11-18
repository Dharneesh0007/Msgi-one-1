# MSGI One — Phase 0 Architectural Corrections & Alignments

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Document:** `docs/PHASE_0_CORRECTIONS.md`  
**Phase:** Transition from Phase 0 to Phase 1  
**Author:** Senior Full-Stack Engineer, Mobile Engineer, Database Architect, Security Engineer & QA Lead  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Executive Summary

Prior to initiating Phase 1 implementation, an architectural review identified 8 specific alignment requirements in the Phase 0 documentation. This document formally records the engineering rationale and resolutions for each item, grounding all decisions in the established engineering principles of **Pressman & Maxim**, **Silberschatz et al.**, **Kleppmann**, **Sommerville**, and **Eric Evans**.

These corrections are codified into the repository architecture and supersede conflicting statements in prior draft documents.

---

## 2. The Eight Architectural Corrections

### Correction 1: Canonical Migration System (Supabase SQL Migrations over Alembic)
- **Problem Statement:** Phase 0 draft referenced Alembic migration commands (`alembic upgrade head`, `alembic downgrade base`) while simultaneously defining Supabase SQL migrations. Having two competing migration authorities risks schema drift and split-brain DDL execution.
- **Engineering Principle:** **Martin Kleppmann** (*Designing Data-Intensive Applications*, Ch. 11) — Single Source of Truth. Relational databases must have exactly one authoritative migration sequence tracked in version control.
- **Resolution:**
  1. **Canonical Migration Authority:** Supabase CLI timestamped SQL migrations (`supabase/migrations/<YYYYMMDDHHMMSS>_*.sql`) are the sole authoritative migration mechanism.
  2. **SQLAlchemy Role:** SQLAlchemy 2.0 is used purely as an Async ORM and query builder for FastAPI, mapping declaratively to the existing database tables.
  3. **Rollback Strategy:** Reversible SQL down-migrations or forward compensating migrations managed via Supabase CLI. All documentation references to Alembic rollbacks are removed.

---

### Correction 2: Prevention of Role Self-Assignment & Principle of Least Privilege
- **Problem Statement:** Registration screens must not allow users to grant themselves privileged roles (`admin`, `faculty`, `recruiter`, `verified_alumni`) simply by selecting an option in a mobile dropdown form.
- **Engineering Principle:** **Roger S. Pressman** (*Software Engineering*, Ch. 9) — Principle of Least Privilege and Complete Mediation. Access rights must be granted only through verifiable institutional authorization gates.
- **Resolution:**
  1. **Requested Role vs Assigned Role:** The registration payload accepts `requested_role` solely as intent metadata.
  2. **Default Least-Privilege Role:** Every newly registered user is granted the default base role (`student` or unverified member) in `public.user_roles`.
  3. **Privileged Role Gates:**
     - `admin`: Can **never** be self-assigned or requested via registration. Provisioned exclusively via database seed or by an existing institutional super-administrator.
     - `alumni`: Created with `users.is_verified = FALSE` and `alumni_profiles.visibility = 'private'` until verified by institutional registrar records.
     - `faculty`: Requires institutional academic email verification and administrator approval.
     - `recruiter`: Requires corporate email confirmation and placement office approval (`recruiter_profiles.verification_status = 'pending'`).

---

### Correction 3: Flexible JWT Algorithm Verification (HS256 and RS256 Support)
- **Problem Statement:** Phase 0 assumed all Supabase projects sign JWTs with asymmetric `RS256` keys via JWKS. In standard Supabase configurations, access tokens are frequently signed with symmetric HMAC-SHA256 (`HS256`) using the project's `JWT_SECRET`. Hardcoding RS256 causes authentication rejection if the project uses HS256.
- **Engineering Principle:** **Ian Sommerville** (*Software Engineering*, Ch. 7) — Robust Interface Design. Security middleware must support valid provider configuration schemes while strictly disallowing insecure fallbacks (e.g., `none` algorithm).
- **Resolution:**
  1. **Dual-Mode Cryptographic Verification:** FastAPI auth dependency inspects the token header `alg`.
  2. If `alg == "HS256"`: Verifies signature using `SUPABASE_JWT_SECRET`.
  3. If `alg == "RS256"`: Verifies signature against Supabase JWKS endpoint (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`).
  4. **Strict Rejection:** Any token specifying `alg == "none"` or unapproved algorithms is rejected with HTTP 401 Unauthorized.
  5. **Standard Claim Validation:** Cryptographically validates `exp` (expiration), `iss` (`{SUPABASE_URL}/auth/v1`), `aud` (`authenticated`), and derives identity exclusively from `sub` (user UUID).

---

### Correction 4: Safe, Idempotent User Bootstrap & Profile Onboarding
- **Problem Statement:** If `first_name` and `last_name` in `public.users` are `NOT NULL`, a database trigger syncing from `auth.users` on sign-up would fail if the user registered with email and password alone, or would require inventing fabricated placeholder names (violating AGENTS.md Rule 8).
- **Engineering Principle:** **Eric Evans** (*Domain-Driven Design*, Ch. 4) — Domain Entity Lifecycle. Entities must transition cleanly from uninitialized to complete states without violating domain integrity.
- **Resolution:**
  1. **Schema Nullability:** In `public.users`, `first_name` and `last_name` are declared as `VARCHAR(100) NULL` during initial account creation.
  2. **Idempotent Database Trigger:** A PostgreSQL trigger (`on_auth_user_created`) automatically inserts a corresponding row into `public.users(id, email, is_verified, is_active)` when a user registers in `auth.users`, ensuring `auth.users.id = public.users.id`.
  3. **Two-Stage Onboarding Flow:**
     - Stage 1 (Auth): User registers with email/password.
     - Stage 2 (Onboarding): Upon first login, mobile app checks `user.first_name IS NULL`. If null, redirects to `/(auth)/complete-profile` where user enters their authentic first name, last name, and department.

---

### Correction 5: Privacy by Default for Geolocation and Profile Contact Details
- **Problem Statement:** In Phase 0 draft, `alumni_locations.is_public` defaulted to `TRUE`. This presents a privacy risk under FERPA and GDPR by exposing geolocation without explicit opt-in.
- **Engineering Principle:** Privacy by Design and Data Minimization (FERPA, GDPR Article 25). Private personal data must remain unexposed until explicit affirmative consent is logged.
- **Resolution:**
  1. **Default Private Geolocation:** `alumni_locations.is_public` defaults to `FALSE`.
  2. **Explicit Consent Gate:** Location coordinates appear on the Global Alumni Connect map only if the user has an active record in `public.consent_records` where `consent_type = 'location_sharing'` and `granted = TRUE`.
  3. **Contact Privacy:** Personal email and phone numbers are never returned in public directory listings (`GET /api/v1/alumni`). Only full name, graduation year, degree, headline, and current company are displayed.

---

### Correction 6: Official Expo SDK 52 & Expo Router v4 Alignment
- **Problem Statement:** Expo SDK dependencies must strictly match the officially supported matrix to avoid runtime Metro bundler crashes and package resolution failures on Android.
- **Engineering Principle:** **Roger S. Pressman** (*Software Engineering*, Ch. 12) — Configuration and Dependency Management. Mobile toolchains require strict semantic peer dependency alignment.
- **Resolution:**
  1. **Validated Dependency Matrix:**
     - `expo`: `~52.0.0`
     - `react-native`: `0.76.5`
     - `react`: `18.3.1`
     - `expo-router`: `~4.0.0`
     - `@supabase/supabase-js`: `^2.47.0`
     - `expo-secure-store`: `~14.0.0`
  2. **Expo Config Plugins:** Configured in `app.json` for `expo-router` and `expo-secure-store` to support native Android compilation without manual `build.gradle` modifications.

---

### Correction 7: Windows-Compatible Android Build Strategy (EAS Cloud Builds)
- **Problem Statement:** Phase 0 draft included commands for `eas build --local`. On Windows hosts without a dedicated Linux WSL2 Android SDK toolchain, local EAS compilation frequently fails due to path delimiter and shell environment incompatibilities.
- **Engineering Principle:** **Ian Sommerville** (*Software Engineering*, Ch. 10) — Continuous Delivery & Build Reproducibility. Build pipelines must execute in clean, containerized, platform-native environments.
- **Resolution:**
  1. **Primary Distribution Strategy:** **Expo Application Services (EAS) Cloud Build** (`npx eas-cli build --platform android --profile preview`). Cloud builders compile the native Android package (`.apk` or `.aab`) in an official Linux container.
  2. **Development Testing Strategy:** Expo Go and local development client (`npx expo start --android`) for rapid iteration on connected Android devices or emulators.

---

### Correction 8: MSGI One Standard API Envelope Specification
- **Problem Statement:** Phase 0 draft referred to error responses as "RFC 7807 aligned" while nesting them within an outer envelope `{ status, data, error, timestamp }`. True RFC 7807 (`application/problem+json`) defines root-level fields (`type`, `title`, `status`, `detail`). Combining the two labels caused ambiguity in contract testing.
- **Engineering Principle:** **Roger S. Pressman** (*Software Engineering*, Ch. 11) — Interface Uniformity. API contracts must have an unambiguous, predictable structure across all success and error conditions.
- **Resolution:**
  1. **Standard Envelope Definition:** The canonical envelope is designated as the **MSGI One Standard API Envelope**:
     - **Success:**
       ```json
       {
         "status": "success",
         "data": { ... },
         "error": null,
         "meta": { ... },
         "timestamp": "2026-11-18T18:00:00Z"
       }
       ```
     - **Error:**
       ```json
       {
         "status": "error",
         "data": null,
         "error": {
           "code": "ENTITY_NOT_FOUND",
           "message": "Human-readable explanation of error.",
           "details": [
             { "field": "email", "issue": "Email format is invalid." }
           ]
         },
         "meta": {},
         "timestamp": "2026-11-18T18:00:00Z"
       }
       ```
  2. **RFC 7807 Alignment:** The inner `error` object provides structured problem details (`code`, `message`, `details`), while the outer envelope guarantees uniform payload parsing for mobile clients.

---

## 3. Approval Sign-Off

All 8 architectural corrections are formally accepted and incorporated into the Phase 1 implementation baseline.
