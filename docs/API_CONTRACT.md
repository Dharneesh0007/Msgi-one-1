# MSGI One — REST API Specification & OpenAPI Contracts

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** Senior Full-Stack Engineer & API Architect  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  
**Base URL:** `/api/v1`  
**Protocol:** HTTPS / TLS 1.3  

---

## 1. REST Standards & Envelope Convention

Following **Pressman & Maxim** (*Software Engineering*, Ch. 11: "WebApp Design") and standard REST conventions, all endpoints return a consistent JSON response envelope.

### 1.1 Success Envelope
```json
{
  "status": "success",
  "data": {},
  "error": null,
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 105,
    "total_pages": 6
  },
  "timestamp": "2026-11-18T13:30:00.000Z"
}
```

### 1.2 Error Envelope (RFC 7807 Aligned)
```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Resource with identifier 'f47ac10b-58cc-4372-a567-0e02b2c3d479' was not found.",
    "details": [
      {
        "field": "id",
        "issue": "Invalid UUID or entity does not exist"
      }
    ]
  },
  "timestamp": "2026-11-18T13:30:00.000Z"
}
```

### 1.3 Standard Error Codes
- `UNAUTHENTICATED`: Bearer token missing, malformed, or expired (401).
- `PERMISSION_DENIED`: Token user lacks required role (403).
- `VALIDATION_ERROR`: Pydantic payload validation failure (422).
- `ENTITY_NOT_FOUND`: Target resource does not exist (404).
- `CONFLICT`: Unique constraint violation or duplicate application (409).
- `CAPACITY_EXCEEDED`: Event or mentor is fully booked (422).
- `WORKFLOW_AWAITING_APPROVAL`: Consequential action paused for human review (202).
- `INTERNAL_ERROR`: Unhandled exception (500).

---

## 2. Core Endpoint Specifications

### 2.1 Identity & Authentication Endpoints

#### `GET /api/v1/me`
- **Purpose:** Retrieve currently authenticated user profile, assigned roles, preferences, and permissions.
- **Allowed Roles:** Authenticated (`student`, `alumni`, `faculty`, `recruiter`, `admin`).
- **Request Headers:** `Authorization: Bearer <jwt>`.
- **Request Schema:** None.
- **Response Schema (`data`):**
  ```json
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "student@example.msgi.edu",
    "first_name": "Taro",
    "last_name": "Yamada",
    "avatar_url": "https://cdn.msgi.edu/avatars/taro.jpg",
    "is_verified": true,
    "roles": ["student"],
    "preferences": {
      "theme": "system",
      "push_notifications_enabled": true
    },
    "student_profile": {
      "roll_number": "MSGI-2024-IT-042",
      "department": "Information Technology",
      "cgpa": 8.75
    }
  }
  ```
- **DB Operations:** `SELECT FROM users u LEFT JOIN user_roles ur ... WHERE u.id = auth.uid()`.
- **Audit:** None (read-only).

#### `PATCH /api/v1/me`
- **Purpose:** Update personal name, avatar URL, or user preferences.
- **Allowed Roles:** All authenticated users.
- **Request Schema:**
  ```json
  {
    "first_name": "Taro",
    "last_name": "Yamada",
    "avatar_url": "https://cdn.msgi.edu/avatars/new.jpg",
    "preferences": {
      "theme": "dark"
    }
  }
  ```
- **Validation:** Names must be 1–100 chars; `avatar_url` must be valid HTTPS URI.
- **DB Operations:** `UPDATE users ... WHERE id = auth.uid()`.
- **Audit:** Audit log emitted on user profile updates.

---

### 2.2 Alumni Network Endpoints

#### `GET /api/v1/alumni`
- **Purpose:** Query paginated directory of verified alumni with privacy-aware filtering.
- **Allowed Roles:** All authenticated users.
- **Query Parameters:**
  - `page` (integer, default 1)
  - `limit` (integer, default 20, max 100)
  - `graduation_year` (integer, optional)
  - `major` (string, optional)
  - `company` (string, optional)
  - `skill` (string, optional)
- **Response Schema (`data`):**
  ```json
  {
    "items": [
      {
        "id": "e2a1b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c",
        "name": "Kenji Sato",
        "degree": "B.Tech Computer Science",
        "graduation_year": 2021,
        "current_company": "Rakuten",
        "current_title": "Staff AI Engineer",
        "location": "Tokyo, Japan",
        "is_mentor": true,
        "skills": ["PyTorch", "FastAPI", "NLP"]
      }
    ]
  }
  ```
- **DB Operations:** Indexed query with RLS evaluation on visibility and consent.

#### `GET /api/v1/alumni/{id}`
- **Purpose:** Retrieve detailed profile of a single alumnus.
- **Allowed Roles:** All authenticated users.
- **Response Schema (`data`):** Returns full biography, employment history, and education. Masked contact email unless mutual connection exists.

---

### 2.3 Global Alumni Connect Endpoints

#### `GET /api/v1/global/locations`
- **Purpose:** Aggregate alumni locations for regional chapter visualization.
- **Allowed Roles:** All authenticated users.
- **Query Parameters:** `country_code` (ISO 2-letter, optional).
- **Response Schema (`data`):**
  ```json
  [
    {
      "country_code": "JP",
      "country_name": "Japan",
      "city": "Tokyo",
      "latitude": 35.6762,
      "longitude": 139.6503,
      "alumni_count": 48,
      "chapter_name": "Tokyo Alumni Chapter"
    }
  ]
  ```

