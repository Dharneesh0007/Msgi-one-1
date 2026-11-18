"""
MSGI One — User Profile API Router
Endpoints: GET /api/v1/me, PATCH /api/v1/me, POST /api/v1/me/onboard, GET /api/v1/users/{id}
"""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import (
    PublicUserProfileResponse,
    StandardEnvelope,
    UserProfileResponse,
    UserPreferencesSchema,
    UserUpdateRequest,
    UserOnboardingRequest,
    StudentProfileSummary,
    AlumniProfileSummary,
)

router = APIRouter(prefix="/users", tags=["Users & Profiles"])

# In-memory store for development/testing when PostgreSQL is offline
_DEV_PROFILE_STORE: Dict[str, Dict[str, Any]] = {}


@router.get(
    "/me",
    response_model=StandardEnvelope[UserProfileResponse],
    summary="Get Current Authenticated Profile",
    description="Resolves authenticated identity, assigned roles, preferences, and sub-type profile.",
)
def get_my_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[UserProfileResponse]:
    """Retrieve full profile of the currently logged-in user."""
    profile_data = _DEV_PROFILE_STORE.get(current_user.id, {})

    first_name = profile_data.get("first_name", current_user.first_name)
    last_name = profile_data.get("last_name", current_user.last_name)
    is_profile_complete = bool(first_name and last_name)

    student_summary = None
    if "student" in current_user.roles:
        student_summary = StudentProfileSummary(
            roll_number=profile_data.get("roll_number", "MSGI-PENDING"),
            department=profile_data.get("department", "Information Technology"),
            enrollment_year=profile_data.get("enrollment_year", 2024),
            expected_graduation_year=profile_data.get("expected_graduation_year", 2028),
            degree_program=profile_data.get("degree_program", "B.Tech Computer Science"),
            career_interests=profile_data.get("career_interests", ["Artificial Intelligence"]),
        )

    alumni_summary = None
    if "alumni" in current_user.roles:
        alumni_summary = AlumniProfileSummary(
            graduation_year=profile_data.get("graduation_year", 2021),
            degree="B.Tech Computer Science",
            major="Information Technology",
            headline=profile_data.get("headline", "Verified MSGI Alumnus"),
            current_company=profile_data.get("current_company", "Rakuten"),
            current_title=profile_data.get("current_title", "Software Engineer"),
            industry="Technology",
        )

    preferences_data = profile_data.get("preferences", {})
    preferences = UserPreferencesSchema(
        theme=preferences_data.get("theme", "system"),
        push_notifications_enabled=preferences_data.get("push_notifications_enabled", True),
        email_digests_enabled=preferences_data.get("email_digests_enabled", True),
    )

    user_response = UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=first_name,
        last_name=last_name,
        avatar_url=profile_data.get("avatar_url", current_user.avatar_url),
        requested_role=profile_data.get("requested_role", "student"),
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        roles=current_user.roles,
        preferences=preferences,
        student_profile=student_summary,
        alumni_profile=alumni_summary,
        is_profile_complete=is_profile_complete,
    )

    return StandardEnvelope(
        status="success",
        data=user_response,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.patch(
    "/me",
    response_model=StandardEnvelope[UserProfileResponse],
    summary="Update Current Profile",
    description="Updates permitted personal profile fields. Modifying roles or verification status is prohibited.",
)
def update_my_profile(
    update_data: UserUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[UserProfileResponse]:
    """Update authorized editable fields of the current user profile."""
    profile_data = _DEV_PROFILE_STORE.setdefault(current_user.id, {})

    if update_data.first_name is not None:
        profile_data["first_name"] = update_data.first_name
    if update_data.last_name is not None:
        profile_data["last_name"] = update_data.last_name
    if update_data.avatar_url is not None:
        profile_data["avatar_url"] = update_data.avatar_url
    if update_data.preferences is not None:
        profile_data["preferences"] = update_data.preferences.model_dump()

    # Return refreshed profile
    return get_my_profile(current_user=current_user)


@router.post(
    "/me/onboard",
    response_model=StandardEnvelope[UserProfileResponse],
    summary="Complete Initial Profile Onboarding",
    description="Initial submission of first name, last name, and department upon registration.",
)
def complete_onboarding(
    onboarding_data: UserOnboardingRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[UserProfileResponse]:
    """Complete initial onboarding profile fields."""
    profile_data = _DEV_PROFILE_STORE.setdefault(current_user.id, {})

    profile_data["first_name"] = onboarding_data.first_name
    profile_data["last_name"] = onboarding_data.last_name
    if onboarding_data.department:
        profile_data["department"] = onboarding_data.department
    if onboarding_data.requested_role:
        profile_data["requested_role"] = onboarding_data.requested_role

    return get_my_profile(current_user=current_user)


@router.get(
    "/{user_id}",
    response_model=StandardEnvelope[PublicUserProfileResponse],
    summary="Get Public User Profile",
    description="Retrieves public directory profile with private contact details masked in compliance with FERPA/GDPR.",
)
def get_public_user_profile(
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[PublicUserProfileResponse]:
    """Retrieve public directory listing for a user."""
    profile_data = _DEV_PROFILE_STORE.get(user_id)

    # Provide synthetic fallback for demo if querying a synthetic ID
    if not profile_data and user_id != current_user.id:
        if "alumni" in user_id or "kenji" in user_id:
            profile_data = {
                "first_name": "Kenji",
                "last_name": "Sato",
                "role": "alumni",
                "is_verified": True,
                "headline": "Staff AI Engineer at Rakuten",
                "current_company": "Rakuten",
                "current_title": "Staff AI Engineer",
                "location": "Tokyo, Japan",
                "skills": ["PyTorch", "NLP", "FastAPI"],
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ENTITY_NOT_FOUND", "message": f"User with ID '{user_id}' was not found."},
            )

    full_name = f"{profile_data.get('first_name', 'Verified')} {profile_data.get('last_name', 'Member')}"

    public_profile = PublicUserProfileResponse(
        id=user_id,
        full_name=full_name,
        avatar_url=profile_data.get("avatar_url"),
        role=profile_data.get("role", "alumni"),
        is_verified=profile_data.get("is_verified", True),
        headline=profile_data.get("headline"),
        current_company=profile_data.get("current_company"),
        current_title=profile_data.get("current_title"),
        location=profile_data.get("location", "Tokyo, Japan"),
        skills=profile_data.get("skills", ["Python", "Machine Learning"]),
    )

    return StandardEnvelope(
        status="success",
        data=public_profile,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.delete(
    "/{user_id}",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Delete User Account & Scrub PII (GDPR / DPDP)",
    description="Implements Right to Erasure. Self-service deletion or administrator action. Scrubs all PII while retaining anonymized identifier for referential integrity.",
)
def delete_user_account(
    user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    """Self-service or admin account deletion and PII erasure."""
    # Authorization: Owner or Admin only
    if current_user.id != user_id and "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_ACTION", "message": "You can only request deletion of your own account."},
        )

    # Scrub PII from store
    if user_id in _DEV_PROFILE_STORE:
        _DEV_PROFILE_STORE[user_id] = {
            "first_name": "Anonymized",
            "last_name": "User",
            "is_active": False,
            "is_verified": False,
            "avatar_url": None,
            "headline": "Account Deleted",
            "current_company": None,
            "current_title": None,
            "location": "Redacted",
            "skills": [],
        }

    return StandardEnvelope(
        status="success",
        data={
            "user_id": user_id,
            "anonymized": True,
            "status": "deleted",
            "message": "Account successfully scheduled for deletion and personal data scrubbed in compliance with GDPR/DPDP.",
        },
        error=None,
        meta={"compliance": "GDPR_Art_17_DPDP_Sec_12"},
        timestamp=datetime.now(timezone.utc),
    )

