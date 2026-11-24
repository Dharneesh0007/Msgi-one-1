# ADR-004: LiveKit WebRTC SFU & Expo SDK 52 Compatibility Strategy

- **Status:** Accepted (Phase 1 — Subject to Native Build Verification in Phase 7)
- **Requirement ID:** FR-RTC-01..04
- **Governing Textbooks:** *WebRTC for the Curious*, Kurose & Ross (*Computer Networking*, 8th Ed.), Silberschatz et al. (*Operating System Concepts*, 10th Ed.).
- **Decision:** Adopt LiveKit SFU (`livekit-api` on FastAPI backend; `@livekit/react-native` + `livekit-client` on Expo SDK 52) with backend-minted short-lived room tokens, signed webhook verification + deduplication, and no default recording.
- **Compatibility Policy:** Expo Go does NOT support native WebRTC modules; Expo Development Builds / EAS native Android builds are required. Before integrating native screen-share plugins in Phase 7, verify exact Gradle/Kotlin/minSdkVersion compatibility with Expo SDK 52 (`kotlinVersion: 1.9.25` in `app.json`) and isolate screen-share extension flags cleanly so Android EAS builds never break.
- **Alternatives Considered:** Peer-to-peer mesh WebRTC or external meeting links (Zoom/Meet). Rejected due to poor multi-party scaling/NAT traversal in mesh and loss of in-app privacy/admission control with external apps.
- **Verification Tests:** Phase 7 room authorization & webhook tests; native build verification via `expo export` & EAS prebuild/build checks.
- **Known Limitations:** Live audio/video/screen-sharing hardware verification requires two physical/emulator dev-build devices and LiveKit credentials; marked `BLOCKED` in headless CI if absent.
