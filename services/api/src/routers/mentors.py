"""
MSGI One — MentorMatch API Router
Endpoints: GET /api/v1/mentors, GET /api/v1/mentors/{id}, POST /api/v1/mentor-requests,
           GET /api/v1/me/mentor-requests, PATCH /api/v1/mentor-requests/{id}
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.business import (
    MentorProfileResponse,
    MentorRequestCreate,
    MentorRequestStatusUpdate,
    MentorRequestResponse,
)
from src.services.mentor_service import (
    search_mentors,
    get_mentor_by_id,
    create_mentor_request,
    update_mentor_request_status,
    get_my_mentor_requests,
)

router = APIRouter(tags=["MentorMatch"])


@router.get(
    "/mentors",
    response_model=StandardEnvelope[List[MentorProfileResponse]],
    summary="Discover Verified Alumni Mentors",
    description="Lists verified alumni who have opted in to mentoring with open capacity.",
)
def list_mentors(
    topic: Optional[str] = Query(None, description="Advisory topic filter"),
    country: Optional[str] = Query(None, description="Country filter"),
    student_goal: Optional[str] = Query("AI Engineer", description="Student career target for ranking"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[MentorProfileResponse]]:
    filters = {
        "topic": topic,
        "country": country,
        "student_goal": student_goal,
    }
    mentors = search_mentors(filters=filters, authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=mentors,
        error=None,
        meta={"total": len(mentors)},
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/mentors/{mentor_id}",
    response_model=StandardEnvelope[MentorProfileResponse],
    summary="Get Mentor Profile Details",
)
def get_mentor(
    mentor_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MentorProfileResponse]:
    mentor = get_mentor_by_id(mentor_id=mentor_id, authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=mentor,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/mentor-requests",
    response_model=StandardEnvelope[MentorRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Mentorship Request",
    description="Submits a request to an available mentor. Rejects if mentor capacity is full or request already pending.",
)
def submit_mentor_request(
    request_data: MentorRequestCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MentorRequestResponse]:
    created_request = create_mentor_request(request_data=request_data, student=current_user)
    return StandardEnvelope(
        status="success",
        data=created_request,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/me/mentor-requests",
    response_model=StandardEnvelope[List[MentorRequestResponse]],
    summary="Get My Mentorship Requests",
    description="Returns all requests where the authenticated user is either the student or the mentor.",
)
def list_my_mentor_requests(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[MentorRequestResponse]]:
    requests = get_my_mentor_requests(user=current_user)
    return StandardEnvelope(
        status="success",
        data=requests,
        error=None,
        meta={"total": len(requests)},
        timestamp=datetime.now(timezone.utc),
    )


@router.patch(
    "/mentor-requests/{request_id}",
    response_model=StandardEnvelope[MentorRequestResponse],
    summary="Update Mentorship Request Status",
    description="Allows mentors to accept/reject, or students to cancel pending requests.",
)
def modify_mentor_request(
    request_id: str,
    status_data: MentorRequestStatusUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MentorRequestResponse]:
    updated = update_mentor_request_status(
        request_id=request_id,
        status_update=status_data,
        user=current_user,
    )
    return StandardEnvelope(
        status="success",
        data=updated,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )
