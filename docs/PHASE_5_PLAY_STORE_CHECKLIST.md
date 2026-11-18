# MSGI ONE — GOOGLE PLAY STORE READINESS & COMPLIANCE CHECKLIST

**Document Reference:** `docs/PHASE_5_PLAY_STORE_CHECKLIST.md`  
**Application Package:** `edu.msgi.one`  
**Current Configuration:** Expo SDK 52 / Android API 35 (Android 15)  
**Target Release Phase:** Phase 5 — Google Play Console Pre-Submission Audit  
**Audit Standard:** Google Play Developer Policy (2026 Standards)  

---

## 1. COMPREHENSIVE GOOGLE PLAY POLICY AUDIT

| Policy Requirement | Google Play Standard | MSGI One Implementation | Compliance Status |
| :--- | :--- | :--- | :---: |
| **Account Deletion Policy** | Mandatory in-app deletion path and web URL to request account and data deletion | In-app deletion button in `src/app/(tabs)/profile.tsx`; backend endpoint `DELETE /api/v1/users/{id}` that scrubs all PII and anonymizes records | **COMPLIANT** |
| **Privacy Policy URL** | Active, non-editable public URL detailing data collection and retention | Defined in documentation (`docs/PRIVACY_POLICY.md` / `https://msgi.edu/privacy`); linked in app settings | **COMPLIANT** |
| **App Permissions** | Minimum necessary permissions; no unnecessary sensitive hardware access | Declares only `INTERNET` and `ACCESS_NETWORK_STATE`; zero camera, contact, or fine location permissions requested | **COMPLIANT** |
| **Target API Level** | Requires API level 36+ (Android 16) for new app submissions starting late 2026 | Configured on Expo SDK 52 (API 35). Ready for internal testing / APK distribution; production Play Store upload requires updating to Expo SDK 53+ | **ACTION GATED** |
| **Release Artifact Format** | Android App Bundle (`.aab`) mandatory for public store tracks | `apps/mobile/eas.json` production profile configures `buildType: "app-bundle"` | **COMPLIANT** |
| **Data Safety Declarations** | Complete declaration of data collection, sharing, encryption, and deletion | Completed below in Section 2 | **COMPLIANT** |

---

## 2. GOOGLE PLAY DATA SAFETY DECLARATION FORM

### 2.1 Data Collection & Usage Breakdown

| Data Type Collected | Purpose of Collection | Shared with Third Parties? | Encrypted in Transit? | Ephemeral / Retained? | User Can Request Deletion? |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Name & Email** | App Functionality & Authentication | NO | YES (TLS 1.3) | Retained while active | YES |
| **User IDs** | Account Management & RLS | NO | YES (TLS 1.3) | Retained | YES |
| **Approximate Location** | Regional Alumni Chapters (Global Connect) | NO | YES (TLS 1.3) | Aggregated (k >= 3) | YES |
| **In-App Messages / Requests** | Mentorship & Job Applications | NO | YES (TLS 1.3) | Retained | YES |
| **Academic / Career Info** | Upskilling, Skill Gap & Matchmaking | NO | YES (TLS 1.3) | Retained | YES |

### 2.2 Security Practices
- **Data Encrypted in Transit:** YES — All client-to-server traffic enforces HTTPS/TLS 1.3.
- **Independent Security Review:** YES — Conducted in `docs/PHASE_5_SECURITY_AUDIT.md`.
- **Target Audience:** Institutional Students and Alumni (Age 18+). Designed for Higher Education.
