"""
MSGI One — LiveKit SFU Meeting Room & Webhook Service (Phase 7)
Enforces:
  - Confirmed meeting validation, participant membership, join window, and user blocks via PermissionChecker.
  - Short-lived scoped LiveKit room tokens (livekit-api AccessToken when configured).
  - Waiting room admission, host removal, and meeting termination.
  - Signed webhook verification & event-id deduplication.
  - Recording strictly disabled by default.
Governing Textbooks: Kurose & Ross, WebRTC for the Curious, Silberschatz et al.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import threading
from typing import Any, Dict, Optional
import uuid
import jwt
from fastapi import HTTPException, status

from src.core.config import settings
from src.core.dependencies import AuthenticatedUser
from src.core.permissions import PermissionChecker
from src.schemas.rooms import (
    MeetingParticipantDTO,
    RoomStateResponse,
    RoomTokenRequest,
    RoomTokenResponse,
)
from src.services.messaging_service import is_pair_blocked
from src.services.scheduling_service import _MEETINGS_STORE, _emit_outbox_event

_ROOM_LOCK = threading.RLock()
_ROOMS_STORE: Dict[str, Dict[str, Any]] = {}  # meeting_id -> room dict
_PROCESSED_WEBHOOK_IDS: set[str] = set()


def _mint_livekit_jwt(
    room_name: str,
    user: AuthenticatedUser,
    is_host: bool,
    ttl_seconds: int = 3600,
) -> tuple[str, bool]:
    """
    Generate a short-lived LiveKit room JWT using livekit-api if configured,
    or return a scoped local signaling token marked livekit_configured=False.
    """
    if settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET:
        from livekit import api as lk_api
        grant = lk_api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
            room_admin=is_host,
        )
        token = (
            lk_api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(user.id)
            .with_name(f"{user.first_name or 'MSGI'} {user.last_name or 'Member'}".strip())
            .with_ttl(timedelta(seconds=ttl_seconds))
            .with_grants(grant)
            .to_jwt()
        )
        return token, True

    # Local dev / CI fallback token signed with app JWT secret (distinct claim so SFU is clearly unconfigured)
    now = datetime.now(timezone.utc)
    payload = {
        "iss": "msgi-local-rtc",
        "sub": user.id,
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "video": {
            "roomJoin": True,
            "room": room_name,
            "canPublish": True,
            "canSubscribe": True,
            "roomAdmin": is_host,
        },
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256"), False


def _get_or_create_room_for_meeting(meeting: Dict[str, Any]) -> Dict[str, Any]:
    meeting_id = meeting["id"]
    if meeting_id in _ROOMS_STORE:
        return _ROOMS_STORE[meeting_id]

    now = datetime.now(timezone.utc)
    room_id = f"room-{uuid.uuid4().hex[:10]}"
    room = {
        "room_id": room_id,
        "meeting_id": meeting_id,
        "room_name": f"msgi-mtg-{meeting_id[:12]}",
        "status": "waiting",
        "host_user_id": meeting["alumni_id"],
        "waiting_room_enabled": True,
        "recording_enabled": False,  # Strictly disabled by default
        "participants": {},
        "started_at": None,
        "ended_at": None,
        "expires_at": meeting["scheduled_end"] + timedelta(minutes=45),
        "created_at": now,
    }
    _ROOMS_STORE[meeting_id] = room
    return room


def request_room_token(
    user: AuthenticatedUser,
    meeting_id: str,
    payload: RoomTokenRequest,
    now_override: Optional[datetime] = None,
) -> RoomTokenResponse:
    meeting = _MEETINGS_STORE.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting not found."})

    blocked = is_pair_blocked(meeting["student_id"], meeting["alumni_id"])
    PermissionChecker.verify_meeting_room_access(
        user_id=user.id,
        student_id=meeting["student_id"],
        alumni_id=meeting["alumni_id"],
        meeting_status=meeting["status"],
        scheduled_start=meeting["scheduled_start"],
        scheduled_end=meeting["scheduled_end"],
        is_blocked=blocked,
        now=now_override,
    )

    with _ROOM_LOCK:
        room = _get_or_create_room_for_meeting(meeting)
        if room["status"] in ("ended", "expired"):
            raise HTTPException(status_code=403, detail={"code": "ROOM_ENDED", "message": "This meeting room has already ended."})

        is_host = user.id == room["host_user_id"]
        existing_part = room["participants"].get(user.id)
        if existing_part and existing_part["admission_status"] == "removed":
            raise HTTPException(status_code=403, detail={"code": "PARTICIPANT_REMOVED", "message": "You were removed from this meeting room."})

        admission = "admitted" if (is_host or not room["waiting_room_enabled"]) else (
            existing_part["admission_status"] if existing_part else "waiting"
        )
        now = now_override or datetime.now(timezone.utc)

        room["participants"][user.id] = {
            "user_id": user.id,
            "role": "host" if is_host else "participant",
            "admission_status": admission,
            "audio_enabled": payload.audio_enabled,
            "video_enabled": payload.video_enabled,
            "screen_sharing": False,
            "joined_at": now if admission == "admitted" else None,
        }

        if is_host and room["status"] == "waiting":
            room["status"] = "active"
            room["started_at"] = now
            meeting["status"] = "in_progress"
            meeting["updated_at"] = now
            _emit_outbox_event("meeting", meeting_id, "meeting.started", {"meeting_id": meeting_id, "room_id": room["room_id"]})

        token_str, lk_configured = _mint_livekit_jwt(room["room_name"], user, is_host=is_host)
        return RoomTokenResponse(
            room_id=room["room_id"],
            meeting_id=meeting_id,
            room_name=room["room_name"],
            livekit_url=settings.LIVEKIT_URL,
            token=token_str,
            role="host" if is_host else "participant",
            admission_status=admission,
            waiting_room_enabled=room["waiting_room_enabled"],
            recording_enabled=False,
            livekit_configured=lk_configured,
            expires_at=room["expires_at"],
        )


def get_room_state(user: AuthenticatedUser, meeting_id: str) -> RoomStateResponse:
    meeting = _MEETINGS_STORE.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting not found."})
    if user.id not in (meeting["student_id"], meeting["alumni_id"]) and "admin" not in user.roles:
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Access denied."})

    room = _get_or_create_room_for_meeting(meeting)
    return RoomStateResponse(
        room_id=room["room_id"],
        meeting_id=meeting_id,
        room_name=room["room_name"],
        status=room["status"],
        host_user_id=room["host_user_id"],
        waiting_room_enabled=room["waiting_room_enabled"],
        recording_enabled=room["recording_enabled"],
        participants=[MeetingParticipantDTO(**p) for p in room["participants"].values()],
        started_at=room.get("started_at"),
        ended_at=room.get("ended_at"),
        expires_at=room["expires_at"],
    )


def admit_participant(host: AuthenticatedUser, meeting_id: str, target_user_id: str) -> RoomStateResponse:
    with _ROOM_LOCK:
        room = _ROOMS_STORE.get(meeting_id)
        if not room:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Room not found."})
        if room["host_user_id"] != host.id:
            raise HTTPException(status_code=403, detail={"code": "HOST_ONLY", "message": "Only the meeting host can admit participants."})
        part = room["participants"].get(target_user_id)
        if not part:
            raise HTTPException(status_code=404, detail={"code": "PARTICIPANT_NOT_FOUND", "message": "Participant not in waiting room."})
        part["admission_status"] = "admitted"
        part["joined_at"] = datetime.now(timezone.utc)
        return get_room_state(host, meeting_id)


def remove_participant(host: AuthenticatedUser, meeting_id: str, target_user_id: str) -> RoomStateResponse:
    with _ROOM_LOCK:
        room = _ROOMS_STORE.get(meeting_id)
        if not room:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Room not found."})
        if room["host_user_id"] != host.id:
            raise HTTPException(status_code=403, detail={"code": "HOST_ONLY", "message": "Only the meeting host can remove participants."})
        if target_user_id == host.id:
            raise HTTPException(status_code=400, detail={"code": "INVALID_TARGET", "message": "Host cannot remove themselves."})
        part = room["participants"].get(target_user_id)
        if not part:
            raise HTTPException(status_code=404, detail={"code": "PARTICIPANT_NOT_FOUND", "message": "Participant not found."})
        part["admission_status"] = "removed"
        return get_room_state(host, meeting_id)


def end_meeting_room(host: AuthenticatedUser, meeting_id: str) -> RoomStateResponse:
    with _ROOM_LOCK:
        meeting = _MEETINGS_STORE.get(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting not found."})
        room = _get_or_create_room_for_meeting(meeting)
        if room["host_user_id"] != host.id and "admin" not in host.roles:
            raise HTTPException(status_code=403, detail={"code": "HOST_ONLY", "message": "Only the host can end the meeting."})

        now = datetime.now(timezone.utc)
        room["status"] = "ended"
        room["ended_at"] = now
        meeting["status"] = "completed"
        meeting["updated_at"] = now

        duration_secs = int((now - (room.get("started_at") or now)).total_seconds())
        _emit_outbox_event("meeting", meeting_id, "meeting.completed", {
            "meeting_id": meeting_id,
            "room_id": room["room_id"],
            "duration_seconds": max(0, duration_secs),
        })
        return get_room_state(host, meeting_id)


def process_livekit_webhook(raw_body: bytes, auth_header: Optional[str]) -> Dict[str, Any]:
    """
    Verify LiveKit signed webhook (JWT Authorization header carrying sha256 of body)
    and deduplicate repeated webhook deliveries by event ID.
    """
    secret = settings.LIVEKIT_API_SECRET or settings.SUPABASE_JWT_SECRET
    if not auth_header:
        raise HTTPException(status_code=401, detail={"code": "MISSING_WEBHOOK_SIGNATURE", "message": "Webhook Authorization header missing."})

    token = auth_header.split(None, 1)[1] if auth_header.lower().startswith("bearer ") else auth_header
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
    except Exception as exc:
        raise HTTPException(status_code=401, detail={"code": "INVALID_WEBHOOK_SIGNATURE", "message": f"Invalid webhook signature: {exc}"})

    expected_sha256 = hashlib.sha256(raw_body).hexdigest()
    claim_hash = claims.get("sha256")
    if claim_hash and claim_hash != expected_sha256:
        raise HTTPException(status_code=401, detail={"code": "WEBHOOK_BODY_HASH_MISMATCH", "message": "Webhook body digest mismatch."})

    payload = json.loads(raw_body.decode("utf-8"))
    event_id = payload.get("id") or hashlib.sha256(raw_body).hexdigest()[:16]
    if event_id in _PROCESSED_WEBHOOK_IDS:
        return {"processed": False, "deduplicated": True, "event_id": event_id}

    _PROCESSED_WEBHOOK_IDS.add(event_id)
    event_name = payload.get("event", "unknown")
    room_name = (payload.get("room") or {}).get("name")
    if event_name == "room_finished" and room_name:
        for room in _ROOMS_STORE.values():
            if room["room_name"] == room_name and room["status"] != "ended":
                room["status"] = "ended"
                room["ended_at"] = datetime.now(timezone.utc)

    return {"processed": True, "deduplicated": False, "event_id": event_id, "event": event_name}
