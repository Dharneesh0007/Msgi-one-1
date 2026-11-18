# MSGI One — Android Release Readiness & EAS Build Audit

**Project:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Target Platform:** Android (Expo SDK 52 / React Native 0.76.5)  
**Deliverable Type:** Release Pipeline Specification & Play Store Readiness Audit  
**Engineering Standards:** Google Play Developer Policy, Pressman Software Quality Assurance  

---

## 1. EAS Build Configuration

The mobile release pipeline is codified in `apps/mobile/eas.json`:

```json
{
  "cli": {
    "version": ">= 14.0.0",
    "appVersionSource": "remote"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  },
  "submit": {
    "production": {
      "android": {
        "serviceAccountKeyPath": "./google-services-key.json",
        "track": "internal"
      }
    }
  }
}
```

### Profile Responsibilities
1. **`development`**: Builds an Android debug APK containing the Expo Dev Client for local emulator testing and rapid hot-reloading.
2. **`preview`**: Generates a self-contained release APK for internal QA and institutional test devices without requiring Play Store distribution.
3. **`production`**: Produces an optimized Android App Bundle (`.aab`) targetted at Google Play Store internal/closed testing tracks.

---

## 2. App Manifest & Permissions Audit (`app.json`)

```json
{
  "expo": {
    "name": "MSGI One",
    "slug": "msgi-one",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#1E3A8A"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#1E3A8A"
      },
      "package": "edu.msgi.one",
      "permissions": [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE"
      ]
    }
  }
}
```

### Key Security & Configuration Decisions
- **Minimal Permissions:** Only `INTERNET` and `ACCESS_NETWORK_STATE` are declared. No dangerous runtime permissions (e.g. `ACCESS_FINE_LOCATION`, `CAMERA`, `READ_CONTACTS`, `RECORD_AUDIO`) are requested.
- **Institutional Namespace:** Android package identifier set to `edu.msgi.one`.
- **Target SDK Compliance:** Built with Expo SDK 52 targeting Android 15 (API level 35), fully exceeding Google Play's minimum API level 34 requirement.

---

## 3. Google Play Store Release Gates

| Release Gate | Requirement | Current Status | Remediation / Next Steps |
|---|---|---|---|
| **Gate 1: Target API Level** | Android 14+ (API 34+) | ✅ **PASSED** | Expo SDK 52 compiles against API 35. |
| **Gate 2: Package Format** | Android App Bundle (`.aab`) | ✅ **CONFIGURED** | Configured in `eas.json` under `production.android.buildType: "app-bundle"`. |
| **Gate 3: Code Signing** | Production Keystore | ⚠️ **PENDING CREDENTIAL** | To be generated during `eas build --platform android --profile production` or provided by institutional devops. |
| **Gate 4: Privacy Policy URL** | Publicly accessible URL | ⚠️ **PENDING DEPLOYMENT** | Must point to institutional domain (e.g. `https://msgi.edu/privacy`). |
| **Gate 5: Data Safety Form** | Data collection disclosure | ✅ **AUDITED** | App collects: User profile (name, degree, email), App interactions (audit logs). Transmitted over HTTPS. |
| **Gate 6: Human Approval Safety** | Rule 15 Compliance | ✅ **PASSED** | Autonomous agents cannot trigger mutations without user consent. |
| **Gate 7: Payment Policy** | Play Billing Compliance | ✅ **PASSED** | Zero live payment processing or monetization endpoints exist. Giving module is volunteering only. |

---

## 4. Execution Commands for Release Engineer

To build and distribute the Android release:
```bash
# 1. Authenticate with Expo Application Services (outside sandbox)
npx eas-cli login

# 2. Build Internal QA APK
npx eas-cli build --platform android --profile preview

# 3. Build Production Android App Bundle
npx eas-cli build --platform android --profile production

# 4. Submit to Google Play Console Internal Track
npx eas-cli submit --platform android --profile production
```
