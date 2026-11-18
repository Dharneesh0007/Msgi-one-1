# MSGI ONE — USER OPERATING GUIDE & ROLE MANUAL

**Document Reference:** `docs/USER_OPERATING_GUIDE.md`  
**Application Platform:** MSGI One — Institutional Alumni & Career Ecosystem  
**Target Environments:** Android Mobile App (Expo SDK 52) & Web REST Portal  
**Target Personas:** Students, Verified Alumni, Faculty, Recruiters, Administrators  

---

## 1. GETTING STARTED & AUTHENTICATION

### 1.1 Account Registration
- Navigate to the **Register** screen.
- Enter your institutional email address (e.g. `alex.rivera@example.msgi.edu`).
- Choose your initial role: **Student**, **Alumni**, **Faculty**, or **Recruiter**.
- Upon registration, you are directed to the **Onboarding Profile** screen to complete your department, graduation year, and professional headline.

### 1.2 Multi-Factor Sign-In
- Enter your email and password on the **Login** screen.
- A secure JWT access token is stored securely in Android Keystore / `expo-secure-store`.
- Tokens expire in 60 minutes and refresh automatically via Supabase Auth session refresh.

---

## 2. STUDENT USER GUIDE

### 2.1 Exploring the Services Hub
From the **Home** tab, tap any of the 12 institutional services:
- **Alumni Directory:** Search verified alumni mentors by company, country, or department. Tap an alumnus to view advisory topics.
- **Career Opportunities:** View active internships and full-time roles. The system automatically highlights your **Skill Overlap %** and missing competencies.
- **MentorMatch:** Submit a mentorship request. Specify your career goal and proposed discussion topic. You will receive an in-app notification when the mentor accepts.
- **Events & Webinars:** Register for upcoming technical workshops, alumni reunions, and career summits.
- **Learning Academy:** Browse curated courses tailored to bridge skill gaps identified for your target career role. Track your progress from 0% to 100%.
- **Communities:** Join open student clubs or submit a join request for private research circles.
- **Collaborative Projects:** Discover cross-disciplinary projects and apply to join project teams.
- **Social Impact:** Pledge non-monetary volunteer hours for institutional community initiatives.

### 2.2 Using the MSGI AI Command Centre
- Switch to the **AI** tab.
- Enter your career aspiration in natural language, for example:
  - *"Analyze my skill gap for a Cloud Solutions Architect role and find a mentor in Japan."*
- The AI Command Centre coordinates the Career, Learning, and Mentorship agents.
- **Safety Rule 15 Confirmation:** When the agent prepares a job application or mentorship request, an **Approval Card** appears in the chat. You must review the payload and tap **"Confirm & Submit"** before any action is executed.

---

## 3. ALUMNI & MENTOR GUIDE

### 3.1 Managing Mentorship
- In your **Profile** tab, toggle **"Accepting Mentees"** to enable student inquiries.
- When a student submits a mentorship request, you will receive an in-app notification.
- Navigate to **MentorMatch > Pending Requests** to **Accept** or **Decline** with feedback notes.

### 3.2 Showcasing Ventures & Projects
- **Startups:** Verified alumni founders can list early-stage ventures in the Startup Showcase to seek student talent or co-founders.
- **Projects:** Create innovative technical projects and recruit skilled student contributors.

---

## 4. RECRUITER & EMPLOYER GUIDE

### 4.1 Posting Opportunities
- Navigate to **CareerBridge > Post Opportunity**.
- Enter job title, company name, location (hybrid/remote/onsite), requirements, and required technical skills.
- The platform automatically matches qualified students and verified alumni based on skill overlap.

### 4.2 Reviewing Applications
- View submitted applications, review candidate cover notes, and update applicant statuses (under review, interviewing, accepted).

---

## 5. FACULTY & RESEARCH GUIDE

### 5.1 Project Creation & Mentorship
- Faculty members can publish research lab projects in the **Collaborative Projects Hub**.
- Set required technical competencies and review student collaboration requests.

---

## 6. INSTITUTIONAL ADMINISTRATOR GUIDE

### 6.1 Credential Verifications
- Access **Admin Console > Verifications** (`/api/v1/admin/verification-requests`).
- Review pending diploma, employment, and faculty credential evidence.
- Select **Approve** to upgrade user roles or **Reject** with formal institutional notes.
- *Anti-Tampering Rule:* Administrators cannot approve their own verification requests.

### 6.2 Administrative Audit Logs
- Access **Admin Console > Audit Logs** (`/api/v1/admin/audit-logs`) to review an immutable chronological trail of administrative actions, role modifications, and system events.

---

## 7. DATA PRIVACY & ACCOUNT ERASURE

- To exercise your GDPR / DPDP Right to Erasure, navigate to **Profile > Settings > Delete Account**.
- Tapping **"Delete Account & Scrub Data"** permanently anonymizes your personal information and invalidates your active session.
