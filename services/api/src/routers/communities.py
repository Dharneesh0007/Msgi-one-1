"""
MSGI One — Communities API Router (Module 10)
Endpoints:
  GET   /api/v1/communities
  GET   /api/v1/communities/{id}
  POST  /api/v1/communities/{id}/join
  GET   /api/v1/communities/me
  PATCH /api/v1/communities/{id}/memberships/{membership_id}
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.extended import MembershipUpdateRequest
from src.services.community_service import (
    list_communities,
    get_community_by_id,
    join_community,
    get_my_communities,
    update_membership_status,
    CommunityItem,
    CommunityMembershipItem,
)

router = APIRouter(prefix="/communities", tags=["Communities & Groups"])


@router.get(
    "",
    response_model=StandardEnvelope[List[CommunityItem]],
    summary="List Accessible Communities",
)
def get_communities(
    category: Optional[str] = Query(None, description="Category filter"),
    query: Optional[str] = Query(None, description="Search query"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[CommunityItem]]:
    items = list_communities(category=category, query=query, user=current_user)
    return StandardEnvelope[List[CommunityItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"total": len(items)},
    )


@router.get(
    "/me",
    response_model=StandardEnvelope[List[CommunityMembershipItem]],
    summary="Get My Community Memberships",
)
def get_user_communities(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[CommunityMembershipItem]]:
    items = get_my_communities(user=current_user)
    return StandardEnvelope[List[CommunityMembershipItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"memberships_count": len(items)},
    )


@router.get(
    "/{community_id}",
    response_model=StandardEnvelope[CommunityItem],
    summary="Get Community Details",
)
def get_community(
    community_id: str = Path(..., description="Community ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[CommunityItem]:
    res = get_community_by_id(community_id=community_id, user=current_user)
    return StandardEnvelope[CommunityItem](
        status="success",
        data=res,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/{community_id}/join",
    response_model=StandardEnvelope[CommunityMembershipItem],
    status_code=status.HTTP_201_CREATED,
    summary="Join or Request Membership to a Community",
)
def join_group(
    community_id: str = Path(..., description="Community ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[CommunityMembershipItem]:
    record = join_community(community_id=community_id, user=current_user)
    return StandardEnvelope[CommunityMembershipItem](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
    )


@router.patch(
    "/{community_id}/memberships/{membership_id}",
    response_model=StandardEnvelope[CommunityMembershipItem],
    summary="Moderate Community Membership Request",
)
def moderate_membership(
    community_id: str = Path(..., description="Community ID"),
    membership_id: str = Path(..., description="Membership request ID"),
    request: MembershipUpdateRequest = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[CommunityMembershipItem]:
    record = update_membership_status(
        community_id=community_id,
        membership_id=membership_id,
        new_status=request.status,
        moderator=current_user,
    )
    return StandardEnvelope[CommunityMembershipItem](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
        meta={"moderated_status": request.status},
    )
