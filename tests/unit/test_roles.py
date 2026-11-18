"""
MSGI One — Role-Based Access Control (RBAC) Unit Tests
Tests: Permission boundaries, least privilege, rejection of unauthorized role access.
"""

import pytest
from fastapi import HTTPException
from src.core.dependencies import AuthenticatedUser, require_role


def test_student_cannot_access_admin_endpoint():
    """A user with only the 'student' role must be rejected with 403 by require_role(['admin'])."""
    student_user = AuthenticatedUser(
        id="student-uuid-1",
        email="student@example.msgi.edu",
        roles=["student"],
        is_verified=True,
    )

    admin_guard = require_role(["admin"])

    with pytest.raises(HTTPException) as exc_info:
        admin_guard(current_user=student_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "PERMISSION_DENIED"


def test_admin_can_access_admin_endpoint():
    """A user with the 'admin' role must successfully pass require_role(['admin'])."""
    admin_user = AuthenticatedUser(
        id="admin-uuid-1",
        email="admin@example.msgi.edu",
        roles=["admin"],
        is_verified=True,
    )

    admin_guard = require_role(["admin"])
    result = admin_guard(current_user=admin_user)
    assert result.id == "admin-uuid-1"
    assert "admin" in result.roles


def test_multi_role_matching():
    """A user holding 'alumni' must pass a guard permitting ['faculty', 'alumni']."""
    alumni_user = AuthenticatedUser(
        id="alumni-uuid-1",
        email="alumni@example.msgi.edu",
        roles=["alumni"],
        is_verified=True,
    )

    guard = require_role(["faculty", "alumni"])
    result = guard(current_user=alumni_user)
    assert result.id == "alumni-uuid-1"


def test_recruiter_cannot_access_faculty_endpoint():
    """A recruiter must be denied access to faculty-only resources."""
    recruiter_user = AuthenticatedUser(
        id="recruiter-uuid-1",
        email="recruiter@example.msgi.edu",
        roles=["recruiter"],
        is_verified=False,
    )

    faculty_guard = require_role(["faculty"])
    with pytest.raises(HTTPException) as exc_info:
        faculty_guard(current_user=recruiter_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "PERMISSION_DENIED"
