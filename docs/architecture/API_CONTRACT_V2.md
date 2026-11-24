# MSGI ONE — API CONTRACT V2.0 (REST, WEBSOCKET & SSE)

**Document ID:** MSGI-API-V2-001  
**Phase:** Phase 1 — Requirements Engineering & Unified System Architecture  
**Compatibility Guarantee:** Preserves `/api/v1` and `/api/v1/api/v1` dual-prefix middleware and `StandardEnvelope[T]` for frozen Android APK `a95a7169-d48b-4730-bcfd-921500e4b8fae`.

---

## 1. Standard Response & Error Envelopes (Frozen Contract)

All REST endpoints return `StandardEnvelope`:
```json
{
  "status": "success | error",
  "data": "<payload or null>",
  "error": { "code": "STRING_CODE", "message": "Human readable", "details": [] },
  "meta": { "page": 1, "limit": 20, "total": 100 },
  "timestamp": "2026-11-24T18:00:00Z"
}
```
Preserved error codes: `UNAUTHENTICATED`, `INVALID_TOKEN_ALGORITHM`, `TOKEN_EXPIRED`, `INVALID_SIGNATURE`, `PERMISSION_DENIED`, `ADMIN_ROLE_REQUIRED`, `VALIDATION_ERROR`, `ENTITY_NOT_FOUND`, `CONFLICT`, `CAPACITY_EXCEEDED`, `WORKFLOW_AWAITING_APPROVAL`, `RATE_LIMITED`.

---

## 2. REST API Endpoints by Domain

