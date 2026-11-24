"""
MSGI One — Transactional Mentorship & Meeting Scheduling Engine (Phase 5)
Implements:
  - Recurring IANA-timezone availability & exception evaluation
  - Multi-slot meeting proposals (up to 3 slots), acceptance, decline, counter-proposals, confirmation
  - Strict state machines for meeting_requests and meetings
  - Atomic double-booking & buffer-conflict protection + idempotency deduplication
  - Rescheduling (replacement linkage), cancellation, no-show, feedback, and .ics calendar export
  - AI tool read/draft contracts (Rule 15 HITL compatible)
Governing Textbooks: Elmasri & Navathe, Martin Kleppmann, Silberschatz et al., Sommerville.
"""

from datetime import date, datetime, time, timedelta, timezone
import threading
from typing import Any, Dict, List, Optional
import uuid
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status

from src.core.dependencies import AuthenticatedUser
from src.core.permissions import PermissionChecker
from src.schemas.scheduling import (
    AvailabilityUpdateRequest,
    AvailabilityWindowResponse,
    MeetingCancelRequest,
    MeetingFeedbackRequest,
    MeetingRequestAccept,
    MeetingRequestConfirm,
    MeetingRequestCounterPropose,
    MeetingRequestCreate,
    MeetingRequestDecline,
    MeetingRequestResponse,
    MeetingRescheduleRequest,
    MeetingResponse,
    MeetingSlotResponse,
    OpenSlotDTO,
)
from src.services.alumni_service import _SYNTHETIC_ALUMNI_STORE
from src.services.notifications_service import create_notification

# Thread-safe lock preventing concurrent double-booking races inside the modular monolith
_BOOKING_LOCK = threading.RLock()

# Canonical stores (mirroring Phase 2 relational schema)
_AVAILABILITY_STORE: Dict[str, List[Dict[str, Any]]] = {
    "user-kenji-001": [
        {
            "id": "avail-kenji-tue",
            "alumni_id": "user-kenji-001",
            "day_of_week": 1,
            "start_time_local": "10:00",
            "end_time_local": "13:00",
            "timezone": "Asia/Tokyo",
            "slot_duration_minutes": 30,
            "buffer_minutes": 10,
            "exceptions": [],
        },
        {
            "id": "avail-kenji-thu",
            "alumni_id": "user-kenji-001",
            "day_of_week": 3,
            "start_time_local": "14:00",
            "end_time_local": "17:00",
            "timezone": "Asia/Tokyo",
            "slot_duration_minutes": 30,
            "buffer_minutes": 10,
            "exceptions": [],
        },
    ],
    "user-ananya-002": [
        {
            "id": "avail-ananya-wed",
            "alumni_id": "user-ananya-002",
            "day_of_week": 2,
            "start_time_local": "15:00",
            "end_time_local": "18:00",
            "timezone": "Asia/Kolkata",
            "slot_duration_minutes": 30,
            "buffer_minutes": 10,
            "exceptions": [],
        }
    ],
}

_MEETING_REQUESTS_STORE: Dict[str, Dict[str, Any]] = {}
_MEETINGS_STORE: Dict[str, Dict[str, Any]] = {}
_SCHEDULING_IDEMPOTENCY: Dict[str, str] = {}  # (user_id:key) -> request_id
_SCHEDULING_OUTBOX: List[Dict[str, Any]] = []


def _to_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _resolve_alumni_record(alumni_id_or_user_id: str) -> Optional[Dict[str, Any]]:
    return next(
        (
            a
            for a in _SYNTHETIC_ALUMNI_STORE
            if a["id"] == alumni_id_or_user_id
            or a["user_id"] == alumni_id_or_user_id
            or a.get("db_id") == alumni_id_or_user_id
            or a.get("db_user_id") == alumni_id_or_user_id
        ),
        None,
    )


def _resolve_display_name(user_id: str, fallback: str = "Institutional Member") -> str:
    alum = _resolve_alumni_record(user_id)
    if alum:
        return alum["full_name"]
    return fallback


