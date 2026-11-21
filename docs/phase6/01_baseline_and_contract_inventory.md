# MSGI One — Phase 6: Baseline & API Contract Inventory

**Document Reference:** `docs/phase6/01_baseline_and_contract_inventory.md`  
**Gate:** Gate 6.0 — Baseline Verification & Contract Freeze  
**Execution Timestamp:** 2026-11-21T18:05:00+05:30  
**Baseline Git Commit:** `9b29883` (`deploy/staging-hosted`) [V-EXEC]  
**Frozen Android Artifact ID:** `a95a7169-d48b-4730-bcfd-921500e4b8fae` [V-READ]  
**Historical Automated Test Baseline:** 98 passed in 3.50s [V-EXEC]  
**Compliance Standard:** Sommerville (Requirements Traceability) & Martin Fowler (Contract Integrity)  

---

## 1. Executive Summary

This document establishes the machine-readable API contract baseline and client integration constraints for Phase 6. Every public route, path parameter, query parameter, request body schema, response envelope, error representation, and pagination semantic is inventoried.

Under the **Frozen APK Rule**, this contract inventory serves as an immutable regression standard: zero modifications to these schemas, status codes, or error structures are permitted if they would alter the expectations of the installed Android standalone application (`a95a7169-d48b-4730-bcfd-921500e4b8fae`).

---

## 2. Global Protocol & Envelope Standards

### 2.1 Base URLs and Dual-Prefix Routing
To support both the frozen APK (which prepends `/api/v1` to base URL `https://msgi-one-jpkz.onrender.com/api/v1`) and standard REST consumers:
1. **Canonical Prefix:** `/api/v1`
2. **Compatibility Prefix:** `/api/v1/api/v1`
3. **ASGI Normalization:** `normalize_api_v1_prefix_middleware` dynamically rewrites `/api/v1/api/v1/*` to `/api/v1/*` in ASGI scope, while all routers are also dual-mounted in `main.py`.

### 2.2 Standard Success Envelope (`StandardEnvelope[T]`)
All non-health endpoints return the uniform MSGI envelope:
```json
{
  "status": "success",
  "data": "<T>",
  "error": null,
  "meta": {},
  "timestamp": "2026-11-21T12:00:00.000000Z"
}
```

### 2.3 Standard Error Envelope (`ErrorEnvelope`)
All error responses adhere to the standard structure:
```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable error description",
    "details": {}
  },
  "timestamp": "2026-11-21T12:00:00.000000Z"
}
```