### 2.1 Existing Preserved Endpoints (Phases 0–7 Baseline)
- `GET /health`, `GET /api/v1/health`, `GET /`
- `POST /api/v1/auth/bootstrap`
- `GET /api/v1/users/me`, `PATCH /api/v1/users/me`, `POST /api/v1/users/me/onboard`, `GET /api/v1/users/{id}`, `DELETE /api/v1/users/{id}`, plus `/api/v1/me*` direct aliases
- `GET /api/v1/alumni`, `GET /api/v1/alumni/search`, `GET /api/v1/alumni/{id}`
- `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `POST /api/v1/jobs`, `POST /api/v1/jobs/{id}/applications`, `GET /api/v1/me/applications`
- `GET /api/v1/mentors`, `GET /api/v1/mentors/{id}`, `POST /api/v1/mentor-requests`, `GET /api/v1/me/mentor-requests`, `PATCH /api/v1/mentor-requests/{id}`
- `GET /api/v1/events`, `POST /api/v1/events`, `POST /api/v1/events/{id}/registrations`, `GET /api/v1/me/event-registrations`, `DELETE /api/v1/events/{id}/registrations`
- `GET /api/v1/global/locations`, `GET /api/v1/global/chapters`
- `GET /api/v1/learning/*`, `GET /api/v1/communities/*`, `GET /api/v1/projects/*`, `GET /api/v1/startups/*`, `GET /api/v1/impact/*`
- `GET /api/v1/notifications`, `GET /api/v1/notifications/unread-count`, `PATCH /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/read-all`
- `GET /api/v1/admin/verifications`, `POST /api/v1/admin/verifications/{id}/decision`, `GET /api/v1/admin/summary`, `GET /api/v1/admin/audit-logs`
- `POST /api/v1/ai/chat`, `POST /api/v1/ai/workflows`, `GET /api/v1/ai/workflows/{session_id}`, `GET /api/v1/ai/approvals/pending`, `POST /api/v1/ai/approvals/{id}/decision`

### 2.2 Phase 3–4 Identity, Verification & Portal Extensions
- `POST /api/v1/auth/logout` — Revoke current session `jti` and optionally unregister device push token.
- `GET /api/v1/verifications/me` — Current user's verification status (`unverified`, `pending`, `approved`, `rejected`) & history.
- `POST /api/v1/verifications/me` — Submit alumni/faculty/recruiter institutional verification request (graduation year, degree, major, department, evidence).
- `PATCH /api/v1/alumni/me` — Verified alumnus updates career history, headline, bio, skills, mentorship availability, and privacy settings.
- `GET /api/v1/admin/users` — List users & roles (admin only).
- `POST /api/v1/admin/users/{user_id}/roles` — Provision/revoke role with audit logging (admin only).
- `GET /api/v1/admin/reports` & `PATCH /api/v1/admin/reports/{report_id}` — Moderation queue (admin only).
- `GET /api/v1/admin/announcements` & `POST /api/v1/admin/announcements` — Institutional announcements.
- `GET /api/v1/admin/status` — Operational health & subsystem readiness (admin only).

### 2.3 Phase 5 Scheduling & Meetings Endpoints
- `GET /api/v1/scheduling/availability/{alumni_user_id}` — Read permitted availability & generated open slots.
- `PUT /api/v1/scheduling/availability/me` — Alumnus sets recurring weekly schedule, IANA timezone, buffer minutes, and exceptions.
- `POST /api/v1/meetings/requests` — Submit meeting request (title, purpose, duration_minutes, up to 3 proposed UTC slots, `Idempotency-Key`).
- `GET /api/v1/meetings/requests` — List sent/received meeting requests.
- `POST /api/v1/meetings/requests/{request_id}/accept` — Accept a specific `slot_id` and atomically book meeting.
- `POST /api/v1/meetings/requests/{request_id}/decline` — Decline with optional reason.
- `POST /api/v1/meetings/requests/{request_id}/counter-propose` — Propose up to 3 alternative UTC slots.
- `POST /api/v1/meetings/requests/{request_id}/confirm` — Student confirms counter-proposed `slot_id`.
- `POST /api/v1/meetings/requests/{request_id}/cancel` — Cancel pending/counter-proposed request.
- `GET /api/v1/meetings` — Upcoming & past meetings for current user.
- `GET /api/v1/meetings/{meeting_id}` — Meeting detail.
- `POST /api/v1/meetings/{meeting_id}/reschedule` — Initiate rescheduling linked to prior meeting.
- `POST /api/v1/meetings/{meeting_id}/cancel` — Cancel confirmed meeting.
- `POST /api/v1/meetings/{meeting_id}/feedback` — Submit post-meeting rating/feedback.
- `GET /api/v1/meetings/{meeting_id}/ics` — Download RFC 5545 iCalendar invite.

### 2.4 Phase 6 Messaging & Safety Endpoints
- `GET /api/v1/conversations` — Paginated conversation list with unread counts & last message preview.
- `POST /api/v1/conversations` — Get or create 1-on-1 conversation (rejects if blocked).
- `GET /api/v1/conversations/{conversation_id}/messages` — Cursor-paginated durable message history (`after_seq` / `before_seq`).
- `POST /api/v1/conversations/{conversation_id}/messages` — REST fallback for offline queue flush (same service & idempotency key as WS).
- `POST /api/v1/conversations/{conversation_id}/read` — Advance read watermark.
- `POST /api/v1/conversations/{conversation_id}/attachments` — Validated attachment upload metadata.
- `POST /api/v1/safety/blocks` & `DELETE /api/v1/safety/blocks/{blocked_user_id}` — Block/unblock user.
- `POST /api/v1/safety/reports` — Report user or message for admin moderation.

### 2.5 Phase 7 LiveKit Audio/Video Rooms Endpoints
- `POST /api/v1/rooms/{meeting_id}/token` — Validate confirmed meeting, participant membership, join window, and block status; return short-lived LiveKit room token + room metadata.
- `POST /api/v1/rooms/{meeting_id}/admit` — Host admits waiting-room participant.
- `POST /api/v1/rooms/{meeting_id}/remove` — Host removes participant.
- `POST /api/v1/rooms/{meeting_id}/end` — Host terminates meeting room and transitions meeting to `COMPLETED`.
- `POST /api/v1/rooms/webhooks/livekit` — Signed LiveKit webhook receiver with signature check & event-id deduplication.

### 2.6 Phase 8 Multi-Provider AI Vault & SSE Streaming Endpoints
- `POST /api/v1/ai/chat/stream` — SSE stream (`text/event-stream`) emitting versioned JSON events.
- `GET /api/v1/admin/ai/providers` — List configured providers with masked key hints (`sk-...xxxx`), never plaintext keys.
- `POST /api/v1/admin/ai/providers` — Create/update provider config & AES-256-GCM encrypted key.
- `POST /api/v1/admin/ai/providers/{config_id}/verify` — Verify provider connectivity & capabilities.
- `PATCH /api/v1/admin/ai/providers/{config_id}` — Enable/disable, set primary/fallback, configure budgets.
- `DELETE /api/v1/admin/ai/providers/{config_id}` — Securely delete credential & audit.
- `GET /api/v1/admin/ai/usage` — Token, latency, and cost analytics from `ai_usage_ledger`.

### 2.7 Phase 9 Push Device Registration
- `POST /api/v1/devices/push-token` — Register/rotate Expo/FCM/APNs device token for authenticated user.
- `DELETE /api/v1/devices/push-token` — Unregister token on logout.

---

## 3. WebSocket Contract (`/ws/chat`)

Handshake: `wss://<host>/ws/chat?token=<jwt>` (or `Authorization: Bearer <jwt>` header).
Versioned Event Envelope (`v: "1.0"`):
```json
{
  "event_id": "evt-uuid",
  "event_type": "message.send | message.accepted | message.created | message.delivered | message.read | typing.started | typing.stopped | presence.changed | conversation.updated | connection.ready | connection.error",
  "schema_version": "1.0",
  "conversation_id": "conv-uuid-or-null",
  "sender_id": "user-uuid",
  "client_idempotency_key": "client-uuid-optional",
  "server_timestamp": "2026-11-24T18:00:00Z",
  "payload": {}
}
```

---

## 4. Server-Sent Events (SSE) Contract (`POST /api/v1/ai/chat/stream`)

Media type: `text/event-stream`. Event types:
- `run.started`: `{ "run_id", "session_id", "provider", "model" }`
- `agent.status`: `{ "agent", "status_text" }` (concise operational status only; zero internal CoT)
- `tool.started`: `{ "tool_name", "call_id" }`
- `tool.completed`: `{ "tool_name", "call_id", "status" }`
- `approval.required`: `{ "approval_id", "action_type", "target_entity_id", "target_entity_name", "validated_args", "expires_at" }`
- `response.delta`: `{ "text": "..." }`
- `citation`: `{ "entity_type", "entity_id", "label" }`
- `usage`: `{ "prompt_tokens", "output_tokens", "total_tokens", "estimated_cost_usd" }`
- `response.completed`: `{ "run_id", "status", "final_summary" }`
- `run.error`: `{ "code", "message", "retryable" }`
