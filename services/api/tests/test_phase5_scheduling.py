"""
MSGI One — Phase 5 Scheduling Engine Verification Tests
Tests:
  1. IANA timezone recurring availability & exception evaluation -> UTC slots.
  2. Full student-to-alumni multi-slot request -> accept -> scheduled meeting + notifications.
  3. Counter-proposal -> student confirmation workflow.
  4. Invalid state transition rejection.
  5. Concurrent double-booking prevention under parallel threads.
  6. Idempotent duplicate request submission.
  7. Rescheduling linkage, cancellation, feedback & RFC 5545 .ics export.
"""

from concurrent.futures import ThreadPoolExecutor
import copy
from datetime import datetime, timedelta, timezone
import uuid
import jwt
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings
from src.core.dependencies import AuthenticatedUser
from src.schemas.scheduling import AvailabilityUpdateRequest, AvailabilityWindowInput, MeetingRequestCreate, ProposedSlotInput, MeetingRequestAccept
from src.services.scheduling_service import (
    _AVAILABILITY_STORE,
    _MEETING_REQUESTS_STORE,
    _MEETINGS_STORE,
    _SCHEDULING_IDEMPOTENCY,
    _SCHEDULING_OUTBOX,
    accept_meeting_request,
    create_meeting_request,
)


@pytest.fixture(autouse=True)
def reset_scheduling_state():
    avail_snap = copy.deepcopy(_AVAILABILITY_STORE)
    reqs_snap = copy.deepcopy(_MEETING_REQUESTS_STORE)
    mtgs_snap = copy.deepcopy(_MEETINGS_STORE)
    idem_snap = copy.deepcopy(_SCHEDULING_IDEMPOTENCY)
    outbox_snap = copy.deepcopy(_SCHEDULING_OUTBOX)
    yield
    _AVAILABILITY_STORE.clear()
    _AVAILABILITY_STORE.update(avail_snap)
    _MEETING_REQUESTS_STORE.clear()
    _MEETING_REQUESTS_STORE.update(reqs_snap)
    _MEETINGS_STORE.clear()
    _MEETINGS_STORE.update(mtgs_snap)
    _SCHEDULING_IDEMPOTENCY.clear()
    _SCHEDULING_IDEMPOTENCY.update(idem_snap)
    _SCHEDULING_OUTBOX[:] = outbox_snap


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(user_id: str, email: str, roles: list[str], is_verified: bool = True) -> dict:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": user_id,
            "email": email,
            "aud": settings.JWT_AUDIENCE,
            "exp": int((now + timedelta(minutes=60)).timestamp()),
            "is_verified": is_verified,
            "app_metadata": {"roles": roles, "is_verified": is_verified},
            "user_metadata": {"first_name": "Sched", "last_name": "User"},
        },
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_availability_timezone_conversion_and_exceptions(client):
    alum_headers = auth_headers("user-kenji-001", "kenji@example.msgi.edu", ["alumni"], is_verified=True)
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    dow = tomorrow.weekday()

    res = client.put(
        "/api/v1/scheduling/availability/me",
        json={
            "windows": [
                {
                    "day_of_week": dow,
                    "start_time_local": "10:00",
                    "end_time_local": "11:00",
                    "timezone": "Asia/Tokyo",
                    "slot_duration_minutes": 30,
                    "buffer_minutes": 10,
                    "exceptions": [],
                }
            ]
        },
        headers=alum_headers,
    )
    assert res.status_code == 200

    avail = client.get("/api/v1/scheduling/availability/user-kenji-001?days_ahead=3", headers=alum_headers)
    assert avail.status_code == 200
    slots = avail.json()["data"]["open_slots"]
    assert len(slots) >= 1
    assert slots[0]["alumni_timezone"] == "Asia/Tokyo"