def _get_alumni_buffer_minutes(alumni_user_id: str) -> int:
    windows = _AVAILABILITY_STORE.get(alumni_user_id) or []
    if windows:
        return max(int(w.get("buffer_minutes", 10)) for w in windows)
    return 10


def _has_conflict(
    user_id: str,
    start_utc: datetime,
    end_utc: datetime,
    buffer_minutes: int = 0,
    exclude_meeting_id: Optional[str] = None,
) -> bool:
    buf = timedelta(minutes=buffer_minutes)
    chk_start = _to_utc(start_utc) - buf
    chk_end = _to_utc(end_utc) + buf

    for m in _MEETINGS_STORE.values():
        if exclude_meeting_id and m["id"] == exclude_meeting_id:
            continue
        if m["status"] not in ("scheduled", "in_progress"):
            continue
        if m["alumni_id"] != user_id and m["student_id"] != user_id:
            continue
        m_start = _to_utc(m["scheduled_start"])
        m_end = _to_utc(m["scheduled_end"])
        if m_start < chk_end and m_end > chk_start:
            return True
    return False


def _emit_outbox_event(aggregate_type: str, aggregate_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    _SCHEDULING_OUTBOX.append({
        "id": f"outbox-{uuid.uuid4().hex[:10]}",
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "event_type": event_type,
        "schema_version": "1.0",
        "payload": payload,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


def set_alumni_availability(
    alumni: AuthenticatedUser,
    payload: AvailabilityUpdateRequest,
) -> List[AvailabilityWindowResponse]:
    PermissionChecker.require_verified_alumni(alumni.roles, alumni.is_verified)

    stored: List[Dict[str, Any]] = []
    for w in payload.windows:
        stored.append({
            "id": f"avail-{uuid.uuid4().hex[:10]}",
            "alumni_id": alumni.id,
            "day_of_week": w.day_of_week,
            "start_time_local": w.start_time_local,
            "end_time_local": w.end_time_local,
            "timezone": w.timezone,
            "slot_duration_minutes": w.slot_duration_minutes,
            "buffer_minutes": w.buffer_minutes,
            "exceptions": [e.model_dump() for e in w.exceptions],
        })
    _AVAILABILITY_STORE[alumni.id] = stored
    return [AvailabilityWindowResponse(**item) for item in stored]


def get_alumni_availability_and_slots(
    alumni_id: str,
    days_ahead: int = 7,
    from_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    alum = _resolve_alumni_record(alumni_id)
    target_user_id = alum["user_id"] if alum else alumni_id
    windows = _AVAILABILITY_STORE.get(target_user_id, [])

    base_now = _to_utc(from_utc) if from_utc else datetime.now(timezone.utc)
    open_slots: List[OpenSlotDTO] = []

    for w in windows:
        tz = ZoneInfo(w["timezone"])
        dur = timedelta(minutes=w["slot_duration_minutes"])
        buf = timedelta(minutes=w["buffer_minutes"])
        sh, sm = map(int, w["start_time_local"].split(":"))
        eh, em = map(int, w["end_time_local"].split(":"))
        exc_map = {ex["date"]: ex for ex in w.get("exceptions", [])}

        for offset in range(max(1, min(days_ahead, 30))):
            day_dt = (base_now.astimezone(tz).date() + timedelta(days=offset))
            if day_dt.weekday() != w["day_of_week"]:
                continue
            day_str = day_dt.isoformat()
            if day_str in exc_map and not exc_map[day_str].get("available", False):
                continue

            cursor_local = datetime.combine(day_dt, time(sh, sm), tzinfo=tz)
            end_local = datetime.combine(day_dt, time(eh, em), tzinfo=tz)

            while cursor_local + dur <= end_local:
                slot_start_utc = cursor_local.astimezone(timezone.utc)
                slot_end_utc = (cursor_local + dur).astimezone(timezone.utc)
                if slot_start_utc > base_now and not _has_conflict(
                    target_user_id, slot_start_utc, slot_end_utc, buffer_minutes=w["buffer_minutes"]
                ):
                    open_slots.append(
                        OpenSlotDTO(
                            start_utc=slot_start_utc,
                            end_utc=slot_end_utc,
                            alumni_timezone=w["timezone"],
                            local_label=f"{cursor_local.strftime('%Y-%m-%d %H:%M')} {w['timezone']}",
                        )
                    )
                cursor_local = cursor_local + dur + buf

    open_slots.sort(key=lambda s: s.start_utc)
    return {
        "alumni_id": target_user_id,
        "windows": [AvailabilityWindowResponse(**w).model_dump() for w in windows],
        "open_slots": [s.model_dump() for s in open_slots],
    }


def create_meeting_request(
    student: AuthenticatedUser,
    payload: MeetingRequestCreate,
    idempotency_key: Optional[str] = None,
) -> MeetingRequestResponse:
    alum = _resolve_alumni_record(payload.alumni_id)
    target_alumni_id = alum["user_id"] if alum else payload.alumni_id
    if alum and not alum.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ALUMNI_NOT_VERIFIED", "message": "Meetings can only be requested with verified alumni."},
        )
    if target_alumni_id == student.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_MEETING_FORBIDDEN", "message": "Cannot request a meeting with yourself."},
        )

    with _BOOKING_LOCK:
        if idempotency_key:
            cache_key = f"{student.id}:{idempotency_key}"
            existing_id = _SCHEDULING_IDEMPOTENCY.get(cache_key)
            if existing_id and existing_id in _MEETING_REQUESTS_STORE:
                return _serialize_meeting_request(_MEETING_REQUESTS_STORE[existing_id])

        now = datetime.now(timezone.utc)
        buffer_mins = _get_alumni_buffer_minutes(target_alumni_id)
        for slot in payload.proposed_slots:
            s_utc = _to_utc(slot.start_utc)
            e_utc = _to_utc(slot.end_utc)
            if s_utc <= now:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"code": "PAST_SLOT_INVALID", "message": "Proposed meeting slots must be in the future."},
                )
            diff_mins = int((e_utc - s_utc).total_seconds() // 60)
            if diff_mins != payload.duration_minutes:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"code": "SLOT_DURATION_MISMATCH", "message": f"Each slot must span exactly {payload.duration_minutes} minutes."},
                )
            if _has_conflict(target_alumni_id, s_utc, e_utc, buffer_minutes=buffer_mins):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "SLOT_CONFLICT", "message": "One or more proposed slots overlap an existing booked meeting."},
                )

        req_id = f"mreq-{uuid.uuid4().hex[:10]}"
        slots = [
            {
                "id": f"mslot-{uuid.uuid4().hex[:10]}",
                "meeting_request_id": req_id,
                "proposed_by": student.id,
                "round_number": 1,
                "start_utc": _to_utc(s.start_utc),
                "end_utc": _to_utc(s.end_utc),
                "status": "proposed",
            }
            for s in payload.proposed_slots
        ]

        record = {
            "id": req_id,
            "student_id": student.id,
            "student_name": f"{student.first_name or 'Institutional'} {student.last_name or 'Student'}".strip(),
            "alumni_id": target_alumni_id,
            "alumni_name": alum["full_name"] if alum else _resolve_display_name(target_alumni_id),
            "mentor_request_id": payload.mentor_request_id,
            "title": payload.title.strip(),
            "purpose": payload.purpose.strip(),
            "duration_minutes": payload.duration_minutes,
            "student_timezone": payload.student_timezone,
            "status": "pending",
            "decline_reason": None,
            "slots": slots,
            "created_at": now,
            "updated_at": now,
        }
        _MEETING_REQUESTS_STORE[req_id] = record
        if idempotency_key:
            _SCHEDULING_IDEMPOTENCY[f"{student.id}:{idempotency_key}"] = req_id

        _emit_outbox_event("meeting_request", req_id, "meeting.requested", {
            "meeting_request_id": req_id,
            "student_id": student.id,
            "alumni_id": target_alumni_id,
            "slot_count": len(slots),
        })
        create_notification(
            user_id=target_alumni_id,
            event_type="meeting.requested",
            entity_id=req_id,
            title="New Meeting Request",
            message=f"{record['student_name']} requested a {payload.duration_minutes}-min meeting: {record['title']}.",
            payload={"meeting_request_id": req_id},
        )
        return _serialize_meeting_request(record)


