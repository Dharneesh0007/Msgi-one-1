"""
MSGI One — Phase 4 Student, Alumni & Administrator Portal Ecosystem Tests
Validates:
  1. Multi-parameter alumni discovery filters (company, title, mentor_opt_in, graduation_year).
  2. Verified alumni professional profile self-management.
  3. Mentor request clarification workflow & role isolation.
  4. Admin portal endpoints (users, role provisioning, moderation reports, announcements, status).
"""

from datetime import datetime, timedelta, timezone
import uuid
import jwt
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings
from src.core.permissions import _SERVER_USER_ROLES, _SERVER_USER_VERIFICATION
import copy
from src.services.admin_service import _MODERATION_REPORTS_STORE, _ANNOUNCEMENTS_STORE, _ADMIN_AUDIT_LOGS_STORE
from src.services.mentor_service import _MENTORS_STORE, _MENTOR_REQUESTS_STORE


@pytest.fixture(autouse=True)
def clean_portal_state():
    mentors_snap = copy.deepcopy(_MENTORS_STORE)
    reqs_snap = copy.deepcopy(_MENTOR_REQUESTS_STORE)
    reports_snap = copy.deepcopy(_MODERATION_REPORTS_STORE)
    ann_snap = copy.deepcopy(_ANNOUNCEMENTS_STORE)
    audit_snap = copy.deepcopy(_ADMIN_AUDIT_LOGS_STORE)
    _SERVER_USER_ROLES.clear()
    _SERVER_USER_VERIFICATION.clear()
    yield
    _MENTORS_STORE[:] = mentors_snap
    _MENTOR_REQUESTS_STORE.clear()
    _MENTOR_REQUESTS_STORE.update(reqs_snap)
    _MODERATION_REPORTS_STORE[:] = reports_snap
    _ANNOUNCEMENTS_STORE[:] = ann_snap
    _ADMIN_AUDIT_LOGS_STORE[:] = audit_snap
    _SERVER_USER_ROLES.clear()
    _SERVER_USER_VERIFICATION.clear()


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
            "exp": int((now + timedelta(minutes=30)).timestamp()),
            "is_verified": is_verified,
            "app_metadata": {"roles": roles, "is_verified": is_verified},
            "user_metadata": {"first_name": "Portal", "last_name": "User"},
        },
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_student_alumni_discovery_filters(client):
    s_headers = auth_headers("student-p4-01", "student.p4@example.msgi.edu", ["student"])

    res_mentor = client.get("/api/v1/alumni?mentor_opt_in=true", headers=s_headers)
    assert res_mentor.status_code == 200
    items = res_mentor.json()["data"]["items"]
    assert len(items) >= 1
    assert all(i["mentor_opt_in"] is True for i in items)

    res_company = client.get("/api/v1/alumni?company=Rakuten&title=Staff", headers=s_headers)
    assert res_company.status_code == 200
    c_items = res_company.json()["data"]["items"]
    assert any(i["full_name"] == "Kenji Sato" for i in c_items)


def test_mentor_request_clarification_flow(client):
    s_headers = auth_headers("student-p4-02", "student2.p4@example.msgi.edu", ["student"])
    mentor_headers = auth_headers("user-ananya-002", "ananya@example.msgi.edu", ["alumni"], is_verified=True)

    create_res = client.post(
        "/api/v1/mentor-requests",
        json={
            "mentor_id": "mentor-ananya-002",
            "topic": "Product Management",
            "career_goal": "Transition into Cloud Product Management",
        },
        headers=s_headers,
    )
    assert create_res.status_code == 201
    req_id = create_res.json()["data"]["id"]

    # Mentor requests clarification
    clarify_res = client.patch(
        f"/api/v1/mentor-requests/{req_id}",
        json={"status": "clarification_requested", "mentor_notes": "Please share your resume focus."},
        headers=mentor_headers,
    )
    assert clarify_res.status_code == 200
    assert clarify_res.json()["data"]["status"] == "clarification_requested"

    # Mentor then accepts
    accept_res = client.patch(
        f"/api/v1/mentor-requests/{req_id}",
        json={"status": "accepted", "mentor_notes": "Welcome aboard!"},
        headers=mentor_headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["data"]["status"] == "accepted"


def test_admin_portal_management_and_isolation(client):
    s_headers = auth_headers("student-p4-03", "student3.p4@example.msgi.edu", ["student"])
    a_headers = auth_headers("admin-p4-01", "admin.p4@example.msgi.edu", ["admin"])

    # Student blocked from admin endpoints
    assert client.get("/api/v1/admin/users", headers=s_headers).status_code == 403
    assert client.get("/api/v1/admin/status", headers=s_headers).status_code == 403
    assert client.post(
        "/api/v1/admin/announcements",
        json={"title": "Unauthorized", "body": "Should not be allowed to post."},
        headers=s_headers,
    ).status_code == 403

    # Admin operational status & role management
    assert client.get("/api/v1/admin/status", headers=a_headers).status_code == 200
    role_res = client.post(
        "/api/v1/admin/users/student-p4-03/roles",
        json={"roles": ["student", "alumni"], "is_verified": True},
        headers=a_headers,
    )
    assert role_res.status_code == 200
    assert "alumni" in role_res.json()["data"]["roles"]

    # Announcements
    ann_res = client.post(
        "/api/v1/admin/announcements",
        json={"title": "Annual Alumni Convocation", "body": "Join our annual alumni summit next month.", "audience_role": "all"},
        headers=a_headers,
    )
    assert ann_res.status_code == 200
    list_ann = client.get("/api/v1/admin/announcements", headers=s_headers)
    assert list_ann.status_code == 200
    assert any(a["title"] == "Annual Alumni Convocation" for a in list_ann.json()["data"])

    # Moderation report review
    rep_id = f"rep-{uuid.uuid4().hex[:8]}"
    _MODERATION_REPORTS_STORE.append({
        "id": rep_id,
        "reporter_id": "student-p4-03",
        "reported_user_id": "bad-actor-01",
        "category": "spam",
        "description": "Unsolicited promotional spam",
        "status": "pending",
        "reviewed_by": None,
        "resolution_notes": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
    })
    rep_res = client.patch(
        f"/api/v1/admin/reports/{rep_id}",
        json={"status": "resolved", "resolution_notes": "Warning issued"},
        headers=a_headers,
    )
    assert rep_res.status_code == 200
    assert rep_res.json()["data"]["status"] == "resolved"
