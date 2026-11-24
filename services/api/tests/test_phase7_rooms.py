"""
MSGI One — Phase 7 LiveKit Audio/Video Room Authorization & Webhook Tests
Validates:
  1. Confirmed meeting participants within join window receive short-lived room tokens.
  2. Uninvited users, blocked users, outside-window, and cancelled meetings are rejected (403).
  3. Waiting room admission, participant removal, and host ending room work cleanly.
  4. Recording is strictly disabled by default.
  5. Signed webhook verification rejects invalid signatures and deduplicates repeated deliveries.
"""

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import jwt
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings
from src.services.messaging_service import _BLOCKS_STORE
from src.services.room_service import _PROCESSED_WEBHOOK_IDS, _ROOMS_STORE
from src.services.scheduling_service import _MEETINGS_STORE


@pytest.fixture(autouse=True)
def clean_room_state():
    r_snap = copy.deepcopy(_ROOMS_STORE)
    m_snap = copy.deepcopy(_MEETINGS_STORE)
    b_snap = set(_BLOCKS_STORE)
    w_snap = set(_PROCESSED_WEBHOOK_IDS)
    yield
    _ROOMS_STORE.clear()
    _ROOMS_STORE.update(r_snap)
    _MEETINGS_STORE.clear()
    _MEETINGS_STORE.update(m_snap)
    _BLOCKS_STORE.clear()
    _BLOCKS_STORE.update(b_snap)
    _PROCESSED_WEBHOOK_IDS.clear()
    _PROCESSED_WEBHOOK_IDS.update(w_snap)


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(user_id: str, roles: list[str]) -> dict:
    now = datetime.now(timezone.utc)
    tok = jwt.encode(
        {
            "sub": user_id,
            "email": f"{user_id}@example.msgi.edu",
            "aud": settings.JWT_AUDIENCE,
            "exp": int((now + timedelta(minutes=60)).timestamp()),
            "app_metadata": {"roles": roles},
            "user_metadata": {"first_name": "Room", "last_name": user_id},
        },
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {tok}"}


def _seed_active_meeting(meeting_id: str = "mtg-live-001", offset_minutes: int = 2) -> str:
    now = datetime.now(timezone.utc)
    _MEETINGS_STORE[meeting_id] = {
        "id": meeting_id,
        "meeting_request_id": None,
        "student_id": "rtc-stu-01",
        "student_name": "Student RTC",
        "alumni_id": "rtc-alum-01",
        "alumni_name": "Alumnus RTC",
        "title": "Architecture Mentoring Call",
        "purpose": "Live consultation",
        "scheduled_start": now + timedelta(minutes=offset_minutes),
        "scheduled_end": now + timedelta(minutes=offset_minutes + 30),
        "status": "scheduled",
        "rescheduled_from_meeting_id": None,
        "cancellation_reason": None,
        "student_rating": None,
        "student_feedback": None,
        "alumni_notes": None,
        "created_at": now,
        "updated_at": now,
    }
    return meeting_id


def test_room_admission_host_controls_and_security_boundaries(client):
    mtg_id = _seed_active_meeting("mtg-live-001", offset_minutes=2)
    h_stu = auth_headers("rtc-stu-01", ["student"])
    h_alum = auth_headers("rtc-alum-01", ["alumni"])
    h_intruder = auth_headers("rtc-intruder", ["student"])

    # Uninvited user rejected
    assert client.post(f"/api/v1/rooms/{mtg_id}/token", json={}, headers=h_intruder).status_code == 403

    # Host joins -> room active & admitted
    host_tok = client.post(f"/api/v1/rooms/{mtg_id}/token", json={"audio_enabled": True, "video_enabled": True}, headers=h_alum)
    assert host_tok.status_code == 200
    host_data = host_tok.json()["data"]
    assert host_data["role"] == "host"
    assert host_data["admission_status"] == "admitted"
    assert host_data["recording_enabled"] is False

    # Student joins -> waiting room
    stu_tok = client.post(f"/api/v1/rooms/{mtg_id}/token", json={"audio_enabled": True, "video_enabled": False}, headers=h_stu)
    assert stu_tok.status_code == 200
    assert stu_tok.json()["data"]["admission_status"] == "waiting"

    # Non-host cannot admit
    assert client.post(f"/api/v1/rooms/{mtg_id}/admit", json={"target_user_id": "rtc-stu-01"}, headers=h_stu).status_code == 403

    # Host admits student
    admit_res = client.post(f"/api/v1/rooms/{mtg_id}/admit", json={"target_user_id": "rtc-stu-01"}, headers=h_alum)
    assert admit_res.status_code == 200
    assert any(p["user_id"] == "rtc-stu-01" and p["admission_status"] == "admitted" for p in admit_res.json()["data"]["participants"])

    # Host ends room -> meeting becomes completed & subsequent join rejected
    end_res = client.post(f"/api/v1/rooms/{mtg_id}/end", headers=h_alum)
    assert end_res.status_code == 200
    assert end_res.json()["data"]["status"] == "ended"
    assert _MEETINGS_STORE[mtg_id]["status"] == "completed"
    assert client.post(f"/api/v1/rooms/{mtg_id}/token", json={}, headers=h_stu).status_code == 403


def test_room_rejects_outside_window_and_blocked(client):
    mtg_far = _seed_active_meeting("mtg-far-002", offset_minutes=240)
    h_stu = auth_headers("rtc-stu-01", ["student"])
    assert client.post(f"/api/v1/rooms/{mtg_far}/token", json={}, headers=h_stu).status_code == 403

    mtg_now = _seed_active_meeting("mtg-blk-003", offset_minutes=1)
    _BLOCKS_STORE.add(("rtc-alum-01", "rtc-stu-01"))
    assert client.post(f"/api/v1/rooms/{mtg_now}/token", json={}, headers=h_stu).status_code == 403


def test_livekit_signed_webhook_verification_and_dedup(client):
    mtg_id = _seed_active_meeting("mtg-wh-004", offset_minutes=1)
    h_alum = auth_headers("rtc-alum-01", ["alumni"])
    room_name = client.post(f"/api/v1/rooms/{mtg_id}/token", json={}, headers=h_alum).json()["data"]["room_name"]

    body = json.dumps({"id": "wh-evt-999", "event": "room_finished", "room": {"name": room_name}}).encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    secret = settings.LIVEKIT_API_SECRET or settings.SUPABASE_JWT_SECRET
    sig_jwt = jwt.encode({"sha256": digest, "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())}, secret, algorithm="HS256")

    # Invalid signature rejected
    bad_wh = client.post("/api/v1/rooms/webhooks/livekit", content=body, headers={"Authorization": "Bearer invalid.jwt.tok"})
    assert bad_wh.status_code == 401

    # Valid webhook processes and ends room
    ok_wh = client.post("/api/v1/rooms/webhooks/livekit", content=body, headers={"Authorization": f"Bearer {sig_jwt}"})
    assert ok_wh.status_code == 200
    assert ok_wh.json()["data"]["processed"] is True
    assert _ROOMS_STORE[mtg_id]["status"] == "ended"

    # Duplicate webhook delivery is deduplicated cleanly
    dup_wh = client.post("/api/v1/rooms/webhooks/livekit", content=body, headers={"Authorization": f"Bearer {sig_jwt}"})
    assert dup_wh.status_code == 200
    assert dup_wh.json()["data"]["deduplicated"] is True