def _serialize_meeting_request(r: Dict[str, Any]) -> MeetingRequestResponse:
    return MeetingRequestResponse(
        id=r["id"],
        student_id=r["student_id"],
        student_name=r["student_name"],
        alumni_id=r["alumni_id"],
        alumni_name=r["alumni_name"],
        mentor_request_id=r.get("mentor_request_id"),
        title=r["title"],
        purpose=r["purpose"],
        duration_minutes=r["duration_minutes"],
        student_timezone=r["student_timezone"],
        status=r["status"],
        decline_reason=r.get("decline_reason"),
        slots=[MeetingSlotResponse(**s) for s in r["slots"]],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def list_my_meeting_requests(user: AuthenticatedUser) -> List[MeetingRequestResponse]:
    items = [
        _serialize_meeting_request(r)
        for r in _MEETING_REQUESTS_STORE.values()
        if r["student_id"] == user.id or r["alumni_id"] == user.id
    ]
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items


def _book_meeting_atomically(req: Dict[str, Any], slot_id: str, actor_id: str) -> MeetingResponse:
    """Atomically validate conflict & transition request -> accepted + create scheduled meeting."""
    slot = next((s for s in req["slots"] if s["id"] == slot_id), None)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SLOT_NOT_FOUND", "message": f"Slot '{slot_id}' does not belong to this request."},
        )
    if slot["status"] != "proposed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SLOT_NOT_AVAILABLE", "message": "Selected slot is no longer proposed."},
        )

    buffer_mins = _get_alumni_buffer_minutes(req["alumni_id"])
    if _has_conflict(req["alumni_id"], slot["start_utc"], slot["end_utc"], buffer_minutes=buffer_mins):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DOUBLE_BOOKING_PREVENTED", "message": "Alumni already has a conflicting scheduled meeting in this time window."},
        )
    if _has_conflict(req["student_id"], slot["start_utc"], slot["end_utc"], buffer_minutes=0):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "STUDENT_CONFLICT", "message": "Student already has a conflicting scheduled meeting in this time window."},
        )

    now = datetime.now(timezone.utc)
    for s in req["slots"]:
        s["status"] = "selected" if s["id"] == slot_id else "rejected"
    req["status"] = "accepted"
    req["updated_at"] = now

    meeting_id = f"mtg-{uuid.uuid4().hex[:10]}"
    meeting = {
        "id": meeting_id,
        "meeting_request_id": req["id"],
        "student_id": req["student_id"],
        "student_name": req["student_name"],
        "alumni_id": req["alumni_id"],
        "alumni_name": req["alumni_name"],
        "title": req["title"],
        "purpose": req["purpose"],
        "scheduled_start": slot["start_utc"],
        "scheduled_end": slot["end_utc"],
        "status": "scheduled",
        "rescheduled_from_meeting_id": None,
        "cancellation_reason": None,
        "student_rating": None,
        "student_feedback": None,
        "alumni_notes": None,
        "created_at": now,
        "updated_at": now,
    }
    _MEETINGS_STORE[meeting_id] = meeting

    _emit_outbox_event("meeting", meeting_id, "meeting.scheduled", {
        "meeting_id": meeting_id,
        "meeting_request_id": req["id"],
        "student_id": req["student_id"],
        "alumni_id": req["alumni_id"],
        "scheduled_start": slot["start_utc"].isoformat(),
        "scheduled_end": slot["end_utc"].isoformat(),
    })

    for target_uid in (req["student_id"], req["alumni_id"]):
        create_notification(
            user_id=target_uid,
            event_type="meeting.scheduled",
            entity_id=meeting_id,
            title="Meeting Confirmed",
            message=f"'{req['title']}' is confirmed for {slot['start_utc'].strftime('%Y-%m-%d %H:%M UTC')}.",
            payload={"meeting_id": meeting_id},
        )
    return MeetingResponse(**meeting)


