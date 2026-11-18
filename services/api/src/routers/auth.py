"""
MSGI One — Authentication & Bootstrap Router
Endpoints: POST /api/v1/auth/bootstrap
"""

from fastapi import APIRouter, Depends
from src.core.dependencies import AuthenticatedUser, get_current_user
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
