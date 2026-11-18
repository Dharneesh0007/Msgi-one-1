"""
MSGI One — User Profiles & Schema Validation Unit Tests
Tests: Schema extra field prevention, envelope formatting, privacy masking.
"""

import pytest
from pydantic import ValidationError
from src.core.dependencies import AuthenticatedUser
from src.schemas.user import UserUpdateRequest, UserOnboardingRequest
from src.routers.users import get_my_profile, update_my_profile, get_public_user_profile, complete_onboarding


def test_user_update_request_forbids_role_modification():
    """Attempting to inject 'role' or 'is_verified' in UserUpdateRequest must raise ValidationError."""
    with pytest.raises(ValidationError):
        UserUpdateRequest(
            first_name="Hacker",
            role="admin",  # Extra field -> must be rejected
        )

    with pytest.raises(ValidationError):
        UserUpdateRequest(
            first_name="Hacker",
            is_verified=True,  # Extra field -> must be rejected
        )


def test_user_update_request_accepts_valid_fields():
    """Permitted fields (first_name, last_name, avatar_url) must validate cleanly."""
    req = UserUpdateRequest(
        first_name="Taro",
        last_name="Yamada",
        avatar_url="https://example.com/avatar.jpg",
    )
    assert req.first_name == "Taro"
    assert req.last_name == "Yamada"


def test_get_my_profile_returns_envelope():
    """get_my_profile returns valid MSGI One Standard Envelope."""
    user = AuthenticatedUser(
        id="user-taro-123",
        email="taro.yamada@example.msgi.edu",
        first_name="Taro",
        last_name="Yamada",
        roles=["student"],
        is_verified=True,
    )

    response = get_my_profile(current_user=user)
    assert response.status == "success"
    assert response.error is None
    assert response.data.id == "user-taro-123"
    assert response.data.email == "taro.yamada@example.msgi.edu"
    assert response.data.roles == ["student"]
    assert response.data.is_profile_complete is True


def test_update_my_profile_persists_changes():
    """update_my_profile updates permitted fields."""
    user = AuthenticatedUser(
        id="user-update-456",
        email="update.user@example.msgi.edu",
        first_name="Initial",
        last_name="Name",
        roles=["student"],
    )

    update_payload = UserUpdateRequest(first_name="UpdatedFirst", last_name="UpdatedLast")
    response = update_my_profile(update_data=update_payload, current_user=user)

    assert response.status == "success"
    assert response.data.first_name == "UpdatedFirst"
    assert response.data.last_name == "UpdatedLast"


def test_complete_onboarding():
    """complete_onboarding persists first_name, last_name, department."""
    user = AuthenticatedUser(
        id="user-onboard-789",
        email="new.student@example.msgi.edu",
        roles=["student"],
    )

    onboard_payload = UserOnboardingRequest(
        first_name="Shinji",
        last_name="Ikari",
        department="Robotics Engineering",
        requested_role="student",
    )
    response = complete_onboarding(onboarding_data=onboard_payload, current_user=user)

    assert response.status == "success"
    assert response.data.first_name == "Shinji"
    assert response.data.last_name == "Ikari"
    assert response.data.is_profile_complete is True


def test_public_user_profile_masks_sensitive_data():
    """get_public_user_profile returns public attributes without private contact details."""
    current_user = AuthenticatedUser(
        id="viewer-1",
        email="viewer@example.msgi.edu",
        roles=["student"],
    )

    response = get_public_user_profile(user_id="alumni-kenji-sato", current_user=current_user)
    assert response.status == "success"
    assert response.data.full_name == "Kenji Sato"
    assert response.data.role == "alumni"
    assert not hasattr(response.data, "email")
    assert not hasattr(response.data, "phone")


def test_direct_me_aliases_return_valid_envelope():
    """Verify that direct /api/v1/me alias handlers function identically to /api/v1/users/me."""
    from src.main import direct_get_me, direct_patch_me, direct_onboard_me

    user = AuthenticatedUser(
        id="user-alias-test",
        email="alias.test@example.msgi.edu",
        first_name="Aoi",
        last_name="Takahashi",
        roles=["student"],
        is_verified=True,
    )

    get_res = direct_get_me(current_user=user)
    assert get_res.status == "success"
    assert get_res.data.id == "user-alias-test"
    assert get_res.data.first_name == "Aoi"

    patch_res = direct_patch_me(
        update_data=UserUpdateRequest(first_name="AoiUpdated"),
        current_user=user,
    )
    assert patch_res.status == "success"
    assert patch_res.data.first_name == "AoiUpdated"

    onboard_res = direct_onboard_me(
        onboarding_data=UserOnboardingRequest(first_name="AoiFinal", last_name="Takahashi"),
        current_user=user,
    )
    assert onboard_res.status == "success"
    assert onboard_res.data.first_name == "AoiFinal"