def accept_meeting_request(alumni: AuthenticatedUser, request_id: str, payload: MeetingRequestAccept) -> MeetingResponse:
    with _BOOKING_LOCK:
        req = _MEETING_REQUESTS_STORE.get(request_id)
        if not req:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting request not found."})
        if req["alumni_id"] != alumni.id:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Only the requested alumnus can accept."})
        if req["status"] != "pending":
            raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": f"Cannot accept request in status '{req['status']}'."})
        return _book_meeting_atomically(req, payload.slot_id, actor_id=alumni.id)


def decline_meeting_request(alumni: AuthenticatedUser, request_id: str, payload: MeetingRequestDecline) -> MeetingRequestResponse:
    with _BOOKING_LOCK:
        req = _MEETING_REQUESTS_STORE.get(request_id)
        if not req:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting request not found."})
        if req["alumni_id"] != alumni.id:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Only the requested alumnus can decline."})
        if req["status"] not in ("pending", "counter_proposed"):
            raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": f"Cannot decline request in status '{req['status']}'."})

        req["status"] = "declined"
        req["decline_reason"] = payload.reason
        req["updated_at"] = datetime.now(timezone.utc)
        for s in req["slots"]:
            if s["status"] == "proposed":
                s["status"] = "rejected"

        create_notification(
            user_id=req["student_id"],
            event_type="meeting.declined",
            entity_id=request_id,
            title="Meeting Request Declined",
            message=f"{req['alumni_name']} declined '{req['title']}'.",
            payload={"meeting_request_id": request_id, "reason": payload.reason},
        )
        return _serialize_meeting_request(req)


