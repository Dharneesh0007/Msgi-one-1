"""
MSGI One — FastAPI Security & Role Authorization Dependencies
Principle: Complete Mediation & Principle of Least Privilege (Sommerville, Pressman, Martin).
"""

from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from src.core.permissions import PermissionChecker
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
    token_jti: Optional[str] = None
    raw_token: Optional[str] = None


def authenticate_bearer_token(token: str) -> AuthenticatedUser:
    """Shared token-to-AuthenticatedUser resolution for HTTP, SSE, and WebSockets."""
    claims = verify_jwt_token(token)

    user_id = claims["sub"]
    email = claims.get("email", "unknown@example.msgi.edu")

    if claims.get("is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "Account has been deactivated."},
        )

    user_roles = PermissionChecker.resolve_server_roles(user_id, claims)
    is_verified = PermissionChecker.resolve_verification_status(user_id, claims)

    user_meta = claims.get("user_metadata") or {}
    return AuthenticatedUser(
        id=user_id,
        email=email,
        first_name=user_meta.get("first_name"),
        last_name=user_meta.get("last_name"),
        avatar_url=user_meta.get("avatar_url"),
        roles=user_roles,
        is_verified=is_verified,
        is_active=True,
        token_jti=claims.get("jti"),
        raw_token=token,
    )


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

    return authenticate_bearer_token(parts[1])


def authenticate_websocket_token(token: Optional[str]) -> AuthenticatedUser:
    """Authenticate WebSocket connection via query/header JWT."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "WebSocket authentication token is required."},
        )
    if token.lower().startswith("bearer "):
        token = token.split(None, 1)[1]
    return authenticate_bearer_token(token)


def require_role(allowed_roles: List[str]):
    """
    Dependency factory enforcing server-side Role-Based Access Control (RBAC).
    Rejects any user not possessing at least one of the specified allowed_roles with HTTP 403.
    """
    def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        PermissionChecker.require_roles(current_user.roles, allowed_roles)
        return current_user

    return role_checker


def require_verified_alumni(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Dependency enforcing verified institutional alumni status (or admin)."""
    PermissionChecker.require_verified_alumni(current_user.roles, current_user.is_verified)
    return current_user
