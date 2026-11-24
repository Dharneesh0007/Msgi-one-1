"""
MSGI One — Phase 3 Identity, Authorization, Privacy & Security Test Suite
Validates:
  1. Asymmetric RS256/ES256 tokens without valid JWKS/public key are strictly rejected (zero unverified fallback).
  2. Session logout revokes active JWT and blocks replay.
  3. Shared PermissionChecker enforces conversation, meeting room, and user_skills RLS gates.
  4. Alumni verification submission -> Admin approval provisions server-side role & verified status.
  5. Sensitive log redaction & sliding window rate limiter.
"""

from datetime import datetime, timedelta, timezone
import uuid
import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings
from src.core.dependencies import authenticate_websocket_token
from src.core.permissions import PermissionChecker, _SERVER_USER_ROLES, _SERVER_USER_VERIFICATION
from src.core.security import (
    SlidingWindowRateLimiter,
    clear_revoked_tokens,
    redact_sensitive_dict,
    redact_sensitive_text,
    verify_jwt_token,
)


import copy
from src.services.admin_service import _VERIFICATION_REQUESTS_STORE, _ADMIN_AUDIT_LOGS_STORE
from src.services.alumni_service import _SYNTHETIC_ALUMNI_STORE


@pytest.fixture(autouse=True)
def reset_security_state():
    vreq_snap = copy.deepcopy(_VERIFICATION_REQUESTS_STORE)
    audit_snap = copy.deepcopy(_ADMIN_AUDIT_LOGS_STORE)
    alumni_snap = copy.deepcopy(_SYNTHETIC_ALUMNI_STORE)
    clear_revoked_tokens()
    _SERVER_USER_ROLES.clear()
    _SERVER_USER_VERIFICATION.clear()
    yield
    _VERIFICATION_REQUESTS_STORE[:] = vreq_snap
    _ADMIN_AUDIT_LOGS_STORE[:] = audit_snap
    _SYNTHETIC_ALUMNI_STORE[:] = alumni_snap
    clear_revoked_tokens()
    _SERVER_USER_ROLES.clear()
    _SERVER_USER_VERIFICATION.clear()


@pytest.fixture
def client():
    return TestClient(app)


def make_hs256_token(user_id: str, email: str, roles: list[str], is_verified: bool = False, jti: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "aud": settings.JWT_AUDIENCE,
        "exp": int((now + timedelta(minutes=30)).timestamp()),
        "jti": jti or f"jti-{uuid.uuid4().hex[:8]}",
        "is_verified": is_verified,
        "app_metadata": {"roles": roles, "is_verified": is_verified},
        "user_metadata": {"first_name": "Phase3", "last_name": "Tester"},
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def test_asymmetric_rs256_without_jwks_is_rejected(monkeypatch):
    """Ensure RS256 tokens never fall back to verify_signature=False."""
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://placeholder-project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_JWT_PUBLIC_KEY", None)
    header_b64 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9"
    payload_b64 = "eyJzdWIiOiJhdHRhY2tlciIsImF1ZCI6ImF1dGhlbnRpY2F0ZWQiLCJleHAiOjk5OTk5OTk5OTl9"
    forged = f"{header_b64}.{payload_b64}.Zm9yZ2Vk"

    with pytest.raises(HTTPException) as exc:
        verify_jwt_token(forged)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] in ("JWKS_UNAVAILABLE", "INVALID_SIGNATURE", "MALFORMED_TOKEN")


def test_session_logout_revokes_token_replay(client):
    token = make_hs256_token("p3-logout-user", "logout@example.msgi.edu", ["student"])
    headers = {"Authorization": f"Bearer {token}"}

    # Works before logout
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200

    # Logout revokes session
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["session_revoked"] is True

    # Replay after logout is rejected
    replay_res = client.get("/api/v1/users/me", headers=headers)
    assert replay_res.status_code == 401
    assert replay_res.json()["error"]["code"] == "SESSION_REVOKED"


