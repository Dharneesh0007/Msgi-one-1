# MSGI One — Module Specifications (12 Bounded Contexts)

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** Principal Software Architect, Senior Full-Stack Engineer & Domain Modeler  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Domain Grouping Overview

Following **Eric Evans** (*Domain-Driven Design*, Chapters 3 & 14: "Model-Driven Design" and "Bounded Contexts"), the 12 functional modules of MSGI One are partitioned into 6 cohesive business domains. Shared aggregate roots (`User`, `Profile`, `ConsentRecord`) are defined centrally to prevent entity duplication across domains.

| Bounded Context / Domain | Enclosed Modules | Primary Shared Aggregate Roots |
| :--- | :--- | :--- |
| **1. Identity & Networking** | 1. Alumni Network<br>2. Global Alumni Connect | `User`, `AlumniProfile`, `UserLocation`, `Connection` |
| **2. Career & Development** | 3. CareerBridge<br>4. MentorMatch<br>5. Learning Academy | `Job`, `JobApplication`, `MentorProfile`, `MentorSession`, `Course`, `LearningProgress` |
| **3. Engagement** | 6. Events & Reunions<br>7. Communities & Interest Groups | `Event`, `EventRegistration`, `Community`, `CommunityMembership` |
| **4. Innovation** | 8. Collaboration Hub<br>9. Startup Ecosystem | `Project`, `ProjectMember`, `Startup`, `StartupMember` |
| **5. Institutional Operations** | 10. Giving & Social Impact<br>11. Institutional Connect & Administration | `ImpactProgramme`, `DonationRecord`, `AuditLog`, `VerificationRequest` |
| **6. Intelligence** | 12. MSGI AI Command Centre | `AgentRun`, `AgentAction`, `ApprovalRequest` |

---

## 2. Detailed Specifications for All 12 Modules

### Module 1: Alumni Network (Identity & Networking)
1. **Purpose:** Maintain verified, searchable institutional alumni directory with privacy-preserving visibility controls.
2. **User Roles:** Student, Alumni, Faculty, Recruiter, Admin.
3. **Required Inputs:** Search query, graduation year range, degree/major filter, industry, skills, page, limit.
4. **Validation Rules:** Graduation year must be valid four-digit integer (`1950 <= year <= current_year + 5`); query string sanitized against SQL/HTML injection.
5. **Processing Workflow:** Client submits query -> API filters by verified status -> applies user's consent & visibility level (`public`, `institutional`, `connections_only`) -> returns paginated profile summaries.
6. **Database Entities:** `users`, `alumni_profiles`, `user_skills`, `skills`, `consent_records`.
7. **API Endpoints:** `GET /api/v1/alumni`, `GET /api/v1/alumni/{id}`, `GET /api/v1/alumni/search`.
8. **AI Agent Involvement:** Alumni Discovery Agent generates semantic embeddings for natural-language candidate matching.
9. **Expected Output:** Paginated list of verified alumni cards with masked contact details if not connected.
10. **Dependencies:** Central Auth and Identity Domain.
11. **Realtime Requirements:** Profile update invalidation via cache tags.
12. **Error Handling:** 404 for non-existent/hidden profiles; 403 for unauthorized detail access.
13. **MVP Priority:** **P0 (Essential MVP)**.

---

### Module 2: Global Alumni Connect (Identity & Networking)
1. **Purpose:** Geographically group alumni into global chapters, regional hubs, and relocation support networks.
2. **User Roles:** Student, Alumni, Faculty, Admin.
3. **Required Inputs:** Country code, city name, chapter identifier, coordinate radius.
4. **Validation Rules:** Valid ISO 3166-1 alpha-2 country codes; latitude/longitude bounds validation.
5. **Processing Workflow:** Fetches alumni who have explicitly opted into sharing city/country location -> aggregates chapter counts -> returns chapter leads and regional directory.
6. **Database Entities:** `alumni_locations`, `chapters`, `chapter_memberships`, `alumni_profiles`.
7. **API Endpoints:** `GET /api/v1/global/locations`, `GET /api/v1/global/chapters`, `POST /api/v1/global/chapters/{id}/join`.
8. **AI Agent Involvement:** Global Connect Agent identifies alumni in destination countries (e.g., Japan relocation queries).
9. **Expected Output:** Aggregated map points, chapter listings, and localized alumni mentors.
10. **Dependencies:** Module 1 (Alumni Network).
11. **Realtime Requirements:** Low; batch or cached updates.
12. **Error Handling:** Empty result handler when no alumni reside in requested region.
13. **MVP Priority:** **P1 (Implement if time permits)**.