def counter_propose_meeting_request(
    alumni: AuthenticatedUser, request_id: str, payload: MeetingRequestCounterPropose
) -> MeetingRequestResponse:
    with _BOOKING_LOCK:
        req = _MEETING_REQUESTS_STORE.get(request_id)
        if not req:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting request not found."})
        if req["alumni_id"] != alumni.id:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Only the requested alumnus can counter-propose."})
        if req["status"] != "pending":
            raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": f"Cannot counter-propose in status '{req['status']}'."})

        now = datetime.now(timezone.utc)
        buffer_mins = _get_alumni_buffer_minutes(alumni.id)
        for slot in payload.proposed_slots:
            s_utc, e_utc = _to_utc(slot.start_utc), _to_utc(slot.end_utc)
            if s_utc <= now:
                raise HTTPException(status_code=422, detail={"code": "PAST_SLOT_INVALID", "message": "Alternative slots must be in the future."})
            if _has_conflict(alumni.id, s_utc, e_utc, buffer_minutes=buffer_mins):
                raise HTTPException(status_code=409, detail={"code": "SLOT_CONFLICT", "message": "Counter-proposed slot conflicts with existing booking."})

        for s in req["slots"]:
            if s["status"] == "proposed":
                s["status"] = "rejected"

        next_round = max((s["round_number"] for s in req["slots"]), default=1) + 1
        for slot in payload.proposed_slots:
            req["slots"].append({
                "id": f"mslot-{uuid.uuid4().hex[:10]}",
                "meeting_request_id": req["id"],
                "proposed_by": alumni.id,
                "round_number": next_round,
                "start_utc": _to_utc(slot.start_utc),
                "end_utc": _to_utc(slot.end_utc),
                "status": "proposed",
            })
        req["status"] = "counter_proposed"
        req["updated_at"] = now

        _emit_outbox_event("meeting_request", req["id"], "meeting.counter_proposed", {
            "meeting_request_id": req["id"],
            "alumni_id": alumni.id,
            "student_id": req["student_id"],
        })
        create_notification(
            user_id=req["student_id"],
            event_type="meeting.counter_proposed",
            entity_id=req["id"],
            title="New Meeting Time Proposed",
            message=f"{req['alumni_name']} proposed alternative time(s) for '{req['title']}'.",
            payload={"meeting_request_id": req["id"]},
        )
        return _serialize_meeting_request(req)


