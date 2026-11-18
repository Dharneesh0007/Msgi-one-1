# MSGI One — Phase 2 API Implementation Document
**REST Services Contract and Endpoint Reference for Core Business Modules**

**Document Version:** 1.0.0  
**Phase:** 2 (Core Business Modules)  
**Base Path:** `/api/v1`  
**Envelope Standard:** `{ status, data, error, meta, timestamp }`  

---

## 1. Alumni Network Endpoints

### 1.1 `GET /api/v1/alumni` & `GET /api/v1/alumni/search`
- **Summary:** Discover and filter alumni profiles.
- **Permission:** Any Authenticated Member (`student`, `alumni`, `faculty`, `recruiter`, `admin`).
- **Query Parameters:**
  - `query`: string (search by full name, company, or skills)
  - `department`: string (e.g. `Information Technology`)
  - `industry`: string (e.g. `Artificial Intelligence`)
  - `country`: string (e.g. `Japan`)
  - `skill`: string (e.g. `PyTorch`)
  - `graduation_year`: integer (e.g. `2021`)
  - `verified_only`: boolean (default `true`)
  - `page`: integer (default `1`)
  - `limit`: integer (default `20`, max `50`)
- **Privacy Guarantees:** Private profiles are completely omitted; sensitive contact details (email, phone, coordinates) are masked.

### 1.2 `GET /api/v1/alumni/{alumni_id}`
- **Summary:** Retrieve public detailed profile for a specific alumnus.
- **Permission:** Any Authenticated Member.
- **Error Codes:** `ENTITY_NOT_FOUND` (404), `PROFILE_PRIVATE` (403).

---

## 2. CareerBridge Endpoints

### 2.1 `GET /api/v1/jobs`
- **Summary:** Retrieve active career opportunities with deterministic skill-overlap analysis.
- **Permission:** Any Authenticated Member.
- **Query Parameters:** `opportunity_type`, `country`, `workplace_type`, `skill`.

### 2.2 `GET /api/v1/jobs/{job_id}`
- **Summary:** Retrieve detailed opportunity description, requirements, and alumni presence.
- **Permission:** Any Authenticated Member.

### 2.3 `POST /api/v1/jobs`
- **Summary:** Post an institutional opportunity.
- **Permission:** `recruiter`, `admin`.
- **Error Codes:** `PERMISSION_DENIED` (403).

### 2.4 `POST /api/v1/jobs/{job_id}/applications`
- **Summary:** Submit an application.
- **Permission:** Any Authenticated Student/Alumni.
- **Constraints:** Enforces `UNIQUE(job_id, applicant_id)`.
- **Error Codes:** `DUPLICATE_APPLICATION` (409), `DEADLINE_PASSED` (400), `JOB_NOT_FOUND` (404).

### 2.5 `GET /api/v1/me/applications`
- **Summary:** List applications submitted by current user.
- **Permission:** Owner only.

---

## 3. MentorMatch Endpoints

### 3.1 `GET /api/v1/mentors`
- **Summary:** Discover verified alumni mentors with open slots, deterministically ranked.
- **Permission:** Any Authenticated Member.
- **Query Parameters:** `topic`, `country`, `student_goal`.

### 3.2 `GET /api/v1/mentors/{mentor_id}`
- **Summary:** Mentor detail view.
- **Permission:** Any Authenticated Member.

### 3.3 `POST /api/v1/mentor-requests`
- **Summary:** Submit request to an available mentor.
- **Permission:** Student/Alumni.
- **Constraints:** Max capacity check; prevents duplicate pending requests; blocks self-mentorship.
- **Error Codes:** `MENTOR_CAPACITY_EXCEEDED` (400), `DUPLICATE_PENDING_REQUEST` (409), `SELF_MENTORSHIP_PROHIBITED` (400).

### 3.4 `GET /api/v1/me/mentor-requests`
- **Summary:** List mentorship requests where user is student or mentor.
- **Permission:** Owner only.

### 3.5 `PATCH /api/v1/mentor-requests/{request_id}`
- **Summary:** Status transition (`accepted`, `rejected`, `completed`, `cancelled`).
- **Permission:** Mentor can accept/reject; Student can cancel.
- **Error Codes:** `PERMISSION_DENIED` (403), `INVALID_TRANSITION` (400).

---

## 4. Events & Reunions Endpoints

### 4.1 `GET /api/v1/events`
- **Summary:** List published institutional events with real-time seat availability.
- **Permission:** Any Authenticated Member.
- **Query Parameters:** `event_type`, `is_virtual`.

### 4.2 `GET /api/v1/events/{event_id}`
- **Summary:** Event detail view.
- **Permission:** Any Authenticated Member.

### 4.3 `POST /api/v1/events/{event_id}/registrations`
- **Summary:** Register for event; atomically decrements available seats.
- **Permission:** Any Authenticated Member.
- **Constraints:** `UNIQUE(event_id, user_id)`.
- **Error Codes:** `EVENT_CAPACITY_EXCEEDED` (400), `DUPLICATE_REGISTRATION` (409).

### 4.4 `GET /api/v1/me/event-registrations`
- **Summary:** List user's active event registrations with ticket codes.
- **Permission:** Owner only.

### 4.5 `DELETE /api/v1/events/{event_id}/registrations`
- **Summary:** Cancel registration; atomically increments available seats.
- **Permission:** Registrant only.

---

## 5. Global Alumni Connect Endpoints (P1)

### 5.1 `GET /api/v1/global/locations`
- **Summary:** Aggregated regional counts.
- **Privacy Rule:** Suppresses counts < 3 for deanonymization protection.

### 5.2 `GET /api/v1/global/chapters`
- **Summary:** Official regional alumni chapters.
- **Permission:** Any Authenticated Member.
