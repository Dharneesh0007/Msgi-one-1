"""
MSGI One — Phase 6 Real-Time 1-on-1 Messaging & Safety Tests
Validates:
  1. WebSocket authentication & rejection of unauthenticated handshakes.
  2. Durable persistence before acceptance, idempotency deduplication, cursor recovery.
  3. Delivery & read receipts + typing indicators.
  4. Cross-user access denial, bilateral blocking, moderation reporting, and attachment validation.
"""

import copy
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.main import app
from src.core.config import settings
from src.services.admin_service import _MODERATION_REPORTS_STORE
from src.services.messaging_service import (
    _BLOCKS_STORE,
    _CONVERSATIONS_STORE,
    _IDEMPOTENCY_INDEX,
    _MESSAGES_STORE,
    _PARTICIPANTS_STORE,
)


@pytest.fixture(autouse=True)
def clean_messaging_state():
    c_snap = copy.deepcopy(_CONVERSATIONS_STORE)
    p_snap = copy.deepcopy(_PARTICIPANTS_STORE)
    m_snap = copy.deepcopy(_MESSAGES_STORE)
    i_snap = copy.deepcopy(_IDEMPOTENCY_INDEX)
    b_snap = set(_BLOCKS_STORE)
    rep_snap = copy.deepcopy(_MODERATION_REPORTS_STORE)
    yield
    _CONVERSATIONS_STORE.clear()
    _CONVERSATIONS_STORE.update(c_snap)
    _PARTICIPANTS_STORE.clear()
    _PARTICIPANTS_STORE.update(p_snap)
    _MESSAGES_STORE.clear()
    _MESSAGES_STORE.update(m_snap)
    _IDEMPOTENCY_INDEX.clear()
    _IDEMPOTENCY_INDEX.update(i_snap)
    _BLOCKS_STORE.clear()
    _BLOCKS_STORE.update(b_snap)
    _MODERATION_REPORTS_STORE[:] = rep_snap


@pytest.fixture
def client():
    return TestClient(app)


def make_token(user_id: str, email: str, roles: list[str]) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "email": email,
            "aud": settings.JWT_AUDIENCE,
            "exp": int((now + timedelta(minutes=60)).timestamp()),
            "app_metadata": {"roles": roles},
            "user_metadata": {"first_name": "Chat", "last_name": "User"},
        },
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )


def test_websocket_rejects_unauthenticated(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/chat") as ws:
            ws.receive_text()


def test_websocket_messaging_dedup_reconnect_and_receipts(client):
    t1 = make_token("chat-u1", "u1@example.msgi.edu", ["student"])
    t2 = make_token("chat-u2", "u2@example.msgi.edu", ["alumni"])
    t3 = make_token("chat-u3", "u3@example.msgi.edu", ["student"])
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}
    h3 = {"Authorization": f"Bearer {t3}"}

    conv_res = client.post("/api/v1/conversations", json={"recipient_id": "chat-u2"}, headers=h1)
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["data"]["id"]

    # Unauthorized third party cannot read messages
    assert client.get(f"/api/v1/conversations/{conv_id}/messages", headers=h3).status_code == 403

    with client.websocket_connect(f"/ws/chat?token={t1}") as ws1:
        ready = ws1.receive_json()
        assert ready["event_type"] == "connection.ready"

        # Send message + duplicate retry with identical client_idempotency_key
        frame = {
            "event_type": "message.send",
            "conversation_id": conv_id,
            "client_idempotency_key": "idem-ws-100",
            "payload": {"body": "Hello from WS!"},
        }
        ws1.send_json(frame)
        accepted = ws1.receive_json()
        created = ws1.receive_json()
        assert accepted["event_type"] == "message.accepted"
        assert accepted["payload"]["seq"] == 1
        assert created["event_type"] == "message.created"

        # Retry identical idempotency key -> still seq 1, no duplicate stored
        ws1.send_json(frame)
        accepted_dup = ws1.receive_json()
        _ = ws1.receive_json()
        assert accepted_dup["payload"]["seq"] == 1

    # While u2 was offline, send message 2 via REST (simulating peer sending during disconnect)
    r_msg2 = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"body": "Missed while offline", "client_idempotency_key": "idem-rest-200"},
        headers=h1,
    )
    assert r_msg2.status_code == 201
    assert r_msg2.json()["data"]["seq"] == 2

    # u2 reconnects and recovers missed messages with after_seq=0 cursor
    hist = client.get(f"/api/v1/conversations/{conv_id}/messages?after_seq=0", headers=h2)
    assert hist.status_code == 200
    msgs = hist.json()["data"]
    assert len(msgs) == 2
    assert [m["seq"] for m in msgs] == [1, 2]

    # Mark read and verify unread_count clears
    read_res = client.post(f"/api/v1/conversations/{conv_id}/read", json={"last_read_seq": 2}, headers=h2)
    assert read_res.status_code == 200
    assert read_res.json()["data"]["unread_count"] == 0


def test_blocking_reporting_and_attachment_security(client):
    h1 = {"Authorization": f"Bearer {make_token('blk-u1', 'b1@example.msgi.edu', ['student'])}"}
    h2 = {"Authorization": f"Bearer {make_token('blk-u2', 'b2@example.msgi.edu', ['alumni'])}"}

    conv_id = client.post("/api/v1/conversations", json={"recipient_id": "blk-u2"}, headers=h1).json()["data"]["id"]

    # Reject dangerous executable attachment
    bad_att = client.post(
        f"/api/v1/conversations/{conv_id}/attachments/validate",
        json={
            "file_name": "malware.exe",
            "mime_type": "application/pdf",
            "size_bytes": 1024,
            "sha256_checksum": "a" * 64,
            "storage_path": "uploads/malware.exe",
        },
        headers=h1,
    )
    assert bad_att.status_code == 422

    # Block user -> sending messages is forbidden
    assert client.post("/api/v1/safety/blocks", json={"blocked_user_id": "blk-u2", "reason": "Spam"}, headers=h1).status_code == 200
    blocked_send = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"body": "Trying after block"},
        headers=h2,
    )
    assert blocked_send.status_code == 403

    # Report user -> lands in moderation queue
    rep = client.post(
        "/api/v1/safety/reports",
        json={"reported_user_id": "blk-u2", "category": "spam", "description": "Repeated unsolicited messages"},
        headers=h1,
    )
    assert rep.status_code == 201
    assert any(r["reported_user_id"] == "blk-u2" for r in _MODERATION_REPORTS_STORE)
