# MSGI One — Staging Android Build Execution Report
**Environment:** STAGING ONLY  
**EAS Cloud Build ID:** `a95a7169-d48b-4730-bcfd-921500e4b8fae`  
**Git Baseline Commit:** `8a2167a` (Branch: `deploy/staging-hosted`)  
**Package Name:** `edu.msgi.one` (Version: `0.1.0`, VersionCode: `1`)  
**Expo SDK:** 52.0.0+  
**Target Architecture:** Android APK (Signed Staging Build)  
**Execution Timestamp:** 2026-11-20T19:35:00+05:30  
**Compliance Standard:** Mandatory Engineering Laws (AGENTS.md Rules 6, 10, 16, 17, 20)  

---

## 1. Executive Summary

This report documents the official Android staging build metadata and verification for MSGI One (`edu.msgi.one`). The signed Android APK build was generated via the EAS Cloud Build pipeline targeting the `staging` build profile.

The APK artifact `a95a7169-d48b-4730-bcfd-921500e4b8fae` serves as the frozen baseline for all physical device testing. Under the **Frozen APK Rule**, zero rebuilds were triggered during subsequent backend defect resolutions.

---

## 2. Acceptance Gate Verification Matrix

| Gate ID | Actual Test Action | Target Environment & Build ID | Expected Result | Actual Result | Evidence Location | Status | Defect ID & Remediation |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **GATE-BLD-01** | Android Asset Prebuild Verification | Expo Prebuild Engine | Valid icon, adaptive icon, and splash assets | Prebuild passed cleanly | `apps/mobile/assets/` | **PASS** | Assets generated via `generate-assets.js` |
| **GATE-BLD-02** | Monorepo Metro JavaScript Bundling | Metro Bundler + Expo SDK 52 | All 960 modules resolved and bundled | Bundled cleanly without unresolved `@msgi-one/*` imports | `apps/mobile/metro.config.js` | **PASS** | Monorepo `watchFolders` configured |
| **GATE-BLD-03** | Source File Git Tracking Verification | Git Index (`deploy/staging-hosted`) | All `src/lib/` files tracked (no broad gitignore exclusions) | `apps/mobile/src/lib/` explicitly tracked | `.gitignore` rule negation | **PASS** | Fixed broad `lib/` ignore rule in commit `17f67ac` |
| **GATE-BLD-04** | Kotlin Version Alignment for Jetpack Compose | Gradle Daemon & EAS Builder | `android.kotlinVersion = 1.9.25` for Compose Compiler 1.5.15 | Build passed compilation with Kotlin 1.9.25 | `apps/mobile/app.json` | **PASS** | Configured `expo-build-properties` in commit `8a2167a` |
| **GATE-BLD-05** | EAS Android Cloud Build Execution | EAS Build ID `a95a7169-d48b-4730-bcfd-921500e4b8fae` | Signed standalone APK produced and downloadable | Signed APK generated and verified on physical hardware | EAS Dashboard / APK download | **PASS** | None |
| **GATE-BLD-06** | Local Hermes Bytecode Export Validation | `npx expo export --platform android` | Valid `.hbc` bytecode bundle (0 errors) | 3.21 MB Hermes bundle compiled in 4,635ms | `apps/mobile/dist/` | **PASS** | None |
| **GATE-BLD-07** | SDK Preservation & Freezing | Repository Root | APK preserved; zero unnecessary rebuilds | Frozen APK rule enforced | Git log / project status | **PASS** | None |

---

## 3. Build Configuration & SDK Version Records

```json
{
  "package": "edu.msgi.one",
  "version": "0.1.0",
  "versionCode": 1,
  "minSdkVersion": 24,
  "compileSdkVersion": 35,
  "targetSdkVersion": 35,
  "kotlinVersion": "1.9.25",
  "hermesEnabled": true,
  "expoSdk": "52.0.0+",
  "reactNative": "0.76.5",
  "easBuildId": "a95a7169-d48b-4730-bcfd-921500e4b8fae"
}
```

---

## 4. Environment Variables Bound at Build Time

The frozen APK contains the following staging environment variables (configured via `apps/mobile/eas.json`):
- `EXPO_PUBLIC_API_URL`: `"https://msgi-one-jpkz.onrender.com/api/v1"`
- `EXPO_PUBLIC_SUPABASE_URL`: `"https://jndvnbvpwxhfmqgmqxfm.supabase.co"`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`: `"sb_publishable_VKlYXils1BGRr5znv9SZJg_C8cZtWUr"`

*Compatibility Note:* Because `EXPO_PUBLIC_API_URL` has `/api/v1` appended, all endpoints in `src/lib/api.ts` are resolved through the backend ASGI normalization middleware and dual-route mounts deployed in commits `6ff0a3e` and `e6877ef`.

---

## 5. Verification Verdict

```
================================================================================
STAGING ANDROID BUILD VERIFICATION: 100% PASS
Total Acceptance Gates: 7 | Passed: 7 | Failed: 0 | Blocked: 0
================================================================================
```
- **State:** SIGNED STANDALONE APK `a95a7169-d48b-4730-bcfd-921500e4b8fae` CERTIFIED AS STAGING BASELINE.
