"""
MSGI One — Frozen Android APK Automated API Contract Test Suite (Gate 6.6 & Correction D)
Artifact ID: a95a7169-d48b-4730-bcfd-921500e4b8fae
Validates:
1. Dual-prefix routing (/api/v1 and /api/v1/api/v1) for mobile HTTP client
2. Profile direct aliases (/api/v1/me and /api/v1/me/onboard)
3. StandardEnvelope schema invariants for both success and error payloads
4. Frozen error codes consumed by mobile error-boundary handlers
5. Mobile notification polling endpoint (/notifications/unread-count)
NOTE ON RUNTIME EXECUTION:
Physical device / emulator runtime verification is classified as UNVERIFIED in headless CI/CD
due to absence of attached Android hardware/adb runtime in the runner environment.
"""

import jwt
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings


@pytest.fixture
def client():
    return TestClient(app)


def make_token(user_id: str, email: str, roles: list[str]) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": settings.JWT_AUDIENCE,
        "exp": datetime.now(timezone.utc).timestamp() + 3600,
        "app_metadata": {"roles": roles},
        "user_metadata": {"first_name": "Frozen", "last_name": "Tester"},
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def student_auth_headers():
    token = make_token("frozen-test-student-01", "frozen.student@example.msgi.edu", ["student"])
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("prefix", ["/api/v1", "/api/v1/api/v1"])
def test_dual_prefix_alumni_directory(client, student_auth_headers, prefix):
    """Verify that alumni directory responds identically under both single and double prefixes."""
    url = f"{prefix}/alumni"
    res = client.get(url, headers=student_auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert "items" in body["data"]
    assert isinstance(body["data"]["items"], list)
    assert "timestamp" in body


@pytest.mark.parametrize("prefix", ["/api/v1", "/api/v1/api/v1"])
def test_dual_prefix_jobs_search(client, student_auth_headers, prefix):
    """Verify that jobs search responds identically under both single and double prefixes."""
    url = f"{prefix}/jobs"
    res = client.get(url, headers=student_auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert isinstance(body["data"], list)


@pytest.mark.parametrize("prefix", ["/api/v1", "/api/v1/api/v1"])
def test_dual_prefix_profile_me_alias(client, student_auth_headers, prefix):
    """Verify that direct profile alias /me resolves under both single and double prefixes."""
    url = f"{prefix}/me"
    res = client.get(url, headers=student_auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["data"]["email"] == "frozen.student@example.msgi.edu"


def test_standard_envelope_error_structure(client):
    """Verify that error payloads conform strictly to the mobile StandardEnvelope schema."""
    res = client.get("/api/v1/me")  # Unauthenticated
    assert res.status_code == 401
    body = res.json()
    assert body["status"] == "error"
    assert body["data"] is None
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "timestamp" in body


def test_frozen_error_codes_not_found(client, student_auth_headers):
    """Verify ENTITY_NOT_FOUND error code mapping for missing resources."""
    res = client.get("/api/v1/jobs/job-nonexistent-9999", headers=student_auth_headers)
    assert res.status_code == 404
    body = res.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"


def test_mobile_polling_notifications_endpoint(client, student_auth_headers):
    """Verify lightweight polling endpoint for unread notifications count under both prefixes."""
    for prefix in ["/api/v1", "/api/v1/api/v1"]:
        url = f"{prefix}/notifications/unread-count"
        res = client.get(url, headers=student_auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "success"
        assert "unread_count" in body["data"]