def test_websocket_token_authentication():
    token = make_hs256_token("ws-user-01", "ws01@example.msgi.edu", ["student"])
    user = authenticate_websocket_token(f"Bearer {token}")
    assert user.id == "ws-user-01"

    with pytest.raises(HTTPException) as exc:
        authenticate_websocket_token(None)
    assert exc.value.status_code == 401


def test_shared_permission_checker_boundaries():
    now = datetime.now(timezone.utc)
    # Conversation membership & blocking
    PermissionChecker.verify_conversation_access("u1", "u1", "u2", is_blocked=False)
    with pytest.raises(HTTPException) as exc:
        PermissionChecker.verify_conversation_access("u3", "u1", "u2", is_blocked=False)
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc_blk:
        PermissionChecker.verify_conversation_access("u1", "u1", "u2", is_blocked=True)
    assert exc_blk.value.detail["code"] == "USER_BLOCKED"

    # Meeting room admission
    PermissionChecker.verify_meeting_room_access(
        "u1", "u1", "u2", "scheduled", now + timedelta(minutes=5), now + timedelta(minutes=35), now=now
    )
    with pytest.raises(HTTPException):
        PermissionChecker.verify_meeting_room_access(
            "u3", "u1", "u2", "scheduled", now + timedelta(minutes=5), now + timedelta(minutes=35), now=now
        )
    with pytest.raises(HTTPException):
        PermissionChecker.verify_meeting_room_access(
            "u1", "u1", "u2", "scheduled", now + timedelta(hours=3), now + timedelta(hours=4), now=now
        )

    # user_skills RLS gate remains disabled until remote migration verified
    assert PermissionChecker.is_user_skills_retrieval_enabled() is False


def test_sensitive_log_redaction_and_rate_limiter():
    raw = "Authorization: Bearer abc.def.ghi sk-1234567890abcdef1234 AIzaSyD12345678901234567890"
    cleaned = redact_sensitive_text(raw)
    assert "abc.def.ghi" not in cleaned
    assert "sk-1234567890abcdef1234" not in cleaned
    assert "AIzaSyD" not in cleaned

    clean_dict = redact_sensitive_dict({"api_key": "secret-val", "note": "Bearer x.y.z"})
    assert clean_dict["api_key"] == "[REDACTED]"
    assert "x.y.z" not in clean_dict["note"]

    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
    limiter.enforce("k1")
    limiter.enforce("k1")
    with pytest.raises(HTTPException) as exc:
        limiter.enforce("k1")
    assert exc.value.status_code == 429


def test_alumni_verification_submission_and_admin_approval_grants_role(client):
    cand_id = f"cand-{uuid.uuid4().hex[:8]}"
    cand_token = make_hs256_token(cand_id, f"{cand_id}@example.msgi.edu", ["student"], is_verified=False)
    cand_headers = {"Authorization": f"Bearer {cand_token}"}

    # Before verification, verified-alumni endpoint is forbidden
    pre_res = client.patch("/api/v1/alumni/me", json={"headline": "Updated"}, headers=cand_headers)
    assert pre_res.status_code == 403

    # Submit alumni verification
    sub_res = client.post(
        "/api/v1/verifications/me",
        json={"requested_role": "alumni", "graduation_year": 2022, "degree": "B.Tech", "department": "CSE"},
        headers=cand_headers,
    )
    assert sub_res.status_code == 201
    req_id = sub_res.json()["data"]["id"]

    status_res = client.get("/api/v1/verifications/me", headers=cand_headers)
    assert status_res.json()["data"]["overall_status"] == "pending"

    # Admin approves
    admin_token = make_hs256_token("admin-p3-01", "admin.p3@example.msgi.edu", ["admin"], is_verified=True)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    dec_res = client.post(
        f"/api/v1/admin/verifications/{req_id}/decision",
        json={"decision": "approved", "review_notes": "Degree verified"},
        headers=admin_headers,
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["data"]["status"] == "approved"

    # Server-side roles now grant alumni + verified status without needing a client claim change
    post_res = client.patch("/api/v1/alumni/me", json={"headline": "Verified Staff Engineer"}, headers=cand_headers)
    assert post_res.status_code == 200
    assert post_res.json()["data"]["headline"] == "Verified Staff Engineer"