---

### 2.4 CareerBridge Endpoints

#### `GET /api/v1/jobs`
- **Purpose:** List curated active jobs and internships.
- **Allowed Roles:** All authenticated users.
- **Query Parameters:** `employment_type` (`internship`, `full_time`), `location`, `remote` (boolean).
- **Response Schema (`data`):** List of job cards with company info, deadlines, and required skills.

#### `POST /api/v1/jobs`
- **Purpose:** Create new job listing.
- **Allowed Roles:** `recruiter`, `alumni`, `admin`.
- **Request Schema:**
  ```json
  {
    "company_name": "Sony AI",
    "title": "Machine Learning Intern",
    "description": "Research and development on generative diffusion models...",
    "employment_type": "internship",
    "location": "Tokyo, Japan",
    "salary_min": 300000,
    "salary_max": 450000,
    "currency": "JPY",
    "required_skills": ["Python", "PyTorch", "Computer Vision"],
    "application_deadline": "2026-12-31T23:59:59Z"
  }
  ```
- **Validation:** Minimum description length 50 chars; deadline must be future date.
- **Side Effects:** Asynchronously computes `vector(1536)` embedding using Gemini embeddings API.
- **Audit:** Emits audit log record.

#### `POST /api/v1/jobs/{id}/applications`
- **Purpose:** Submit application for an active job.
- **Allowed Roles:** `student`, `alumni`.
- **Request Schema:**
  ```json
  {
    "resume_url": "resumes/2026/student_42.pdf",
    "cover_letter": "I have completed research in multimodal transformers..."
  }
  ```
- **DB Operations:** Atomic insert into `job_applications` with unique constraint enforcement.
- **Realtime:** Dispatches WebSocket alert to the job poster.

---

### 2.5 MentorMatch Endpoints

#### `GET /api/v1/mentors`
- **Purpose:** List available alumni mentors and their advisory domains.
- **Allowed Roles:** All authenticated users.
- **Query Parameters:** `topic` (string), `availability` (boolean).
- **Response Schema (`data`):** List of verified mentors with active mentee capacity and ratings.

#### `POST /api/v1/mentor-requests`
- **Purpose:** Submit formal request for mentorship.
- **Allowed Roles:** `student`, `alumni`.
- **Request Schema:**
  ```json
  {
    "mentor_id": "8a3d5e21-9b4c-4e8a-bf12-9c8e7a6b5c4d",
    "goal_statement": "Seeking guidance on entering the Japanese tech ecosystem as a foreigner."
  }
  ```
- **Validation:** Goal statement 20–500 chars; checks that `mentor.active_mentees < mentor.max_capacity`.
- **DB Operations:** Insert into `mentor_requests`.
- **Realtime:** Notifies mentor via Supabase Realtime channel.

---

### 2.6 Events and Reunions Endpoints

#### `GET /api/v1/events`
- **Purpose:** Browse upcoming reunions, webinars, and networking mixers.
- **Allowed Roles:** All authenticated users.
- **Query Parameters:** `category`, `time_frame` (`upcoming`, `past`).

#### `POST /api/v1/events/{id}/registrations`
- **Purpose:** RSVP for an event and receive digital ticket code.
- **Allowed Roles:** All authenticated users.
- **Validation:** Event capacity check (`registered_count < capacity`).
- **DB Operations:** Atomic increment of `registered_count` and insertion of `event_registrations`.

---

### 2.7 MSGI AI Command Centre Endpoints

#### `POST /api/v1/ai/chat`
- **Purpose:** Interactive conversational assistant for quick inquiries.
- **Allowed Roles:** All authenticated users.
- **Request Schema:**
  ```json
  {
    "message": "Who are some alumni working in AI in Tokyo?",
    "conversation_id": "optional-uuid"
  }
  ```
- **Response Schema (`data`):**
  ```json
  {
    "reply": "I found 3 verified alumni in Tokyo working in AI...",
    "referenced_entities": [
      {
        "type": "alumni",
        "id": "e2a1b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c",
        "name": "Kenji Sato"
      }
    ]
  }
  ```

#### `POST /api/v1/ai/workflows`
- **Purpose:** Launch multi-agent autonomous goal execution (e.g. End-to-End Career Roadmap).
- **Allowed Roles:** All authenticated users.
- **Request Schema:**
  ```json
  {
    "goal": "I am an IT student. I want to become an AI engineer in Japan. Find suitable MSGI alumni, recommend mentors, identify missing skills, suggest learning resources and find internships.",
    "workflow_type": "career_roadmap"
  }
  ```
- **Response Schema (`data`):** Returns 200 OK (or 202 Awaiting Approval) with serialized workflow graph output, candidate mentors, roadmap steps, and pending approval gate IDs.

#### `POST /api/v1/ai/approvals/{id}/decision`
- **Purpose:** Human-in-the-loop sign-off for consequential agent actions.
- **Allowed Roles:** Initiating user.
- **Request Schema:**
  ```json
  {
    "decision": "approved", // or "rejected"
    "reason": "Proceed with sending mentor request."
  }
  ```
- **Processing:** Resumes paused LangGraph workflow checkpoint and executes the bound service action.