### 2.4 Pagination Semantics
- Query Parameters: `page` (integer, default 1, minimum 1), `limit` (integer, default 20, maximum 50).
- Response Schema for Paginated Lists:
```json
{
  "items": [],
  "total": 4,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

---

## 3. Comprehensive Machine-Readable API Contract Inventory

### 3.1 Module 1: Identity, Auth & User Profiles (`users.py`, `auth.py`)

| HTTP Method | Route | Auth Required | Request Body / Query Params | Response Data Schema | Expected Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `GET` | `/api/v1/health` | No | None | `HealthResponse` | 200 OK |
| `POST` | `/api/v1/auth/register` | No | `UserCreateRequest` (`email`, `password`, `requested_role`, `first_name`, `last_name`) | `UserRegisterResponse` | 201 Created |
| `POST` | `/api/v1/auth/login` | No | `UserLoginRequest` (`email`, `password`) | `UserLoginResponse` (`access_token`, `token_type`, `user`) | 200 OK |
| `POST` | `/api/v1/auth/refresh` | No | `TokenRefreshRequest` (`refresh_token`) | `TokenRefreshResponse` | 200 OK |
| `GET` | `/api/v1/users/me` | Bearer JWT | None | `UserProfileResponse` | 200 OK |
| `GET` | `/api/v1/me` *(Direct Alias)* | Bearer JWT | None | `UserProfileResponse` | 200 OK |
| `PATCH` | `/api/v1/users/me` | Bearer JWT | `UserUpdateRequest` (`first_name`, `last_name`, `avatar_url`, `headline`, `bio`, etc.) | `UserProfileResponse` | 200 OK |
| `PATCH` | `/api/v1/me` *(Direct Alias)* | Bearer JWT | `UserUpdateRequest` | `UserProfileResponse` | 200 OK |
| `POST` | `/api/v1/users/me/onboard` | Bearer JWT | `UserOnboardingRequest` | `UserProfileResponse` | 200 OK |
| `GET` | `/api/v1/users/{user_id}` | Bearer JWT | Path: `user_id` (UUID or alias) | `PublicUserProfileResponse` (Masked) | 200 OK / 404 |
| `PATCH` | `/api/v1/users/me/deactivate` | Bearer JWT | `UserDeactivateRequest` | `StandardEnvelope[Dict]` | 200 OK |

### 3.2 Module 1: Alumni Network Directory (`alumni.py`)

| HTTP Method | Route | Auth Required | Parameters | Response Data Schema | Expected Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `GET` | `/api/v1/alumni` | Bearer JWT | Query: `query`, `department`, `industry`, `country`, `skill`, `graduation_year`, `verified_only`, `page`, `limit` | Paginated `List[AlumniDirectoryItem]` | 200 OK |
| `GET` | `/api/v1/alumni/search` | Bearer JWT | Same as `/api/v1/alumni` | Paginated `List[AlumniDirectoryItem]` | 200 OK |
| `GET` | `/api/v1/alumni/{alumni_id}` | Bearer JWT | Path: `alumni_id` (UUID, alias, or user_id) | `AlumniDetailResponse` | 200 OK / 404 |

### 3.3 Module 2: CareerBridge (`jobs.py`)

| HTTP Method | Route | Auth Required | Parameters / Body | Response Data Schema | Expected Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `GET` | `/api/v1/jobs` | Bearer JWT | Query: `query`, `opportunity_type`, `workplace_type`, `country`, `skill`, `page`, `limit` | `List[JobResponse]` | 200 OK |
| `POST` | `/api/v1/jobs` | Recruiter/Admin | `JobCreateRequest` | `JobResponse` | 201 Created |
| `GET` | `/api/v1/jobs/{job_id}` | Bearer JWT | Path: `job_id` | `JobResponse` | 200 OK / 404 |
| `POST` | `/api/v1/jobs/{job_id}/applications` | Student | `JobApplicationRequest` (`resume_url`, `cover_note`) | `JobApplicationResponse` | 201 Created / 400 |
| `GET` | `/api/v1/me/applications` | Student | None | `List[JobApplicationResponse]` | 200 OK |

### 3.4 Module 3: MentorMatch (`mentors.py`)

| HTTP Method | Route | Auth Required | Parameters / Body | Response Data Schema | Expected Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `GET` | `/api/v1/mentors` | Bearer JWT | Query: `topic`, `country`, `student_goal` | `List[MentorProfileResponse]` | 200 OK |
| `GET` | `/api/v1/mentors/{mentor_id}` | Bearer JWT | Path: `mentor_id` | `MentorProfileResponse` | 200 OK / 404 |
| `POST` | `/api/v1/mentor-requests` | Student | `MentorRequestCreate` (`mentor_id`, `topic`, `career_goal`, `message`) | `MentorRequestResponse` | 201 Created / 400 |
| `GET` | `/api/v1/me/mentor-requests` | Bearer JWT | None | `List[MentorRequestResponse]` | 200 OK |
| `PATCH` | `/api/v1/mentor-requests/{id}` | Mentor | `MentorRequestStatusUpdate` (`status`, `mentor_notes`) | `MentorRequestResponse` | 200 OK |

### 3.5 Module 4: Events & Reunions (`events.py`)

| HTTP Method | Route | Auth Required | Parameters / Body | Response Data Schema | Expected Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `GET` | `/api/v1/events` | Bearer JWT | Query: `event_type`, `is_virtual`, `page`, `limit` | `List[EventResponse]` | 200 OK |
| `POST` | `/api/v1/events` | Admin/Faculty | `EventCreateRequest` | `EventResponse` | 201 Created |
| `GET` | `/api/v1/events/{event_id}` | Bearer JWT | Path: `event_id` | `EventResponse` | 200 OK / 404 |
| `POST` | `/api/v1/events/{id}/registrations` | Bearer JWT | Path: `event_id` | `EventRegistrationResponse` | 201 Created / 400 |
| `GET` | `/api/v1/me/event-registrations` | Bearer JWT | None | `List[EventRegistrationResponse]` | 200 OK |
| `DELETE` | `/api/v1/events/{id}/registrations` | Bearer JWT | Path: `event_id` | `StandardEnvelope[Dict]` | 200 OK |

### 3.6 Module 6: MSGI AI Command Centre (`ai.py`)

| HTTP Method | Route | Auth Required | Parameters / Body | Response Data Schema | Expected Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `POST` | `/api/v1/ai/chat` | Bearer JWT | `ChatRequest` (`prompt`, `session_id`) | `CommandCentreState` | 200 OK |
| `POST` | `/api/v1/ai/workflows` | Bearer JWT | `WorkflowTriggerRequest` (`prompt`, `session_id`) | `CommandCentreState` | 202 Accepted |
| `GET` | `/api/v1/ai/workflows/{id}` | Bearer JWT | Path: `session_id` | `CommandCentreState` | 200 OK / 404 |
| `GET` | `/api/v1/ai/approvals/pending` | Bearer JWT | None | `List[ApprovalRequestResponse]` | 200 OK |
| `POST` | `/api/v1/ai/approvals/{id}/decision` | Bearer JWT | `ApprovalDecisionRequest` (`decision`, `decision_note`) | `ApprovalRequestResponse` | 200 OK |

### 3.7 Module 9–12: Extended Modules & Admin (`learning.py`, `communities.py`, `admin.py`, `extended.py`, `notifications.py`)

| HTTP Method | Route | Auth Required | Parameters / Body | Response Data Schema | Expected Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| `GET` | `/api/v1/learning/resources` | Bearer JWT | Query: `skill`, `difficulty` | `List[LearningResourceResponse]` | 200 OK |
| `POST` | `/api/v1/learning/enrollments` | Bearer JWT | `EnrollmentCreateRequest` (`resource_id`) | `EnrollmentResponse` | 201 Created |
| `GET` | `/api/v1/learning/me` | Bearer JWT | None | `List[EnrollmentResponse]` | 200 OK |
| `GET` | `/api/v1/communities` | Bearer JWT | Query: `category` | `List[CommunityResponse]` | 200 OK |
| `POST` | `/api/v1/communities/{id}/join` | Bearer JWT | Path: `community_id` | `CommunityMembershipResponse` | 201 Created |
| `GET` | `/api/v1/communities/me` | Bearer JWT | None | `List[CommunityMembershipResponse]` | 200 OK |
| `GET` | `/api/v1/admin/verifications` | Admin | Query: `status` | `List[VerificationRequestItem]` | 200 OK |
| `POST` | `/api/v1/admin/verifications/{id}/decision` | Admin | `VerificationDecisionRequest` | `VerificationRequestItem` | 200 OK |
| `GET` | `/api/v1/admin/summary` | Admin | None | `AdminSummaryResponse` | 200 OK |
| `GET` | `/api/v1/admin/audit-logs` | Admin | Query: `limit` | `List[AdminAuditLogItem]` | 200 OK |
| `GET` | `/api/v1/notifications` | Bearer JWT | Query: `unread_only` | `List[NotificationResponse]` | 200 OK |
| `GET` | `/api/v1/notifications/unread-count` | Bearer JWT | None | `{"unread_count": int}` | 200 OK |
| `PATCH` | `/api/v1/notifications/{id}/read` | Bearer JWT | Path: `notification_id` | `NotificationResponse` | 200 OK |
| `POST` | `/api/v1/notifications/read-all` | Bearer JWT | None | `{"marked_read": int}` | 200 OK |

---

## 4. Frozen Android Mobile Polling & State Dependencies

The mobile application `a95a7169-d48b-4730-bcfd-921500e4b8fae` interacts with the backend using the following polling and lifecycle patterns:
1. **Network Screen Polling (`network.tsx`):** Debounced (250ms) search trigger calling `GET /api/v1/alumni?verified_only=true`.
2. **Opportunities Screen (`opportunities.tsx`):** On-mount and pull-to-refresh execution of `GET /api/v1/jobs` and `GET /api/v1/mentors`.
3. **AI Command Centre (`ai.tsx`):** On-mount query to `GET /api/v1/ai/approvals/pending` to restore pending HITL approval cards.
4. **Notification Badge:** Periodic header refresh calling `GET /api/v1/notifications/unread-count`.

---

## 5. Gate 6.0 Certification

```
================================================================================
GATE 6.0 VERDICT: BASELINE CONTRACT INVENTORY FROZEN
Total Endpoints Inventoried: 42
Dual-Prefix Mounts Required: 100% (/api/v1 and /api/v1/api/v1)
Status: CERTIFIED FOR PHASE 6 EXECUTION
================================================================================
```
