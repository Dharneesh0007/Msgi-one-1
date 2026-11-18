# MSGI One — Phase 4 Realtime Architecture & Notification Design

**Project:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Target Environment:** Windows, Expo SDK 52, FastAPI, Supabase Realtime / PostgreSQL  
**Engineering Standards:** Martin Kleppmann *Designing Data-Intensive Applications*, Ian Sommerville *Software Engineering*  

---

## 1. Architectural Overview

The MSGI One Realtime Notification System guarantees reliable, authenticated event propagation across distributed actors (Students, Mentors, Alumni Founders, and Institutional Administrators). It connects business events dispatched by domain services to persistent notifications and mobile client state.

```
+-----------------------------------------------------------------------------------+
|                              EVENT PRODUCERS                                      |
|  - Learning Academy (Milestone Completed)       - Startup Intro Requests          |
|  - Communities (Membership Requests/Decisions)  - Admin Verification Decisions    |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                        NOTIFICATIONS DOMAIN SERVICE                               |
|              (services/api/src/services/notifications_service.py)                 |
|  - Validates user recipient id                                                    |
|  - Enforces schema invariants                                                     |
|  - Persists record with event_type, title, message, payload                       |
+------------------------------------------+----------------------------------------+
                                           |
                    +----------------------+----------------------+
                    |                                             |
                    v                                             v
+---------------------------------------+     +-------------------------------------+
|        DATABASE PERSISTENCE           |     |     REALTIME STREAM DISPATCH        |
|        public.notifications           |     |    (Supabase Realtime / WebSocket)  |
|  - Row Level Security (RLS)           |     |  - User-specific channel:           |
|  - User isolation: auth.uid()=user_id |     |    notifications:{user_id}          |
|  - Index: (user_id, is_read, time)    |     |  - Graceful fallback: Polling/REST  |
+---------------------------------------+     +-------------------------------------+
                    |                                             |
                    +----------------------+----------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                               MOBILE CONSUMER                                     |
|               (apps/mobile/src/app/(tabs)/index.tsx Services Hub)                 |
|  - Unread badge counter updates                                                   |
|  - Realtime alert card stream                                                     |
|  - Mark-as-read acknowledgement action                                            |
+-----------------------------------------------------------------------------------+
```

---

## 2. Notification Data Model

The notification entity is defined in `supabase/migrations/20261121000001_phase_4_extended_modules.sql`:

```sql
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread 
ON public.notifications(user_id, is_read, created_at DESC);
```

### Supported Event Types
1. `course_enrolled`: Dispatched when a student enrolls in a learning resource.
2. `course_completed`: Dispatched when course progress reaches 100%.
3. `community_joined`: Dispatched when a member joins a public guild.
4. `community_membership_requested`: Dispatched to community creator when a private group join is requested.
5. `community_membership_decided`: Dispatched to applicant upon moderator approval or rejection.
6. `startup_connection_requested`: Dispatched to alumni founder when a student requests mentorship or collaboration.
7. `volunteering_registered`: Dispatched upon confirming interest in an institutional social impact programme.
8. `verification_decided`: Dispatched to user upon administrative credential approval/rejection.

---

## 3. Security and User Isolation (Row-Level Security)

To satisfy MSGI Security Policies and prevent unauthorized eavesdropping:
1. **User Isolation Policy:**
   ```sql
   CREATE POLICY "Users can view their own notifications"
   ON public.notifications FOR SELECT
   USING (auth.uid() = user_id);

   CREATE POLICY "Users can update their own notification read status"
   ON public.notifications FOR UPDATE
   USING (auth.uid() = user_id);
   ```
2. **API Endpoint Guard:**
   `PUT /api/v1/notifications/{id}/read` validates `notif.user_id == authenticated_user.id`. Any attempt by User A to alter User B's notification returns `403 FORBIDDEN` (verified in `test_notification_lifecycle_and_security`).

---

## 4. Two-Client Event Flow Verification

The system was verified under test `test_two_client_realtime_event_propagation` in `services/api/tests/test_phase_4_modules.py`:
- **Step 1:** Client A (Student) submits a connection request to startup `start-neural-001`.
- **Step 2:** The startup service resolves the founder (`user-kenji-001`) and invokes `create_notification()`.
- **Step 3:** Client B (Alumni Founder) polls `/api/v1/notifications/unread-count`. The unread count increments by 1.
- **Step 4:** Client B retrieves `/api/v1/me/notifications` and receives the structured payload containing `startup_connection_requested`.

---

## 5. Offline & Network Resilience Strategy

In production, Supabase Realtime utilizes WebSockets on `wss://<project>.supabase.co/realtime/v1/websocket`. However, institutional campus firewalls or offline environments may disrupt socket connections:
- **Resilience Mechanism:** The mobile application implements optimistic UI updates paired with resilient background polling. When socket heartbeats fail, the client polls `/api/v1/notifications/unread-count` upon dashboard pull-to-refresh or navigation focus events.
- **Sandboxed Execution Compliance:** In testing environments without open external sockets, all notification stores execute synchronously in-memory, ensuring 100% deterministic test execution.
