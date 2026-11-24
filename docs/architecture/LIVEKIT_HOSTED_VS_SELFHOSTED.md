# MSGI ONE — LIVEKIT SFU DEPLOYMENT & EXPO SDK 52 COMPATIBILITY ANALYSIS

**Document ID:** MSGI-RTC-001  
**Phase:** Phase 7 — Real-Time Audio, Video & Screen Sharing  

## 1. LiveKit Hosted (Cloud) vs. Self-Hosted Evaluation

| Dimension | LiveKit Cloud (Managed) | Self-Hosted LiveKit Server (Docker / VM) |
| :--- | :--- | :--- |
| **Operational Complexity** | Low: managed SFU mesh, global edge routing, automatic TURN/TLS. | High: requires public UDP port ranges (50000–60000), TLS, TURN (coturn) for symmetric NATs, Redis coordination. |
| **Geographic Latency** | Multi-region edge PoPs minimize RTT for global alumni chapters (India, Japan, US). | Single-region unless multi-region cluster deployed manually. |
| **Cost Predictability** | Metered participant-minutes + bandwidth; free dev tier available for staging. | Fixed VM + egress bandwidth cost; lower at sustained high concurrency. |
| **Scaling** | Elastic automatic SFU scaling. | Manual/autoscaled node pool with Redis state. |
| **Authorization Status** | **NOT PROVISIONED** (requires explicit owner authorization & credentials `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`). | **NOT PROVISIONED** (Docker compose / staging setup covered in Phase 11). |

## 2. Expo SDK 52 & Native Platform Verification
- Installed via `npx expo install`: `@livekit/react-native@2.9.8`, `@livekit/react-native-webrtc@137.0.3`, `@livekit/react-native-expo-plugin@1.0.2`, `@config-plugins/react-native-webrtc@10.0.0` (verified `expo: ^52` peer compatibility), `livekit-client@2.15.8`.
- **Android:** Requires Expo Development Build / EAS native APK (NOT Expo Go). Uses `MediaProjection` + Android foreground service (`FOREGROUND_SERVICE_MEDIA_PROJECTION`) for screen sharing, controlled behind `ENABLE_SCREEN_SHARE_NATIVE` config flag.
- **iOS:** Screen sharing requires a ReplayKit Broadcast Upload Extension (`RTCScreenSharing` / App Group bundle) configured during EAS iOS prebuild; disabled on iOS unless Apple Developer provisioning & broadcast extension target are configured.
- **Privacy Invariant:** `recording_enabled` is strictly `false` by default; no audio/video or transcripts are captured automatically.
