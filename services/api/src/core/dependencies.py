"""
MSGI One — FastAPI Security & Role Authorization Dependencies
Principle: Complete Mediation & Principle of Least Privilege (Pressman Ch. 9).
"""

from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from src.core.security import verify_jwt_token


class AuthenticatedUser(BaseModel):
    """Server-side verified authenticated user context."""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: List[str] = ["student"]
    is_verified: bool = False
    is_active: bool = True


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> AuthenticatedUser:
    """
    Extract and cryptographically verify Bearer JWT.
    Enforces that identity is derived solely from the validated token subject (sub).
    Never trusts user_id or role submitted in request bodies.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHENTICATED",
                "message": "Authorization header is required with Bearer token.",
            },
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MALFORMED_HEADER",
                "message": "Authorization header must be formatted as 'Bearer <token>'.",
            },
        )

    token = parts[1]
    claims = verify_jwt_token(token)

    user_id = claims["sub"]
    email = claims.get("email", "unknown@example.msgi.edu")

    # Extract roles from custom claims or app_metadata if present, default to student
    app_metadata = claims.get("app_metadata", {})
    user_roles = app_metadata.get("roles", ["student"])
    if not isinstance(user_roles, list) or len(user_roles) == 0:
        user_roles = ["student"]

    # Verify active state
    if claims.get("is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "Account has been deactivated."},
        )

    return AuthenticatedUser(
        id=user_id,
        email=email,
        first_name=claims.get("user_metadata", {}).get("first_name"),
        last_name=claims.get("user_metadata", {}).get("last_name"),
        avatar_url=claims.get("user_metadata", {}).get("avatar_url"),
        roles=user_roles,
        is_verified=claims.get("is_verified", False),
        is_active=True,
    )


def require_role(allowed_roles: List[str]):
    """
    Dependency factory enforcing server-side Role-Based Access Control (RBAC).
    Rejects any user not possessing at least one of the specified allowed_roles with HTTP 403.
    """
    def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not any(role in allowed_roles for role in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": f"Access denied. Requires one of the following roles: {allowed_roles}. You hold: {current_user.roles}.",
                },
            )
        return current_user

    return role_checker
