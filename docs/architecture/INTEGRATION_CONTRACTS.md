# MSGI ONE — CROSS-PHASE INTEGRATION CONTRACTS

**Document ID:** MSGI-INT-001  
**Date:** November 24, 2026  

## 1. Canonical Domain Event Taxonomy (Section F3)
All durable domain events emitted to `outbox_events` and internal subscribers use versioned JSON payloads (`schema_version: "1.0"`):
- `user.verified` (`{ user_id, approved_role, decided_by }`)
- `mentor.requested` (`{ request_id, student_id, mentor_id }`)
- `mentor.accepted` (`{ request_id, student_id, mentor_id }`)
- `meeting.requested` (`{ meeting_request_id, student_id, alumni_id, slot_count }`)
- `meeting.counter_proposed` (`{ meeting_request_id, alumni_id, student_id, slot_count }`)
- `meeting.scheduled` (`{ meeting_id, meeting_request_id, student_id, alumni_id, scheduled_start, scheduled_end }`)
- `meeting.cancelled` (`{ meeting_id, cancelled_by, reason }`)
- `meeting.started` (`{ meeting_id, room_id }`)
- `meeting.completed` (`{ meeting_id, room_id, duration_seconds }`)
- `message.created` (`{ message_id, conversation_id, sender_id, seq }`)
- `message.read` (`{ conversation_id, reader_id, last_read_seq }`)
- `agent.approval_required` (`{ approval_id, run_id, user_id, action_type, expires_at }`)
- `agent.action_completed` (`{ approval_id, run_id, user_id, action_type, status }`)

## 2. Shared Integration Rules
- **UTC Timestamps:** All persisted and wire timestamps use timezone-aware ISO-8601 UTC (`TIMESTAMPTZ`). User IANA timezone is stored separately (`alumni_availability.timezone`, `meeting_requests.student_timezone`) for local display and recurring rule expansion.
- **UUIDs & Idempotency:** All new entities use 36-char UUID v4 strings; mutating endpoints and WS `message.send` support `Idempotency-Key` backed by `idempotency_keys`.
- **Single Authorization Gateway:** `src/core/permissions.py` (`PermissionChecker`) is shared by REST routers, WebSocket connections, LiveKit room token minting, and AI tools.
- **AI Tool Surface:** Every domain service exposes narrow, typed, authenticated functions for AI agents without granting raw repository or SQL access.
