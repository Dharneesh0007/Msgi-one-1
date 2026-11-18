"""
MSGI One — Communities & Interest Groups Domain Service (Module 10)
Manages interest groups, public/private access controls, and moderation workflows.
Principles: Evans Bounded Contexts & Silberschatz Access Control.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from src.core.dependencies import AuthenticatedUser
from src.services.notifications_service import create_notification


class CommunityItem(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    is_private: bool
    creator_id: str
    member_count: int
    topics: List[str]
    created_at: str
    is_member: bool = False
    membership_status: Optional[str] = None


class CommunityMembershipItem(BaseModel):
    id: str
    community_id: str
    community_name: str
    user_id: str
    role: str  # 'member', 'moderator', 'admin'
    status: str  # 'pending', 'active', 'rejected'
    joined_at: str


# In-memory stores conforming to public.communities and public.community_memberships
_COMMUNITIES_STORE: List[Dict[str, Any]] = [
    {
        "id": "comm-ai-001",
        "name": "MSGI AI & Robotics Guild",
        "slug": "msgi-ai-robotics",
        "description": "Cross-disciplinary community for students and alumni building embodied AI, LLMs, and ROS systems.",
        "category": "Technology",
        "is_private": False,
        "creator_id": "user-kenji-001",
        "member_count": 48,
        "topics": ["AI", "Robotics", "Python", "ROS 2"],
        "created_at": "2026-09-01T00:00:00Z",
    },
    {
        "id": "comm-cloud-002",
        "name": "Cloud Native & DevOps Practitioners",
        "slug": "cloud-native-devops",
        "description": "Architectural discussions on Kubernetes, Terraform, and high-availability cloud platforms.",
        "category": "Technology",
        "is_private": False,
        "creator_id": "user-ananya-002",
        "member_count": 32,
        "topics": ["Cloud", "Kubernetes", "DevOps"],
        "created_at": "2026-09-15T00:00:00Z",
    },
    {
        "id": "comm-exec-003",
        "name": "Alumni Founders & Executive Circle (Private)",
        "slug": "alumni-founders-circle",
        "description": "Private advisory council for vetted alumni startup founders and senior executives.",
        "category": "Entrepreneurship",
        "is_private": True,
        "creator_id": "user-admin-001",
        "member_count": 12,
        "topics": ["Ventures", "Leadership", "Funding"],
        "created_at": "2026-10-01T00:00:00Z",
    },
]

_COMMUNITY_MEMBERSHIPS_STORE: List[Dict[str, Any]] = [
    {
        "id": "cm-001",
        "community_id": "comm-ai-001",
        "community_name": "MSGI AI & Robotics Guild",
        "user_id": "user-kenji-001",
        "role": "moderator",
        "status": "active",
        "joined_at": "2026-09-01T00:00:00Z",
    },
    {
        "id": "cm-002",
        "community_id": "comm-exec-003",
        "community_name": "Alumni Founders & Executive Circle (Private)",
        "user_id": "user-admin-001",
        "role": "moderator",
        "status": "active",
        "joined_at": "2026-10-01T00:00:00Z",
    },
]


def list_communities(
    category: Optional[str] = None,
    query: Optional[str] = None,
    user: Optional[AuthenticatedUser] = None,
) -> List[CommunityItem]:
    """
    Lists communities respecting privacy rules:
    Private communities are visible only to active members, creators, or administrators.
    """
    user_id = user.id if user else None
    user_roles = user.roles if user else []

    results: List[CommunityItem] = []

    for c in _COMMITIES_STORE if "_COMMITIES_STORE" in globals() else _COMMUNITIES_STORE:
        # Check membership
        membership = next(
            (m for m in _COMMUNITY_MEMBERSHIPS_STORE if m["community_id"] == c["id"] and m["user_id"] == user_id),
            None,
        )
        is_active_member = membership is not None and membership["status"] == "active"

        # Privacy guard
        if c.get("is_private", False):
            is_creator = user_id == c["creator_id"]
            is_admin = "admin" in user_roles
            if not (is_active_member or is_creator or is_admin):
                continue

        # Filters
        if category and category.lower() != c.get("category", "").lower():
            continue

        if query:
            q_lower = query.lower()
            name_match = q_lower in c["name"].lower()
            desc_match = q_lower in c["description"].lower()
            topic_match = any(q_lower in t.lower() for t in c.get("topics", []))
            if not (name_match or desc_match or topic_match):
                continue

        results.append(CommunityItem(
            **c,
            is_member=is_active_member,
            membership_status=membership["status"] if membership else None,
        ))

    return results


def get_community_by_id(community_id: str, user: AuthenticatedUser) -> CommunityItem:
    comm = next((c for c in _COMMUNITIES_STORE if c["id"] == community_id), None)
    if not comm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMUNITY_NOT_FOUND", "message": f"Community '{community_id}' does not exist."},
        )

    membership = next(
        (m for m in _COMMUNITY_MEMBERSHIPS_STORE if m["community_id"] == community_id and m["user_id"] == user.id),
        None,
    )

    if comm.get("is_private", False):
        if not (membership and membership["status"] == "active") and user.id != comm["creator_id"] and "admin" not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PRIVATE_COMMUNITY", "message": "This community is private and requires approved membership."},
            )

    return CommunityItem(
        **comm,
        is_member=membership is not None and membership["status"] == "active",
        membership_status=membership["status"] if membership else None,
    )


def join_community(community_id: str, user: AuthenticatedUser) -> CommunityMembershipItem:
    """
    Joins a public community or creates a pending membership request for private groups.
    Enforces duplicate prevention: UNIQUE(community_id, user_id).
    """
    comm = next((c for c in _COMMUNITIES_STORE if c["id"] == community_id), None)
    if not comm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMUNITY_NOT_FOUND", "message": f"Community '{community_id}' not found."},
        )

    # Check for existing membership
    existing = next(
        (m for m in _COMMUNITY_MEMBERSHIPS_STORE if m["community_id"] == community_id and m["user_id"] == user.id),
        None,
    )
    if existing:
        if existing["status"] == "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DUPLICATE_MEMBERSHIP", "message": "You are already a member of this community."},
            )
        elif existing["status"] == "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "PENDING_REQUEST_EXISTS", "message": "Your membership request is currently pending moderator review."},
            )

    membership_status = "pending" if comm.get("is_private", False) else "active"
    mem_id = f"cm-{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    record = {
        "id": mem_id,
        "community_id": community_id,
        "community_name": comm["name"],
        "user_id": user.id,
        "role": "member",
        "status": membership_status,
        "joined_at": now_iso,
    }
    _COMMUNITY_MEMBERSHIPS_STORE.append(record)

    if membership_status == "active":
        comm["member_count"] += 1
        create_notification(
            user_id=user.id,
            event_type="community_joined",
            entity_id=community_id,
            title="Joined Community",
            message=f"You are now an active member of {comm['name']}.",
            payload={"community_id": community_id, "slug": comm["slug"]},
        )
    else:
        # Notify community creator of pending review
        create_notification(
            user_id=comm["creator_id"],
            event_type="community_membership_requested",
            entity_id=community_id,
            title="New Membership Request",
            message=f"{user.first_name} requested to join {comm['name']}.",
            payload={"community_id": community_id, "applicant_id": user.id},
        )

    return CommunityMembershipItem(**record)


def get_my_communities(user: AuthenticatedUser) -> List[CommunityMembershipItem]:
    user_mems = [m for m in _COMMUNITY_MEMBERSHIPS_STORE if m["user_id"] == user.id]
    return [CommunityMembershipItem(**m) for m in user_mems]


def update_membership_status(
    community_id: str,
    membership_id: str,
    new_status: str,
    moderator: AuthenticatedUser,
) -> CommunityMembershipItem:
    """
    Moderator approves or rejects a membership request for a private community.
    Enforces authorization: Only community creator or admin can moderate.
    """
    comm = next((c for c in _COMMUNITIES_STORE if c["id"] == community_id), None)
    if not comm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMUNITY_NOT_FOUND", "message": "Community not found."},
        )

    if moderator.id != comm["creator_id"] and "admin" not in moderator.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "MODERATOR_REQUIRED", "message": "Only community moderators or institutional admins can decide membership requests."},
        )

    mem = next((m for m in _COMMUNITY_MEMBERSHIPS_STORE if m["id"] == membership_id and m["community_id"] == community_id), None)
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MEMBERSHIP_NOT_FOUND", "message": "Membership request not found."},
        )

    if new_status not in ("active", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATUS", "message": "Status must be 'active' or 'rejected'."},
        )

    mem["status"] = new_status
    if new_status == "active":
        comm["member_count"] += 1

    # Notify applicant of decision
    create_notification(
        user_id=mem["user_id"],
        event_type="community_membership_decided",
        entity_id=community_id,
        title="Community Request Decided",
        message=f"Your request to join {comm['name']} was {new_status}.",
        payload={"community_id": community_id, "decision": new_status},
    )

    return CommunityMembershipItem(**mem)