---

### Module 3: CareerBridge (Career & Development)
1. **Purpose:** Curated employment portal connecting verified institutional students and alumni to vetted internships and jobs.
2. **User Roles:** Student (applicant), Alumni (poster/applicant), Recruiter (poster/reviewer), Admin (moderator).
3. **Required Inputs:** Job title, company, description, employment type, location, experience level, required skills, application deadline.
4. **Validation Rules:** Deadline must be in the future; description >= 50 characters; salary ranges must be positive.
5. **Processing Workflow:** Recruiter/Alumni posts job -> Admin/Auto-verification -> published to feed -> Student reviews -> submits resume (Storage signed URL) -> application record created.
6. **Database Entities:** `jobs`, `job_applications`, `skills`, `user_skills`, `student_profiles`.
7. **API Endpoints:** `GET /api/v1/jobs`, `POST /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `POST /api/v1/jobs/{id}/applications`.
8. **AI Agent Involvement:** Career Agent performs resume-to-job description match scoring and missing skill analysis.
9. **Expected Output:** Structured job listing and real-time application tracking for students and recruiters.
10. **Dependencies:** Identity Domain, Storage Service.
11. **Realtime Requirements:** Realtime alert when application status changes (e.g., Shortlisted, Interview Scheduled).
12. **Error Handling:** 409 Conflict if student re-applies to the same job; 400 if application deadline has elapsed.
13. **MVP Priority:** **P0 (Essential MVP)**.

---

### Module 4: MentorMatch (Career & Development)
1. **Purpose:** Structured mentorship matching connecting students with experienced alumni in specific target industries.
2. **User Roles:** Student (mentee), Alumni (mentor), Admin.
3. **Required Inputs:** Target industry, mentorship topics, mentee goal description, meeting availability, request message.
4. **Validation Rules:** Goal description 20–500 chars; mentor must have active capacity (`active_mentees < max_capacity`).
5. **Processing Workflow:** Student submits mentorship request -> Mentor receives notification -> Mentor accepts/declines -> Session schedule established -> Feedback recorded.
6. **Database Entities:** `mentor_profiles`, `mentor_requests`, `mentor_sessions`, `career_goals`.
7. **API Endpoints:** `GET /api/v1/mentors`, `POST /api/v1/mentor-requests`, `PATCH /api/v1/mentor-requests/{id}`, `GET /api/v1/mentor-requests/me`.
8. **AI Agent Involvement:** Mentor Matching Agent evaluates mentee goals against mentor domain expertise and capacity.
9. **Expected Output:** Match quality score (0–100%), verified mentor profile, and status-tracked request record.
10. **Dependencies:** Module 1 (Alumni Network), Module 12 (AI Command Centre).
11. **Realtime Requirements:** Realtime WebSocket update when mentor accepts or declines a request.
12. **Error Handling:** 422 if mentor has reached capacity; 409 if active pending request already exists between the pair.
13. **MVP Priority:** **P0 (Essential MVP)**.

---

### Module 5: Learning Academy (Career & Development)
1. **Purpose:** Institutional skills development, curated learning roadmaps, and certification pathways aligned with industry demands.
2. **User Roles:** Student, Alumni, Faculty.
3. **Required Inputs:** Skill target, course category, completion status, quiz scores.
4. **Validation Rules:** Progress percentage between 0 and 100.
5. **Processing Workflow:** Student selects target career goal -> System maps missing skills -> presents curated modules -> records completion.
6. **Database Entities:** `courses`, `course_modules`, `learning_progress`, `skills`.
7. **API Endpoints:** `GET /api/v1/courses`, `GET /api/v1/courses/{id}`, `POST /api/v1/courses/{id}/progress`, `GET /api/v1/learning/recommendations`.
8. **AI Agent Involvement:** Learning Agent parses career gaps and returns prioritized courses or public learning resources.
9. **Expected Output:** Personalized learning checklist with verifiable progress metrics.
10. **Dependencies:** Module 3 (CareerBridge), Module 4 (MentorMatch).
11. **Realtime Requirements:** None (standard request-response).
12. **Error Handling:** Standard 404 for invalid course IDs.
13. **MVP Priority:** **P1 (Implement if time permits)**.

---

### Module 6: Events and Reunions (Engagement)
1. **Purpose:** Facilitate physical and virtual institutional reunions, webinars, homecoming events, and career mixers.
2. **User Roles:** All roles (browse and register); Alumni/Admin/Faculty (event creation).
3. **Required Inputs:** Event title, description, category, start_time, end_time, location_type (`virtual` | `in_person`), venue/link, capacity.
4. **Validation Rules:** `end_time > start_time`; capacity must be positive integer; past event dates rejected for new events.
5. **Processing Workflow:** Organizer drafts event -> Admin approves (if student/alumni submitted) -> published to feed -> users RSVP -> registration record created -> QR ticket generated.
6. **Database Entities:** `events`, `event_registrations`, `event_categories`.
7. **API Endpoints:** `GET /api/v1/events`, `POST /api/v1/events`, `GET /api/v1/events/{id}`, `POST /api/v1/events/{id}/registrations`, `DELETE /api/v1/events/{id}/registrations`.
8. **AI Agent Involvement:** Event Agent surfaces relevant upcoming events based on user skills, interests, and location.
9. **Expected Output:** Event catalog, RSVP confirmation, and registration roster for organizers.
10. **Dependencies:** Identity Domain.
11. **Realtime Requirements:** Live registration counter updates on high-demand events.
12. **Error Handling:** 400 "Event at maximum capacity"; 409 "Already registered".
13. **MVP Priority:** **P0 (Essential MVP)**.

---

### Module 7: Communities and Interest Groups (Engagement)
1. **Purpose:** Niche discussion spaces, affinity groups (e.g. Women in Tech, Robotics Club Alumni), and regional chapters.
2. **User Roles:** All roles.
3. **Required Inputs:** Community name, description, privacy (`public`, `private`, `invite_only`), topic tags.
4. **Validation Rules:** Community name unique and 3–100 chars; profanity filters applied.
5. **Processing Workflow:** User creates group -> members join or request access -> discussions posted -> notifications dispatched.
6. **Database Entities:** `communities`, `community_memberships`, `community_posts`.
7. **API Endpoints:** `GET /api/v1/communities`, `POST /api/v1/communities`, `POST /api/v1/communities/{id}/join`.
8. **AI Agent Involvement:** Community Agent moderates incoming posts for code-of-conduct violations.
9. **Expected Output:** Community feed and member directory.
10. **Dependencies:** Identity Domain.
11. **Realtime Requirements:** WebSocket post broadcast for active chat threads.
12. **Error Handling:** 403 on private community content without approved membership.
13. **MVP Priority:** **P2 (Post-MVP)**.

---

### Module 8: Collaboration and Innovation Hub (Innovation)
1. **Purpose:** Cross-disciplinary research collaboration, academic paper co-authoring, and open innovation projects.
2. **User Roles:** Student, Alumni, Faculty.
3. **Required Inputs:** Project title, abstract, required roles/skills, faculty supervisor, IP disclosures.
4. **Validation Rules:** Title >= 10 chars; faculty approval required before publishing call for members.
5. **Processing Workflow:** Initiator posts project -> Faculty verifies -> Students/Alumni apply -> Collaborative milestone tracking.
6. **Database Entities:** `projects`, `project_members`, `project_milestones`.
7. **API Endpoints:** `GET /api/v1/projects`, `POST /api/v1/projects`, `POST /api/v1/projects/{id}/apply`.
8. **AI Agent Involvement:** Collaboration Agent matches student technical backgrounds with open faculty research initiatives.
9. **Expected Output:** Research directory, member rosters, and milestone status.
10. **Dependencies:** Module 1 (Alumni Network), Module 5 (Learning Academy).
11. **Realtime Requirements:** Low.
12. **Error Handling:** 403 when non-members attempt to view internal research notes.
13. **MVP Priority:** **P2 (Post-MVP)**.

---

### Module 9: Startup Ecosystem (Innovation)
1. **Purpose:** Incubate alumni and student ventures, connect founders to institutional seed networks, and showcase startup portfolios.
2. **User Roles:** Student Founders, Alumni Founders, Alumni Investors/Mentors, Admin.
3. **Required Inputs:** Startup name, pitch summary, industry sector, funding stage (`bootstrapped`, `seed`, `series_a`), website, pitch deck URL.
4. **Validation Rules:** Valid URL formats; stage must match defined enum.
5. **Processing Workflow:** Founder registers venture -> Admin/Incubator reviews credentials -> Venture showcased in institutional directory.
6. **Database Entities:** `startups`, `startup_members`, `startup_milestones`.
7. **API Endpoints:** `GET /api/v1/startups`, `POST /api/v1/startups`, `GET /api/v1/startups/{id}`.
8. **AI Agent Involvement:** Startup Agent assists founders in pitch deck refinement and investor matching.
9. **Expected Output:** Showcase portfolio cards and founder-to-investor introduction channels.
10. **Dependencies:** Module 1 (Alumni Network), Module 4 (MentorMatch).
11. **Realtime Requirements:** Low.
12. **Error Handling:** 400 on malformed pitch deck URLs.
13. **MVP Priority:** **P2 (Post-MVP)**.

---

### Module 10: Giving and Social Impact (Institutional Operations)
1. **Purpose:** Transparent institutional endowment campaigns, scholarship sponsorships, and student hardship emergency funds.
2. **User Roles:** Alumni (donor), Admin (campaign manager), Student (beneficiary).
3. **Required Inputs:** Campaign ID, pledge amount, currency, anonymity preference, message to beneficiaries.
4. **Validation Rules:** Amount >= minimum allowed pledge; currency restricted to valid institutional payment configs (e.g. USD, JPY, INR).
5. **Processing Workflow:** User creates donation intent -> system creates pending pledge record -> passes to simulated secure gateway -> updates campaign progress -> generates tax receipt.
6. **Database Entities:** `impact_programmes`, `donation_records`, `volunteering_records`.
7. **API Endpoints:** `GET /api/v1/giving/programmes`, `POST /api/v1/giving/pledge`, `GET /api/v1/giving/my-contributions`.
8. **AI Agent Involvement:** Impact Agent summarizes campaign progress and generates personalized institutional impact reports.
9. **Expected Output:** Real-time campaign funding thermometers, receipt issuance, and donor recognition badges.
10. **Dependencies:** Identity Domain, Module 11 (Institutional Administration).
11. **Realtime Requirements:** Immediate campaign total re-calculation on committed donation.
12. **Error Handling:** Consequential financial approval gate prevents accidental double-charging.
13. **MVP Priority:** **P1 (Implement if time permits)**.

---

### Module 11: Institutional Connect and Administration (Institutional Operations)
1. **Purpose:** Institutional verification of alumni degrees, administrator role delegation, audit log review, and platform moderation.
2. **User Roles:** Admin, Faculty.
3. **Required Inputs:** Student roll number/ID, verification decision (`approved`, `rejected`), reason, role assignment payload.
4. **Validation Rules:** Admin role required on token; mandatory justification string on rejections.
5. **Processing Workflow:** User registers -> placed in verification queue -> Admin verifies against institutional records -> role status elevated to `verified_alumni` -> welcome email dispatched.
6. **Database Entities:** `users`, `user_roles`, `audit_logs`, `institutional_documents`.
7. **API Endpoints:** `GET /api/v1/admin/verification-queue`, `POST /api/v1/admin/verify-user/{id}`, `GET /api/v1/admin/audit-logs`.
8. **AI Agent Involvement:** Institutional Knowledge Agent searches institutional policies and accreditation documentation.
9. **Expected Output:** Administrative dashboard, moderation queue metrics, and immutable audit logs.
10. **Dependencies:** Identity Domain, Layer G (Audit Logging).
11. **Realtime Requirements:** Realtime updates on critical security events.
12. **Error Handling:** 403 Forbidden for any non-admin token.
13. **MVP Priority:** **P1 (Core admin verification queue in MVP)**.

---

### Module 12: MSGI AI Command Centre (Intelligence)
1. **Purpose:** The cognitive core of MSGI One. Orchestrates cross-module queries, performs career gap analysis, and executes safe multi-step workflows.
2. **User Roles:** All authenticated roles.
3. **Required Inputs:** Natural language prompt, contextual filters, conversation history, workflow identifiers.
4. **Validation Rules:** Prompt length 5–2000 chars; prompt injection sanitation; rate-limited to 10 queries/minute per user.
5. **Processing Workflow:** Receives query -> Master Orchestrator creates execution graph -> routes to specialized sub-agents -> queries vector and relational stores -> constructs unified response -> triggers approval gates for consequential actions.
6. **Database Entities:** `agent_runs`, `agent_actions`, `approval_requests`.
7. **API Endpoints:** `POST /api/v1/ai/chat`, `POST /api/v1/ai/workflows`, `GET /api/v1/ai/workflows/{id}`, `POST /api/v1/ai/approvals/{id}/decision`.
8. **AI Agent Involvement:** Master Orchestrator + all 11 domain sub-agents.
9. **Expected Output:** Multimodal structured plan, mentor cards, job cards, skill roadmaps, and explicit approval prompts.
10. **Dependencies:** All other 11 modules.
11. **Realtime Requirements:** Realtime streaming response tokens and approval prompt triggers.
12. **Error Handling:** Graceful fallback to deterministic search when LLM returns low confidence or rate-limit errors.
13. **MVP Priority:** **P0 (Essential MVP)**.
