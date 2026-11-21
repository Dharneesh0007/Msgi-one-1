# MSGI ONE — TECHNICAL DEBT AND RISK AUDIT (GATE 6.7)
**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** 6 — PostgreSQL Persistence, Async Repository Architecture, and Legacy Android Compatibility  
**Document ID:** `docs/phase6/12_technical_debt_and_remaining_risks.md`  
**Execution Standard:** Executive Engineering Directive v2.0  
**Audit Baseline Commit:** `9b29883`  
**Status:** COMPLETE / VERIFIED  

---

## 1. Executive Summary

This report catalogues remaining architectural considerations, technical debt items, and operational risks identified during Phase 6 engineering execution.

### 1.1 Academic Engineering Grounding
- **Steve McConnell — *Code Complete* (2nd Edition):**
  - *Managing Technical Debt (McConnell, Ch. 28):* Intentional debt tracking, boundary containment, and risk retirement strategies.
- **Martin Kleppmann — *Designing Data-Intensive Applications*:**
  - *Distributed Systems & Operational Realities (Kleppmann, Ch. 8):* Connection pooling saturation, statement timeout governance, and transaction pooler limits.

---

## 2. Technical Debt & Residual Risk Inventory

| Item ID | Category | Description | Severity | Mitigation Strategy | Deferred Phase |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DEBT-01` | Connection Pooling | Staging connects to Supabase PgBouncer (port 6543) with `statement_cache_size: 0`. At extreme concurrent load (>1000 active mobile users), connection exhaustion can occur. | Medium | Implement Redis connection cache or pgbouncer server-side scaling. | Phase 8 |
| `DEBT-02` | Live LLM Integration | Command Centre LangGraph workflows use rule-based tools and fallbacks; live Gemini API keys remain decoupled from Phase 6 persistence. | Low | Connect live Gemini 2.0 Flash / Pro keys in dedicated AI Phase 7. | Phase 7 |
| `DEBT-03` | Mobile Polling Overhead | The frozen Android APK polls `/api/v1/notifications` periodically rather than relying exclusively on persistent WebSocket subscriptions. | Low | Preserved as baseline design to protect frozen APK compatibility; realtime overhaul in Phase 8. | Phase 8 |
| `DEBT-04` | Direct Aliases Mounting | Direct `/api/v1/me` aliases exist alongside `/api/v1/users/me` to prevent legacy mobile screen breakage. | Negligible | Intentionally preserved for backward compatibility. | None (Permanent) |
| `DEBT-05` | Double-Prefix Routing | ASGI middleware normalizes `/api/v1/api/v1` prefix originating from bundled mobile `EXPO_PUBLIC_API_URL`. | Low | Retained until next major APK rebuild (v0.2.0). | Phase 8 |

---

## 3. Certification

All remaining risks have identified mitigations and do not block production deployment or APK compatibility.
