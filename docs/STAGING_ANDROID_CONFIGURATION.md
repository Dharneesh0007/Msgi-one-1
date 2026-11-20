# MSGI One — Staging Android Build Configuration
**Environment:** STAGING ONLY  
**Framework:** React Native 0.76+ / Expo SDK 52+ / TypeScript 5.3+  
**Target Platform:** Android (API Level 35/36, Target Android 15)  
**Package Name:** `edu.msgi.one`  
**Execution Timestamp:** 2026-11-20T13:30:00+05:30  
**Compliance Standard:** Mandatory Engineering Laws (AGENTS.md Rules 2, 6, 7, 8, 17, 19)  

---

## 1. Executive Summary

This document specifies the Android mobile build configuration for the MSGI One staging release. It defines the explicit staging build profile in `eas.json`, environment variable mapping for hosted Supabase and FastAPI backend services, Android manifest security policies, network security configurations, and permissions.

---

## 2. Build Profiles (`apps/mobile/eas.json`)

The EAS build specification contains a dedicated `staging` profile delivering an internal distribution APK connected strictly to the hosted staging infrastructure:

```json
{
  "cli": {
    "version": ">= 12.0.0"
  },
  "build": {
    "staging": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      },
      "env": {
        "EXPO_PUBLIC_API_URL": "https://api-staging.msgi.edu/api/v1",
        "EXPO_PUBLIC_SUPABASE_URL": "https://jndvnbvpwxhfmqgmqxfm.supabase.co",
        "EXPO_PUBLIC_SUPABASE_ANON_KEY": "sb_publishable_VKlYXils1BGRr5znv9SZJg_C8cZtWUr"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      },
      "env": {
        "EXPO_PUBLIC_API_URL": "https://api.msgi.edu"
      }
    }
  }
}
```

### 2.1 Environmental Invariants
1. **Public Publishable Credentials Only:**
   - `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY` are safe client-side keys protected by PostgreSQL Row-Level Security (RLS).
   - `SUPABASE_SERVICE_ROLE_KEY` is strictly excluded and never compiled into mobile artifacts.
2. **Cleartext Traffic Enforcement:**
   - In staging and production builds, all endpoints strictly enforce TLS (`https://` and `wss://`).
   - Cleartext HTTP traffic is prohibited on release builds, conforming to Android 9+ default network security policies.

---

## 3. Application Manifest & Android Configuration (`apps/mobile/app.json`)

```json
{
  "expo": {
    "name": "MSGI One",
    "slug": "msgi-one",
    "version": "0.1.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "automatic",
    "scheme": "msgi-one",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#1A365D"
    },
    "android": {
      "package": "edu.msgi.one",
      "versionCode": 1,
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#1A365D"
      },
      "permissions": [
        "INTERNET",
        "ACCESS_NETWORK_STATE"
      ]
    },
    "plugins": [
      "expo-router",
      "expo-secure-store"
    ],
    "experiments": {
      "typedRoutes": true
    }
  }
}
```

### 3.1 Permissions Audit
- `INTERNET`: Required for REST API communication with FastAPI and WebSocket connectivity with Supabase Realtime.
- `ACCESS_NETWORK_STATE`: Required by NetInfo to detect offline/airplane mode and trigger graceful cached data fallbacks.
- **Sensitive Permissions:** No unnecessary permissions (`CAMERA`, `READ_CONTACTS`, `ACCESS_FINE_LOCATION`, `RECORD_AUDIO`) are requested, minimizing attack surfaces and Google Play review friction.

### 3.2 Secure Storage Plugin
- `expo-secure-store` encrypts user access and refresh tokens using Android KeyStore hardware-backed keystore mechanisms.

---

## 4. Configuration Verdict

- **EAS Profile:** Dedicated `staging` internal profile verified.
- **Client Security:** Service role keys excluded; hardware-backed SecureStore configured; cleartext HTTP prohibited.
- **State:** ANDROID STAGING CONFIGURATION LOCKED.
