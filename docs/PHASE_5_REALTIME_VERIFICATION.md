# MSGI ONE — PHASE 5 REALTIME NOTIFICATION & EVENT BUS AUDIT

**Document Reference:** `docs/PHASE_5_REALTIME_VERIFICATION.md`  
**Phase:** Phase 5 — Quality Assurance & Release Readiness  
**Target Environment:** Local REST Event Bus / Cloud Supabase Realtime Channels  
**Audit Standard:** Kleppmann Distributed Data Systems & Sommerville Component Architecture  
**Status:** VERIFIED OFFLINE / LIVE WEBSOCKET BLOCKED (Rule 20)  

---

## 1. DUAL-MODE ARCHITECTURAL DESIGN

To ensure zero developer friction and reliable offline testability, the MSGI One notification system operates under a **Dual-Mode Event Delivery Architecture**:

```mermaid
flowchart TD
    subgraph ClientLayer["Mobile Client (Expo SDK 52)"]
        UI["Notifications Hub UI"]
        Sub["Supabase Realtime Channel (apps/mobile/src/services/realtime.ts)"]
        Poll["REST Polling Fallback (GET /api/v1/notifications)"]
    end

    subgraph BackendLayer["FastAPI Service Layer"]
        DomainEvt["Domain Action (Mentorship, Application, Community)"]
        NotifService["notifications_service.create_notification()"]
        NotifStore["_NOTIFICATIONS_STORE (In-Memory / Postgres)"]
    end

    DomainEvt --> NotifService
    NotifService --> NotifStore
    NotifStore -.->|Live Cloud Mode (PostgreSQL CDC)| Sub
    NotifStore -->|Offline Dev Mode (REST Polling)| Poll
    Sub --> UI
    Poll --> UI
```

---

## 2. TWO-USER EVENT FLOW VERIFICATION

The two-user notification workflow was verified in `tests/test_phase_5_qa_e2e.py` under test scenario `test_wf001_mentorship_lifecycle`:

1. **Event Trigger:** Student (`user-student-001`) initiates a mentorship request to Mentor (`user-kenji-001`).
2. **Notification Emission:** Domain service calls `create_notification()`:
   - Target User ID: `user-kenji-001`
   - Event Type: `mentorship_requested`
   - Title: `New Mentorship Request`
   - Entity ID: `req-1`
3. **Delivery & Inbox Isolation:**
   - Mentor queries inbox via `get_my_notifications(user=mentor)`: Notification is present with `is_read = False`.
   - Student queries inbox via `get_my_notifications(user=student)`: Notification is **not present** (100% user isolation).
4. **Read Acknowledgment:**
   - Mentor marks notification as read via `mark_notification_as_read(notif_id, user=mentor)`.
   - Status updates atomically to `is_read = True`, `read_at = ISO-8601 Timestamp`.

---

## 3. SECURITY & OWNERSHIP AUDIT

- **Cross-User Leakage Defense:**
  - Evaluated in `tests/test_phase_5_security_compliance.py::test_sec003_cross_user_notification_isolation`.
  - When User A attempts to acknowledge or retrieve User B's notification ID, the service raises `HTTP 403 Forbidden` (`PERMISSION_DENIED`).
- **Live Supabase Realtime Channels:**
  - `apps/mobile/src/services/realtime.ts` implements standard Supabase Realtime subscription:
    ```typescript
    supabase.channel('public:notifications:user_id=eq.' + userId)
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'notifications' }, handleNewNotification)
      .subscribe();
    ```
  - Status: Offline development cleanly uses REST polling (`/api/v1/notifications`). Live WebSocket connection is marked `BLOCKED per Rule 20` due to absence of external cloud Supabase credentials.
