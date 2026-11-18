# MSGI One — Phase 4 Extended Modules Implementation Specification

**Project:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Target Architecture:** 7-Layer Architecture (Layers A through G)  
**Implementation Phase:** Phase 4 — Extended MVP, Realtime and Android Release Preparation  
**Engineering Standards:** Evans Domain-Driven Design, Silberschatz Database System Concepts, Sommerville Software Engineering  

---

## 1. Executive Summary

Phase 4 completes the remaining six business modules of the MSGI One platform, elevating the system from the initial P0 foundation to the full 12-module institutional ecosystem. All modules strictly adhere to the central identity architecture, consuming `auth.users`, `public.users`, and `public.user_roles` without introducing secondary authentication or isolated data stores.

Every endpoint returns the standard architectural envelope:
```json
{
  "status": "success",
  "data": { ... },
  "error": null,
  "meta": { "timestamp": "2026-11-21T00:00:00Z" }
}
```

---

## 2. Module Implementations

### 2.1 Module 9: Learning Academy
- **Domain Service:** `services/api/src/services/learning_service.py`
- **Router:** `services/api/src/routers/learning.py` (`/api/v1/learning/*` and `/api/v1/me/learning`)
- **Key Entities:** `public.learning_resources`, `public.course_enrollments`
- **Business Capabilities:**
  1. **Course Catalog Discovery:** Filterable by target skill (e.g. Python, Docker, PyTorch) and difficulty level (`Beginner`, `Intermediate`, `Advanced`).
  2. **Student Course Enrollment:** Enforces `UNIQUE(user_id, resource_id)`. Duplicate enrollments return `409 CONFLICT`.
  3. **Progress Tracking & Invariant Bounds:** Progress validated at `0 <= progress <= 100`. Out-of-bounds updates return `400 BAD_REQUEST`.
  4. **Cross-User Authorization Guard:** Only the enrolled user can modify progress; cross-user attempts return `403 FORBIDDEN`.
  5. **Completion Milestone Dispatch:** When progress reaches `100%`, status transitions to `completed`, `completed_at` is stamped, and a realtime in-app notification is committed to the student's inbox.

### 2.2 Module 10: Communities & Interest Groups
- **Domain Service:** `services/api/src/services/community_service.py`
- **Router:** `services/api/src/routers/communities.py` (`/api/v1/communities/*` and `/api/v1/me/communities`)
- **Key Entities:** `public.communities`, `public.community_memberships`
- **Business Capabilities:**
  1. **Public vs. Private Visibility:** Public communities are globally discoverable; private circles (e.g. Founders Circle) are hidden from non-member searches.
  2. **Direct Join vs. Moderated Approval:** Joining a public community grants immediate `active` status. Joining a private group creates a `pending` membership record and notifies the group creator.
  3. **Role-Based Moderation:** Only the community creator or an institutional administrator can approve/reject membership requests; non-moderators receive `403 FORBIDDEN`.
  4. **Duplicate Protection:** Enforces `UNIQUE(community_id, user_id)` preventing spam applications (`409 CONFLICT`).

### 2.3 Module 12: Institutional Administration
- **Domain Service:** `services/api/src/services/admin_service.py`
- **Router:** `services/api/src/routers/admin.py` (`/api/v1/admin/*`)
- **Key Entities:** `public.verification_requests`, `public.admin_audit_logs`
- **Business Capabilities:**
  1. **RBAC Enforcement:** Requires `admin` or `institutional_admin` role. Unauthorized users receive `403 FORBIDDEN`.
  2. **Credential Verification Queue:** Lists submitted verification requests with evidence payloads (degrees, graduation years, student IDs).
  3. **Anti-Self-Verification Gate:** Administrators cannot approve or reject their own user verification request (`400 BAD_REQUEST`).
  4. **Immutable Audit Logging:** Every administrative action (`verify_user_approved`, `verify_user_rejected`) generates an append-only entry in `public.admin_audit_logs`.
  5. **Institutional Summary Metrics:** Aggregates pending verification counts, active verified alumni, open jobs, and mentor capacity.

### 2.4 Module 7: Collaboration & Innovation Hub
- **Domain Service:** `services/api/src/services/extended_service.py`
- **Router:** `services/api/src/routers/extended.py` (`/api/v1/projects/*` and `/api/v1/me/projects`)
- **Key Entities:** `public.projects`, `public.project_members`
- **Business Capabilities:**
  1. **Cross-Disciplinary Project Discovery:** Search active engineering and research projects by required skills.
  2. **Contributor Application:** Students apply to projects with `pending` status, dispatching a notification to the project owner.
  3. **Duplicate Prevention:** Enforces `UNIQUE(project_id, user_id)` (`409 CONFLICT`).

### 2.5 Module 8: Startup Ecosystem
- **Domain Service:** `services/api/src/services/extended_service.py`
- **Router:** `services/api/src/routers/extended.py` (`/api/v1/startups/*`)
- **Key Entities:** `public.startups`, `public.startup_connection_requests`
- **Business Capabilities:**
  1. **Vetted Venture Directory:** Search ventures founded by verified alumni, tagged with funding stage and intent flags (`seeking_mentors`, `seeking_talent`).
  2. **Introduction Requests:** Prospective hires and advisors submit targeted connection requests (`mentorship`, `talent`, `collaboration`).
  3. **Founder Notification:** Founder receives in-app alerts detailing applicant background and message.

### 2.6 Module 11: Giving and Social Impact
- **Domain Service:** `services/api/src/services/extended_service.py`
- **Router:** `services/api/src/routers/extended.py` (`/api/v1/impact/*`)
- **Key Entities:** `public.impact_programmes`, `public.volunteer_interests`
- **Business Capabilities:**
  1. **Institutional Impact Initiatives:** Browse active community outreach, youth STEM coding drives, and campus sustainability projects.
  2. **Volunteer Interest Expression:** Alumni and students submit volunteer registrations with scheduling availability notes.
  3. **Strict Non-Payment Invariant:** Per architectural policy, live payment gateways, credit card processing, and currency flows are strictly deferred and non-operational. Programmes focus entirely on high-impact institutional volunteering and non-monetary contribution.

---

## 3. Cross-Module Entity Relationship Summary

```
                      +-------------------+
                      |   public.users    |
                      +---------+---------+
                                |
      +-------------------------+-------------------------+
      |                         |                         |
      v                         v                         v
+-----+---------------+   +-----+---------------+   +-----+---------------+
| course_enrollments  |   |community_memberships|   |verification_requests|
+---------------------+   +---------------------+   +---------------------+
      |                         |                         |
      v                         v                         v
+-----+---------------+   +-----+---------------+   +-----+---------------+
|  learning_resources |   |     communities     |   |  admin_audit_logs   |
+---------------------+   +---------------------+   +---------------------+
```

All 6 extended modules cleanly interlock with the existing identity, notification, and authorization subsystems without introducing orphan records or schema discrepancies.
