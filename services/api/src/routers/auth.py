"""
MSGI One — Authentication & Session Lifecycle Router
Endpoints:
  POST /api/v1/auth/bootstrap
  POST /api/v1/auth/logout
"""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.core.security import revoke_token
from src.schemas.user import StandardEnvelope, UserProfileResponse
from src.routers.users import get_my_profile

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


@router.post(
    "/bootstrap",
    response_model=StandardEnvelope[UserProfileResponse],
    summary="Bootstrap Authenticated User",
    description="Idempotent endpoint ensuring public.users record exists for authenticated Supabase session.",
)
def bootstrap_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[UserProfileResponse]:
    """Idempotently bootstrap user state and return authenticated profile."""
    return get_my_profile(current_user=current_user)


@router.post(
    "/logout",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Revoke Current Session",
    description="Revokes the active JWT token so subsequent replays with the same token are rejected.",
)
def logout_session(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    revoked_key = None
    if current_user.raw_token:
        claims = {"jti": current_user.token_jti} if current_user.token_jti else None
        revoked_key = revoke_token(current_user.raw_token, claims)

    return StandardEnvelope(
        status="success",
        data={
            "user_id": current_user.id,
            "session_revoked": True,
            "revocation_ref": revoked_key,
        },
        timestamp=datetime.now(timezone.utc),
    )