def confirm_counter_proposal(student: AuthenticatedUser, request_id: str, payload: MeetingRequestConfirm) -> MeetingResponse:
    with _BOOKING_LOCK:
        req = _MEETING_REQUESTS_STORE.get(request_id)
        if not req:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting request not found."})
        if req["student_id"] != student.id:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Only the requesting student can confirm counter-proposed slots."})
        if req["status"] != "counter_proposed":
            raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": f"Cannot confirm in status '{req['status']}'."})
        return _book_meeting_atomically(req, payload.slot_id, actor_id=student.id)


def cancel_meeting_request(user: AuthenticatedUser, request_id: str) -> MeetingRequestResponse:
    with _BOOKING_LOCK:
        req = _MEETING_REQUESTS_STORE.get(request_id)
        if not req:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting request not found."})
        if user.id not in (req["student_id"], req["alumni_id"]):
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Access denied."})
        if req["status"] not in ("pending", "counter_proposed"):
            raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": f"Cannot cancel request in status '{req['status']}'."})
        req["status"] = "cancelled"
        req["updated_at"] = datetime.now(timezone.utc)
        for s in req["slots"]:
            if s["status"] == "proposed":
                s["status"] = "expired"
        return _serialize_meeting_request(req)


def list_my_meetings(user: AuthenticatedUser) -> List[MeetingResponse]:
    items = [
        MeetingResponse(**m)
        for m in _MEETINGS_STORE.values()
        if m["student_id"] == user.id or m["alumni_id"] == user.id
    ]
    items.sort(key=lambda x: x.scheduled_start)
    return items


