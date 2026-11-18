# MSGI ONE — PHASE 5 ANDROID TOOLCHAIN & RELEASE ENGINEERING AUDIT

**Document Reference:** `docs/PHASE_5_ANDROID_BUILD_REPORT.md`  
**Mobile Toolchain:** Expo SDK 52, React Native 0.76.5, TypeScript 5.3  
**Package Identifier:** `edu.msgi.one`  
**Configuration Files:** `apps/mobile/app.json`, `apps/mobile/eas.json`  
**Status:** BUILD CONFIGURATION AUDITED & VALIDATED (Offline) / REMOTE CLOUD BUILD BLOCKED (Rule 20)  

---

## 1. ANDROID MANIFEST & APP CONFIGURATION (`app.json`)

```json
{
  "expo": {
    "name": "MSGI One",
    "slug": "msgi-one",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "automatic",
    "newArchEnabled": true,
    "splash": {
      "image": "./assets/splash-icon.png",
      "resizeMode": "contain",
      "backgroundColor": "#0F172A"
    },
    "android": {
      "package": "edu.msgi.one",
      "versionCode": 1,
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#0F172A"
      },
      "permissions": [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE"
      ]
    }
  }
}
```

### 1.1 Permissions Audit & Play Store Least-Privilege
- **Declared Permissions:**
  - `INTERNET`: Required for REST API communication.
  - `ACCESS_NETWORK_STATE`: Required to detect offline mode and render offline banner.
- **Dangerous Permissions Suppressed:**
  - `READ_MEDIA_IMAGES` / `CAMERA`: Not requested (avatar upload uses secure file picker).
  - `ACCESS_FINE_LOCATION`: Suppressed. Geolocation uses server-side coarse aggregation only.
  - `READ_CONTACTS`: Strictly prohibited under MSGI privacy charter.

---

## 2. EAS BUILD PROFILES (`eas.json`)

The EAS build pipeline defines three standard profiles:
1. **development:** Compiles a custom development client (`developmentClient: true`) for debugging on Android physical devices and emulators.
2. **preview:** Compiles a standalone APK (`buildType: "apk"`) for internal QA testing and institutional stakeholder distribution without requiring Google Play Store onboarding.
3. **production:** Compiles an optimized Android App Bundle (`buildType: "app-bundle"`) with full resource shrinking and ProGuard optimization.

---

## 3. GOOGLE PLAY TARGET SDK (API 35 vs API 36+) ANALYSIS

| Attribute | Local / Preview Config | Google Play Production Mandate (Late 2026) | Technical Action Required |
| :--- | :--- | :--- | :--- |
| **Expo SDK Version** | Expo SDK 52 | Expo SDK 53+ | Current build uses Expo SDK 52 (`react-native: 0.76.5`). Internal testing works cleanly. |
| **Target Android API** | API 35 (Android 15) | API 36+ (Android 16) | Google Play requires API level 36+ for new app submissions. Production Play Store distribution requires updating `targetSdkVersion` or upgrading to Expo SDK 53+. |
| **Distribution Format** | Standalone APK (`preview`) | Android App Bundle (`.aab`) | EAS is configured to produce `.aab` in `production` profile. |
| **Signing Credentials** | Debug / Local Keystore | Google Play App Signing Keystore | Cloud credentials blocked per Rule 20 until production deployment. |

---

## 4. EXTERNAL CLOUD BUILD BLOCKER (RULE 20)

In accordance with Rule 20 (`AGENTS.md`):
- Interactive `eas login`, `eas build --platform android`, and cloud credential generation require external user accounts, cloud credit billing, and unsandboxed network communication.
- **Release Status:** Remote EAS cloud execution is marked `BLOCKED per Rule 20`. All local Gradle/Expo manifests and profiles are syntactically and structurally verified for immediate execution upon credential provisioning.
