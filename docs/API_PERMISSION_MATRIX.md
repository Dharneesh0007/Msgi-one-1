# MSGI One — API Role-Based Permission Matrix (RBAC)

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** DevSecOps Engineer & API Architect  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Role Definitions

1. **Student (`student`):** Active matriculated undergraduate or postgraduate learner.
2. **Alumni (`alumni`):** Verified graduate holding an institutional degree.
3. **Faculty (`faculty`):** Academic professor, lecturer, researcher, or department head.
4. **Recruiter (`recruiter`):** Verified corporate hiring partner or institutional placement officer.
5. **Administrator (`admin`):** Institutional ecosystem governance and compliance officer.

---

## 2. Comprehensive Endpoint Permission Matrix

Legend:
- `ALLOW`: Permitted with valid authenticated token.
- `OWN`: Permitted only for resources owned by the authenticated user (`user_id = auth.uid()`).
- `DENY`: HTTP 403 Forbidden.

| HTTP Method & Endpoint | Student | Alumni | Faculty | Recruiter | Admin | Notes / Policy |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Authentication & Profiles** | | | | | | |
| `GET /api/v1/me` | `OWN` | `OWN` | `OWN` | `OWN` | `OWN` | Read own verified profile. |
| `PATCH /api/v1/me` | `OWN` | `OWN` | `OWN` | `OWN` | `OWN` | Update own name/avatar/preferences. |
| `GET /api/v1/users/{id}` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Subject to privacy consent. |
| **Module 1: Alumni Network** | | | | | | |
| `GET /api/v1/alumni` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Verified directory listing. |
| `GET /api/v1/alumni/{id}` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Full profile (masked contacts). |
| `GET /api/v1/alumni/search` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Keyword / vector semantic search. |
| **Module 2: Global Connect** | | | | | | |
| `GET /api/v1/global/locations`| `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Aggregated map coordinates. |
| `GET /api/v1/global/chapters` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Regional chapters directory. |
| `POST /api/v1/global/chapters/{id}/join` | `DENY` | `ALLOW` | `ALLOW` | `DENY` | `ALLOW` | Chapter membership restricted. |
| **Module 3: CareerBridge** | | | | | | |
| `GET /api/v1/jobs` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Active job openings feed. |
| `GET /api/v1/jobs/{id}` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Detailed job specification. |
| `POST /api/v1/jobs` | `DENY` | `ALLOW` | `DENY` | `ALLOW` | `ALLOW` | Post new job/internship. |
| `PATCH /api/v1/jobs/{id}` | `DENY` | `OWN` | `DENY` | `OWN` | `ALLOW` | Edit job (poster or admin). |
| `DELETE /api/v1/jobs/{id}` | `DENY` | `OWN` | `DENY` | `OWN` | `ALLOW` | Deactivate/remove job posting. |
| `POST /api/v1/jobs/{id}/applications` | `ALLOW` | `ALLOW` | `DENY` | `DENY` | `DENY` | Submit job application. |
| `GET /api/v1/jobs/{id}/applications` | `DENY` | `OWN` | `DENY` | `OWN` | `ALLOW` | Review applicants for job. |
| **Module 4: MentorMatch** | | | | | | |
| `GET /api/v1/mentors` | `ALLOW` | `ALLOW` | `ALLOW` | `DENY` | `ALLOW` | Directory of available mentors. |
| `POST /api/v1/mentor-requests` | `ALLOW` | `ALLOW` | `DENY` | `DENY` | `DENY` | Request mentorship connection. |
| `GET /api/v1/mentor-requests/me`| `OWN` | `OWN` | `DENY` | `DENY` | `ALLOW` | Pending/active requests. |
| `PATCH /api/v1/mentor-requests/{id}` | `DENY` | `OWN` | `DENY` | `DENY` | `ALLOW` | Mentor accepts or declines. |
| **Module 5: Learning Academy** | | | | | | |
| `GET /api/v1/courses` | `ALLOW` | `ALLOW` | `ALLOW` | `DENY` | `ALLOW` | Catalog of courses. |
| `GET /api/v1/learning/recommendations` | `ALLOW` | `ALLOW` | `DENY` | `DENY` | `DENY` | AI-curated skill pathway. |
| `POST /api/v1/courses/{id}/progress` | `OWN` | `OWN` | `DENY` | `DENY` | `DENY` | Record module completion. |
| **Module 6: Events & Reunions**| | | | | | |
| `GET /api/v1/events` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Public institutional events. |
| `POST /api/v1/events` | `DENY` | `ALLOW` | `ALLOW` | `DENY` | `ALLOW` | Create institutional event. |
| `POST /api/v1/events/{id}/registrations` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | RSVP / ticket issuance. |
| `DELETE /api/v1/events/{id}/registrations`| `OWN` | `OWN` | `OWN` | `OWN` | `ALLOW` | Cancel event RSVP. |
| **Module 10: Giving & Impact** | | | | | | |
| `GET /api/v1/giving/programmes`| `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Institutional giving funds. |
| `POST /api/v1/giving/pledge` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Pledge financial donation. |
| `GET /api/v1/giving/my-contributions` | `OWN` | `OWN` | `OWN` | `OWN` | `ALLOW` | Tax receipts & history. |
| **Module 11: Administration** | | | | | | |
| `GET /api/v1/admin/verification-queue` | `DENY` | `DENY` | `DENY` | `DENY` | `ALLOW` | Unverified registrations. |
| `POST /api/v1/admin/verify-user/{id}` | `DENY` | `DENY` | `DENY` | `DENY` | `ALLOW` | Approve/reject alumni status. |
| `GET /api/v1/admin/audit-logs` | `DENY` | `DENY` | `DENY` | `DENY` | `ALLOW` | Security & compliance logs. |
| **Module 12: AI Command Centre** | | | | | | |
| `POST /api/v1/ai/chat` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Conversational assistant. |
| `POST /api/v1/ai/workflows` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | `ALLOW` | Autonomous multi-agent goal. |
| `GET /api/v1/ai/workflows/{id}` | `OWN` | `OWN` | `OWN` | `OWN` | `ALLOW` | Retrieve execution state. |
| `POST /api/v1/ai/approvals/{id}/decision` | `OWN` | `OWN` | `OWN` | `OWN` | `ALLOW` | Sign off on paused actions. |

---

## 3. Server-Side Enforcement Architecture

FastAPI implements permission enforcement through high-order dependency injection:

```python
from fastapi import Depends, HTTPException, status
from typing import List

def require_role(allowed_roles: List[str]):
    async def role_checker(current_user = Depends(get_current_active_user)):
        user_roles = current_user.roles  # Retrieved from public.user_roles
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not possess the necessary role permissions to access this resource."
            )
        return current_user
    return role_checker
```

This guarantees zero client bypass: even if a client crafts a manipulated payload, the endpoint router rejects the request prior to invoking any domain service or database transaction.