def get_meeting(user: AuthenticatedUser, meeting_id: str) -> MeetingResponse:
    m = _MEETINGS_STORE.get(meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting not found."})
    if user.id not in (m["student_id"], m["alumni_id"]) and "admin" not in user.roles:
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Not a meeting participant."})
    return MeetingResponse(**m)


def reschedule_meeting(user: AuthenticatedUser, meeting_id: str, payload: MeetingRescheduleRequest) -> MeetingResponse:
    with _BOOKING_LOCK:
        m = _MEETINGS_STORE.get(meeting_id)
        if not m:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting not found."})
        if user.id not in (m["student_id"], m["alumni_id"]):
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Not a meeting participant."})
        if m["status"] != "scheduled":
            raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": f"Cannot reschedule meeting in status '{m['status']}'."})

        new_start = _to_utc(payload.new_start_utc)
        new_end = _to_utc(payload.new_end_utc)
        if new_start <= datetime.now(timezone.utc):
            raise HTTPException(status_code=422, detail={"code": "PAST_SLOT_INVALID", "message": "Rescheduled time must be in the future."})

        buf = _get_alumni_buffer_minutes(m["alumni_id"])
        if _has_conflict(m["alumni_id"], new_start, new_end, buffer_minutes=buf, exclude_meeting_id=meeting_id):
            raise HTTPException(status_code=409, detail={"code": "DOUBLE_BOOKING_PREVENTED", "message": "Alumni has a conflicting meeting at the new time."})
        if _has_conflict(m["student_id"], new_start, new_end, buffer_minutes=0, exclude_meeting_id=meeting_id):
            raise HTTPException(status_code=409, detail={"code": "STUDENT_CONFLICT", "message": "Student has a conflicting meeting at the new time."})

        now = datetime.now(timezone.utc)
        m["status"] = "cancelled"
        m["cancellation_reason"] = payload.reason or "Rescheduled to new slot"
        m["updated_at"] = now

        new_id = f"mtg-{uuid.uuid4().hex[:10]}"
        new_meeting = {
            "id": new_id,
            "meeting_request_id": None,
            "student_id": m["student_id"],
            "student_name": m["student_name"],
            "alumni_id": m["alumni_id"],
            "alumni_name": m["alumni_name"],
            "title": m["title"],
            "purpose": m["purpose"],
            "scheduled_start": new_start,
            "scheduled_end": new_end,
            "status": "scheduled",
            "rescheduled_from_meeting_id": meeting_id,
            "cancellation_reason": None,
            "student_rating": None,
            "student_feedback": None,
            "alumni_notes": None,
            "created_at": now,
            "updated_at": now,
        }
        _MEETINGS_STORE[new_id] = new_meeting
        return MeetingResponse(**new_meeting)


def cancel_meeting(user: AuthenticatedUser, meeting_id: str, payload: MeetingCancelRequest) -> MeetingResponse:
    with _BOOKING_LOCK:
        m = _MEETINGS_STORE.get(meeting_id)
        if not m:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting not found."})
        if user.id not in (m["student_id"], m["alumni_id"]):
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Not a meeting participant."})
        if m["status"] not in ("scheduled", "in_progress"):
            raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": f"Cannot cancel meeting in status '{m['status']}'."})

        m["status"] = "cancelled"
        m["cancellation_reason"] = payload.reason
        m["updated_at"] = datetime.now(timezone.utc)
        _emit_outbox_event("meeting", meeting_id, "meeting.cancelled", {"meeting_id": meeting_id, "cancelled_by": user.id})
        return MeetingResponse(**m)


def submit_meeting_feedback(user: AuthenticatedUser, meeting_id: str, payload: MeetingFeedbackRequest) -> MeetingResponse:
    m = _MEETINGS_STORE.get(meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Meeting not found."})
    if user.id not in (m["student_id"], m["alumni_id"]):
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Not a meeting participant."})
    if user.id == m["student_id"]:
        if payload.rating is not None:
            m["student_rating"] = payload.rating
        if payload.feedback is not None:
            m["student_feedback"] = payload.feedback
    if user.id == m["alumni_id"] and payload.alumni_notes is not None:
        m["alumni_notes"] = payload.alumni_notes
    m["updated_at"] = datetime.now(timezone.utc)
    return MeetingResponse(**m)


def export_meeting_ics(user: AuthenticatedUser, meeting_id: str) -> str:
    m = get_meeting(user, meeting_id)
    dt_fmt = "%Y%m%dT%H%M%SZ"
    start_s = _to_utc(m.scheduled_start).strftime(dt_fmt)
    end_s = _to_utc(m.scheduled_end).strftime(dt_fmt)
    stamp_s = datetime.now(timezone.utc).strftime(dt_fmt)
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//MSGI One//Scheduling Engine//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{m.id}@msgi.edu\r\n"
        f"DTSTAMP:{stamp_s}\r\n"
        f"DTSTART:{start_s}\r\n"
        f"DTEND:{end_s}\r\n"
        f"SUMMARY:{m.title}\r\n"
        f"DESCRIPTION:{m.purpose}\r\n"
        f"STATUS:{'CANCELLED' if m.status == 'cancelled' else 'CONFIRMED'}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


# ============================================================================
# AI TOOL CONTRACTS (READ & DRAFT ONLY — MUTATIONS REQUIRE HITL APPROVAL)
# ============================================================================

def get_alumni_availability_tool(alumni_id: str, days_ahead: int = 7) -> Dict[str, Any]:
    return get_alumni_availability_and_slots(alumni_id=alumni_id, days_ahead=days_ahead)


def suggest_meeting_slots_tool(alumni_id: str, duration_minutes: int = 30, max_suggestions: int = 3) -> List[Dict[str, Any]]:
    avail = get_alumni_availability_and_slots(alumni_id=alumni_id, days_ahead=14)
    return avail["open_slots"][:max_suggestions]


def draft_meeting_request_tool(
    student: AuthenticatedUser,
    alumni_id: str,
    title: str,
    purpose: str,
    proposed_slots: List[Dict[str, str]],
    duration_minutes: int = 30,
) -> Dict[str, Any]:
    alum = _resolve_alumni_record(alumni_id)
    target_id = alum["user_id"] if alum else alumni_id
    return {
        "action_type": "create_meeting_request",
        "confirmation_required": True,
        "student_id": student.id,
        "alumni_id": target_id,
        "alumni_name": alum["full_name"] if alum else _resolve_display_name(target_id),
        "title": title,
        "purpose": purpose,
        "duration_minutes": duration_minutes,
        "proposed_slots": proposed_slots,
    }
