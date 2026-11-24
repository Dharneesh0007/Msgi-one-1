"""
MSGI One — Shared Authorization & Permission Policy Gateway (Phase 3)
Consumed uniformly by REST Routers, WebSocket Handlers, LiveKit Room Tokens, and AI Tools.
Principles: Robert C. Martin (Clean Architecture), Saltzer & Schroeder (Complete Mediation & Least Privilege).
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
from fastapi import HTTPException, status

# Authoritative server-side role & verification state overrides (synced from DB/admin verification)
_SERVER_USER_ROLES: Dict[str, List[str]] = {}
_SERVER_USER_VERIFICATION: Dict[str, bool] = {}

VALID_ROLES: Set[str] = {"student", "alumni", "faculty", "recruiter", "admin"}

# Per Directive Phase 3: user_skills RLS migration (20261121000002_user_skills_rls_patch.sql)
# has not been applied remotely; keep protected AI retrieval disabled until explicitly verified.
USER_SKILLS_RLS_VERIFIED_REMOTELY: bool = False


class PermissionChecker:
    """Centralized server-side policy enforcement shared across all transport & AI boundaries."""

    @staticmethod
    def set_user_roles(user_id: str, roles: List[str], is_verified: Optional[bool] = None) -> List[str]:
        sanitized = [r for r in roles if r in VALID_ROLES]
        if not sanitized:
            sanitized = ["student"]
        _SERVER_USER_ROLES[user_id] = list(dict.fromkeys(sanitized))
        if is_verified is not None:
            _SERVER_USER_VERIFICATION[user_id] = bool(is_verified)
        return _SERVER_USER_ROLES[user_id]

    @staticmethod
    def grant_role(user_id: str, role: str, mark_verified: bool = True) -> List[str]:
        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_ROLE", "message": f"Role '{role}' is not recognized."},
            )
        existing = list(_SERVER_USER_ROLES.get(user_id, ["student"]))
        if role not in existing:
            existing.append(role)
        _SERVER_USER_ROLES[user_id] = existing
        if mark_verified:
            _SERVER_USER_VERIFICATION[user_id] = True
        return existing

    @staticmethod
    def resolve_server_roles(user_id: str, claims: Dict[str, Any]) -> List[str]:
        """
        Resolve authoritative roles strictly from server-side state or Supabase-signed app_metadata.
        NEVER trusts user_metadata or client request headers/bodies.
        """
        if user_id in _SERVER_USER_ROLES:
            return list(_SERVER_USER_ROLES[user_id])

        app_metadata = claims.get("app_metadata") or {}
        raw_roles = app_metadata.get("roles", ["student"])
        if not isinstance(raw_roles, list) or len(raw_roles) == 0:
            return ["student"]
        valid = [r for r in raw_roles if r in VALID_ROLES]
        return valid or ["student"]

    @staticmethod
    def resolve_verification_status(user_id: str, claims: Dict[str, Any]) -> bool:
        if user_id in _SERVER_USER_VERIFICATION:
            return _SERVER_USER_VERIFICATION[user_id]
        app_metadata = claims.get("app_metadata") or {}
        if "is_verified" in app_metadata:
            return bool(app_metadata["is_verified"])
        return bool(claims.get("is_verified", False))

    @staticmethod
    def require_roles(user_roles: List[str], allowed_roles: List[str]) -> None:
        if not any(r in allowed_roles for r in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": f"Access denied. Requires one of {allowed_roles}. Held: {user_roles}.",
                },
            )

    @staticmethod
    def require_verified_alumni(user_roles: List[str], is_verified: bool) -> None:
        if "admin" in user_roles:
            return
        if "alumni" not in user_roles or not is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "VERIFIED_ALUMNI_REQUIRED",
                    "message": "Institutional alumni verification is required to perform this action.",
                },
            )

    @staticmethod
    def verify_conversation_access(
        user_id: str,
        participant_one_id: str,
        participant_two_id: str,
        is_blocked: bool = False,
    ) -> None:
        if user_id not in (participant_one_id, participant_two_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "You are not a participant in this conversation."},
            )
        if is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "USER_BLOCKED", "message": "Communication is blocked between these users."},
            )

    @staticmethod
    def verify_meeting_room_access(
        user_id: str,
        student_id: str,
        alumni_id: str,
        meeting_status: str,
        scheduled_start: datetime,
        scheduled_end: datetime,
        is_blocked: bool = False,
        now: Optional[datetime] = None,
        early_join_minutes: int = 15,
        grace_after_minutes: int = 30,
    ) -> None:
        if user_id not in (student_id, alumni_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "Only confirmed meeting participants may join this room."},
            )
        if is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "USER_BLOCKED", "message": "Meeting admission denied due to active user block."},
            )
        if meeting_status in ("cancelled", "completed", "no_show"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "MEETING_NOT_ACTIVE", "message": f"Cannot join meeting in status '{meeting_status}'."},
            )
        current = now or datetime.now(timezone.utc)
        earliest = scheduled_start - timedelta(minutes=early_join_minutes)
        latest = scheduled_end + timedelta(minutes=grace_after_minutes)
        if current < earliest or current > latest:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "OUTSIDE_JOIN_WINDOW", "message": "Meeting room is only accessible within the permitted joining window."},
            )

    @staticmethod
    def is_user_skills_retrieval_enabled() -> bool:
        return USER_SKILLS_RLS_VERIFIED_REMOTELY
