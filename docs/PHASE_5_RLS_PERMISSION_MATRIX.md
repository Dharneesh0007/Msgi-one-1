# MSGI ONE — PHASE 5 ROW-LEVEL SECURITY & RBAC PERMISSION MATRIX

**Document Reference:** `docs/PHASE_5_RLS_PERMISSION_MATRIX.md`  
**Phase:** Phase 5 — Quality Assurance & Release Readiness  
**Source Specification:** `supabase/seed/csv/qa_role_permissions.csv` (35 Endpoints Audited)  
**Security Standard:** Principle of Least Privilege (Saltzer & Schroeder)  
**Verification Result:** 100% Validated against SQL Migration Policies & API Guards  

---

## 1. COMPREHENSIVE ENDPOINT & ROLE PERMISSION MATRIX

Legend:
- **ALLOWED**: Full authorized execution for the authenticated role.
- **FORBIDDEN**: Blocked with `HTTP 403 Forbidden` (`PERMISSION_DENIED`).
- **OWNER_ONLY**: Restricted strictly to the creator, applicant, or target user of the entity (`auth.uid() = user_id`).

| Module | Endpoint | Method | Student | Verified Alumni | Unverified Alumni | Faculty | Recruiter | Admin | Candidate | Privacy Boundary / RLS Policy Enforced |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Identity & Profiles** | `/api/v1/users/{id}` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Public profile fields visible; PII masked unless consented |
| **Identity & Profiles** | `/api/v1/users/{id}` | PUT | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | ALLOWED | OWNER_ONLY | Users may only update their own profile; Admin may edit any |
| **Identity & Profiles** | `/api/v1/users/{id}` | DELETE | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | ALLOWED | OWNER_ONLY | GDPR/DPDP erasure; self-service or admin oversight |
| **Alumni Network** | `/api/v1/alumni` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Only verified alumni returned in public directory search |
| **Alumni Network** | `/api/v1/alumni/{id}` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Contact info masked unless alumni has `mentor_opt_in=true` |
| **CareerBridge** | `/api/v1/jobs` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Active approved job postings visible to all authenticated roles |
| **CareerBridge** | `/api/v1/jobs` | POST | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | ALLOWED | ALLOWED | FORBIDDEN | Students and unverified candidates cannot post job openings |
| **CareerBridge** | `/api/v1/jobs/{id}/apply` | POST | ALLOWED | ALLOWED | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | Only students and verified alumni may submit job applications |
| **MentorMatch** | `/api/v1/mentors` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Returns verified mentors with active availability |
| **MentorMatch** | `/api/v1/mentors/requests` | POST | ALLOWED | ALLOWED | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | Mentees may initiate mentorship requests with goals |
| **MentorMatch** | `/api/v1/mentors/requests/{id}/status` | PUT | FORBIDDEN | OWNER_ONLY | FORBIDDEN | OWNER_ONLY | FORBIDDEN | ALLOWED | FORBIDDEN | Only the assigned mentor may accept or decline request |
| **Events & Reunions** | `/api/v1/events` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | All active institutional and alumni events listed |
| **Events & Reunions** | `/api/v1/events` | POST | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | Event creation restricted to alumni hosts faculty and admin |
| **Events & Reunions** | `/api/v1/events/{id}/register` | POST | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Event registration open to all authenticated roles |
| **Global Connect** | `/api/v1/global/directory` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | City-level geolocation only with user consent; country default |
| **Learning & Upskilling** | `/api/v1/learning/resources` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Resource catalog open to all registered learners |
| **Learning & Upskilling** | `/api/v1/learning/enroll` | POST | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Personal course enrollment and progress tracking |
| **Communities** | `/api/v1/communities` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Directory lists public and private group summaries |
| **Communities** | `/api/v1/communities` | POST | ALLOWED | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | Requires verified account standing to create a community |
| **Communities** | `/api/v1/communities/{id}/join` | POST | ALLOWED | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | Public groups auto-join; private groups create pending request |
| **Institutional Verification** | `/api/v1/verifications/submit` | POST | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Users submit credential evidence for institutional role upgrade |
| **Institutional Verification** | `/api/v1/admin/verifications` | GET | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | Restricted strictly to institutional administrative roles |
| **Institutional Verification** | `/api/v1/admin/verifications/{id}/review` | POST | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | Admin decision; never auto-approved by AI agents |
| **Admin & Audit** | `/api/v1/admin/audit-logs` | GET | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | FORBIDDEN | Institutional audit logs accessible strictly to platform admin |
| **Collaborative Projects** | `/api/v1/projects` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Active student and faculty projects catalog |
| **Collaborative Projects** | `/api/v1/projects` | POST | ALLOWED | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | Requires verified student faculty or alumni account |
| **Collaborative Projects** | `/api/v1/projects/{id}/join` | POST | ALLOWED | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | Authenticated users can request collaboration |
| **Startups & Incubation** | `/api/v1/startups` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Showcase directory of alumni and institutional ventures |
| **Startups & Incubation** | `/api/v1/startups` | POST | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | Founders must hold verified alumni or faculty credentials |
| **Social Impact & Giving** | `/api/v1/giving/programmes` | GET | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Non-monetary volunteering initiatives open to all |
| **Social Impact & Giving** | `/api/v1/giving/pledge` | POST | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED | Volunteer hour pledge; strictly zero monetary transactions |
| **AI Command Centre** | `/api/v1/ai/dispatch` | POST | ALLOWED | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | ALLOWED | FORBIDDEN | Dispatches multi-agent workflow; HITL required for mutations |
| **AI Command Centre** | `/api/v1/ai/approve` | POST | OWNER_ONLY | OWNER_ONLY | FORBIDDEN | OWNER_ONLY | FORBIDDEN | ALLOWED | FORBIDDEN | Human-in-the-loop gate; caller must own execution thread |
| **Realtime Notifications** | `/api/v1/notifications` | GET | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | Users strictly receive their own in-app notifications |
| **Realtime Notifications** | `/api/v1/notifications/{id}/read` | PATCH | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | OWNER_ONLY | Users may only acknowledge their own notifications |

---

## 2. POSTGRESQL ROW-LEVEL SECURITY (RLS) POLICIES AUDIT

In `supabase/migrations/20261121000001_phase_4_extended_modules.sql`, all tables have `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;` enabled. Key verified policies include:
1. `notifications_user_isolation`:
   ```sql
   CREATE POLICY notifications_select_policy ON public.notifications
       FOR SELECT USING (auth.uid() = user_id);
   ```
2. `community_private_isolation`:
   ```sql
   CREATE POLICY communities_select_policy ON public.communities
       FOR SELECT USING (
           is_private = false OR
           creator_id = auth.uid() OR
           EXISTS (
               SELECT 1 FROM public.community_memberships cm
               WHERE cm.community_id = id AND cm.user_id = auth.uid() AND cm.status = 'active'
           )
       );
   ```
3. `admin_audit_logs_restriction`:
   ```sql
   CREATE POLICY admin_audit_logs_policy ON public.admin_audit_logs
       FOR SELECT USING (
           EXISTS (
               SELECT 1 FROM public.user_roles ur
               JOIN public.roles r ON ur.role_id = r.id
               WHERE ur.user_id = auth.uid() AND r.name IN ('admin', 'institutional_admin')
           )
       );
   ```
