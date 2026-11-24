# MSGI ONE — PHASE DEPENDENCY GRAPH & EXECUTION PLAN

**Document ID:** MSGI-PDG-001  
**Date:** November 24, 2026  

```mermaid
flowchart TD
    P0["Phase 0: Forensic Audit (VERIFIED_EXECUTION: 184 pytest, 0 tsc errors)"] --> P1["Phase 1: Requirements & Architecture V2"]
    P1 --> P2["Phase 2: Database Schema & Async Repositories"]
    P1 --> P3A["Phase 3 Foundational Identity & Security"]
    P2 --> P3["Phase 3: Identity, RBAC, Privacy & Security"]
    P3A --> P3
    P2 --> P4["Phase 4: Student, Alumni & Admin Portals"]
    P3 --> P4
    P4 --> P5["Phase 5: Mentorship, Availability & Meeting Scheduling"]
    P3 --> P6["Phase 6: Real-Time 1-on-1 Messaging (WS + Redis)"]
    P4 --> P6
    P5 --> P6
    P3 --> P7["Phase 7: LiveKit Audio, Video & Screen Sharing"]
    P5 --> P7
    P2 & P3 & P4 & P5 & P6 & P7 --> P8["Phase 8: Agentic AI & Encrypted Multi-Provider Vault"]
    P4 & P5 & P6 & P7 & P8 --> P9["Phase 9: Mobile Modernization (TanStack Query, FlashList, Biometrics, Push, Offline)"]
    P9 --> P10["Phase 10: Integrated E2E Testing, Negative Tests & Benchmarks"]
    P10 --> P11["Phase 11: DevOps, CI/CD & Production Readiness"]
    P11 --> P12["Phase 12: Continuous Evolution, AI & Operational Governance"]
```

## Checkpoint Grouping
- **Checkpoint A:** Phases 1–4 (Architecture, DB Foundation, Identity/Security, Student/Alumni/Admin Portals)
- **Checkpoint B:** Phases 5–7 (Scheduling Engine, WebSocket Messaging, LiveKit Audio/Video)
- **Checkpoint C:** Phases 8–12 (Agentic AI + Encrypted Vault + Streaming, Mobile Modernization, E2E QA & Benchmarks, DevOps, Governance)