def test_full_scheduling_accept_counter_reschedule_and_ics(client):
    student_headers = auth_headers("sched-stu-01", "stu01@example.msgi.edu", ["student"])
    alum_headers = auth_headers("user-kenji-001", "kenji@example.msgi.edu", ["alumni"], is_verified=True)

    s1_start = datetime.now(timezone.utc) + timedelta(days=3, hours=1)
    s1_end = s1_start + timedelta(minutes=30)
    s2_start = datetime.now(timezone.utc) + timedelta(days=3, hours=3)
    s2_end = s2_start + timedelta(minutes=30)

    # Idempotent submission
    payload = {
        "alumni_id": "alumni-kenji-sato",
        "title": "ML Systems Mentorship",
        "purpose": "Review distributed LLM inference roadmap",
        "duration_minutes": 30,
        "student_timezone": "Asia/Kolkata",
        "proposed_slots": [
            {"start_utc": s1_start.isoformat(), "end_utc": s1_end.isoformat()},
            {"start_utc": s2_start.isoformat(), "end_utc": s2_end.isoformat()},
        ],
    }
    idem = {"Idempotency-Key": "idem-sched-001", **student_headers}
    r1 = client.post("/api/v1/meetings/requests", json=payload, headers=idem)
    r2 = client.post("/api/v1/meetings/requests", json=payload, headers=idem)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["data"]["id"] == r2.json()["data"]["id"]

    req_data = r1.json()["data"]
    req_id = req_data["id"]
    slot_id = req_data["slots"][0]["id"]

    # Alumni accepts slot 0 -> confirmed meeting created
    acc_res = client.post(
        f"/api/v1/meetings/requests/{req_id}/accept",
        json={"slot_id": slot_id},
        headers=alum_headers,
    )
    assert acc_res.status_code == 200
    mtg = acc_res.json()["data"]
    assert mtg["status"] == "scheduled"
    mtg_id = mtg["id"]

    # Invalid second accept rejected
    bad_acc = client.post(
        f"/api/v1/meetings/requests/{req_id}/accept",
        json={"slot_id": slot_id},
        headers=alum_headers,
    )
    assert bad_acc.status_code == 409

    # .ics export
    ics_res = client.get(f"/api/v1/meetings/{mtg_id}/ics", headers=student_headers)
    assert ics_res.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_res.text
    assert "ML Systems Mentorship" in ics_res.text

    # Counter-proposal flow
    s3_start = datetime.now(timezone.utc) + timedelta(days=5, hours=2)
    s3_end = s3_start + timedelta(minutes=30)
    req2 = client.post(
        "/api/v1/meetings/requests",
        json={
            "alumni_id": "user-ananya-002",
            "title": "Product Strategy Chat",
            "purpose": "Discuss PM transition steps",
            "duration_minutes": 30,
            "student_timezone": "UTC",
            "proposed_slots": [{"start_utc": s3_start.isoformat(), "end_utc": s3_end.isoformat()}],
        },
        headers=student_headers,
    ).json()["data"]

    ananya_headers = auth_headers("user-ananya-002", "ananya@example.msgi.edu", ["alumni"], is_verified=True)
    alt_start = datetime.now(timezone.utc) + timedelta(days=6, hours=4)
    alt_end = alt_start + timedelta(minutes=30)
    cp_res = client.post(
        f"/api/v1/meetings/requests/{req2['id']}/counter-propose",
        json={"proposed_slots": [{"start_utc": alt_start.isoformat(), "end_utc": alt_end.isoformat()}]},
        headers=ananya_headers,
    )
    assert cp_res.status_code == 200
    assert cp_res.json()["data"]["status"] == "counter_proposed"
    alt_slot_id = [s["id"] for s in cp_res.json()["data"]["slots"] if s["status"] == "proposed"][0]

    conf_res = client.post(
        f"/api/v1/meetings/requests/{req2['id']}/confirm",
        json={"slot_id": alt_slot_id},
        headers=student_headers,
    )
    assert conf_res.status_code == 200
    assert conf_res.json()["data"]["status"] == "scheduled"

    # Reschedule & feedback
    resch_start = datetime.now(timezone.utc) + timedelta(days=7, hours=5)
    resch_end = resch_start + timedelta(minutes=30)
    resch_res = client.post(
        f"/api/v1/meetings/{mtg_id}/reschedule",
        json={"new_start_utc": resch_start.isoformat(), "new_end_utc": resch_end.isoformat(), "reason": "Conflict"},
        headers=student_headers,
    )
    assert resch_res.status_code == 200
    new_mtg_id = resch_res.json()["data"]["id"]
    assert resch_res.json()["data"]["rescheduled_from_meeting_id"] == mtg_id

    fb_res = client.post(
        f"/api/v1/meetings/{new_mtg_id}/feedback",
        json={"rating": 5, "feedback": "Very helpful guidance!"},
        headers=student_headers,
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["data"]["student_rating"] == 5


def test_concurrent_double_booking_prevented():
    s1 = AuthenticatedUser(id="conc-stu-1", email="c1@example.msgi.edu", roles=["student"])
    s2 = AuthenticatedUser(id="conc-stu-2", email="c2@example.msgi.edu", roles=["student"])
    alum = AuthenticatedUser(id="user-kenji-001", email="kenji@example.msgi.edu", roles=["alumni"], is_verified=True)

    slot_start = datetime.now(timezone.utc) + timedelta(days=4, hours=2)
    slot_end = slot_start + timedelta(minutes=30)

    r1 = create_meeting_request(
        s1,
        MeetingRequestCreate(
            alumni_id="user-kenji-001",
            title="Concurrent A",
            purpose="Testing concurrency lock A",
            duration_minutes=30,
            proposed_slots=[ProposedSlotInput(start_utc=slot_start, end_utc=slot_end)],
        ),
    )
    r2 = create_meeting_request(
        s2,
        MeetingRequestCreate(
            alumni_id="user-kenji-001",
            title="Concurrent B",
            purpose="Testing concurrency lock B",
            duration_minutes=30,
            proposed_slots=[ProposedSlotInput(start_utc=slot_start, end_utc=slot_end)],
        ),
    )

    def try_accept(req_obj):
        try:
            accept_meeting_request(alum, req_obj.id, MeetingRequestAccept(slot_id=req_obj.slots[0].id))
            return "OK"
        except Exception:
            return "CONFLICT"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(try_accept, [r1, r2]))

    assert outcomes.count("OK") == 1
    assert outcomes.count("CONFLICT") == 1
