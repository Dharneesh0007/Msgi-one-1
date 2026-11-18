"""
MSGI One — Alumni Network Unit & Privacy Tests
Tests: Filter accuracy, verification filter, privacy suppression (FERPA/GDPR), pagination.
"""

import pytest
from fastapi import HTTPException
from src.core.dependencies import AuthenticatedUser
from src.services.alumni_service import search_alumni, get_alumni_by_id


@pytest.fixture
def student_user():
    return AuthenticatedUser(
        id="student-tester-001",
        email="student.tester@example.msgi.edu",
        first_name="Ken",
        last_name="Watanabe",
        roles=["student"],
        is_verified=True,
    )


def test_search_alumni_with_department_and_country_filter(student_user):
    """Student searches for IT alumni in Japan."""
    filters = {
        "department": "Information Technology",
        "country": "Japan",
        "verified_only": True,
    }
    result = search_alumni(filters, authenticated_user=student_user)
    assert result["total"] >= 1
    for item in result["items"]:
        assert item.country == "Japan"
        assert "Information Technology" in item.major
        assert item.is_verified is True


def test_search_alumni_excludes_unverified_records_by_default(student_user):
    """Unverified alumni must not appear in verified directory."""
    result = search_alumni({"verified_only": True}, authenticated_user=student_user)
    ids = [item.id for item in result["items"]]
    assert "alumni-unverified-test" not in ids


def test_search_alumni_excludes_private_opt_out_profiles(student_user):
    """Alumni who opted out of public directory must be completely hidden."""
    result = search_alumni({"verified_only": False}, authenticated_user=student_user)
    ids = [item.id for item in result["items"]]
    assert "alumni-private-test" not in ids


def test_search_alumni_skill_filter(student_user):
    """Filtering by skill 'PyTorch' must return matching profiles."""
    result = search_alumni({"skill": "PyTorch"}, authenticated_user=student_user)
    assert len(result["items"]) >= 1
    assert any("PyTorch" in item.skills for item in result["items"])


def test_get_alumni_by_id_masks_private_contact_info(student_user):
    """Detailed profile must not expose private email, phone, or precise residential coordinates."""
    profile = get_alumni_by_id("alumni-kenji-sato", authenticated_user=student_user)
    assert profile.full_name == "Kenji Sato"
    assert profile.current_company == "Rakuten Symphony"
    # Ensure sensitive fields are not present on the DTO
    assert not hasattr(profile, "email")
    assert not hasattr(profile, "phone")
    assert not hasattr(profile, "latitude")
    assert not hasattr(profile, "longitude")


def test_get_private_alumni_by_unauthorized_user_raises_403(student_user):
    """Requesting a private profile by an unauthorized user must raise HTTP 403."""
    with pytest.raises(HTTPException) as exc_info:
        get_alumni_by_id("alumni-private-test", authenticated_user=student_user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "PROFILE_PRIVATE"
