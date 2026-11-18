"""
MSGI One — Learning Academy API Router (Module 9)
Endpoints:
  GET   /api/v1/learning/resources
  GET   /api/v1/learning/resources/{id}
  POST  /api/v1/learning/enrollments
  GET   /api/v1/learning/me
  PATCH /api/v1/learning/progress/{id}
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.extended import EnrollmentRequest, ProgressUpdateRequest
from src.services.learning_service import (
    list_learning_resources,
    get_learning_resource,
    enroll_in_course,
    get_my_learning,
    update_learning_progress,
    LearningResourceItem,
    CourseEnrollmentItem,
)

router = APIRouter(prefix="/learning", tags=["Learning Academy"])


@router.get(
    "/resources",
    response_model=StandardEnvelope[List[LearningResourceItem]],
    summary="List Learning Courseware Resources",
)
def get_resources(
    skill: Optional[str] = Query(None, description="Filter by skill or title"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[LearningResourceItem]]:
    items = list_learning_resources(skill=skill, difficulty=difficulty)
    return StandardEnvelope[List[LearningResourceItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"total": len(items)},
    )


@router.get(
    "/resources/{resource_id}",
    response_model=StandardEnvelope[LearningResourceItem],
    summary="Get Learning Resource Details",
)
def get_resource_details(
    resource_id: str = Path(..., description="Courseware resource ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[LearningResourceItem]:
    res = get_learning_resource(resource_id=resource_id)
    return StandardEnvelope[LearningResourceItem](
        status="success",
        data=res,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/enrollments",
    response_model=StandardEnvelope[CourseEnrollmentItem],
    status_code=status.HTTP_201_CREATED,
    summary="Enroll in a Learning Resource",
)
def create_enrollment(
    request: EnrollmentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[CourseEnrollmentItem]:
    record = enroll_in_course(resource_id=request.resource_id, user=current_user)
    return StandardEnvelope[CourseEnrollmentItem](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/me",
    response_model=StandardEnvelope[List[CourseEnrollmentItem]],
    summary="Get My Active Enrollments and Progress",
)
def get_my_enrollments(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[CourseEnrollmentItem]]:
    items = get_my_learning(user=current_user)
    return StandardEnvelope[List[CourseEnrollmentItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"enrolled_count": len(items)},
    )


@router.patch(
    "/progress/{enrollment_id}",
    response_model=StandardEnvelope[CourseEnrollmentItem],
    summary="Update Course Progress Percentage",
)
def update_progress(
    enrollment_id: str = Path(..., description="Enrollment record ID"),
    request: ProgressUpdateRequest = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[CourseEnrollmentItem]:
    record = update_learning_progress(
        enrollment_id=enrollment_id,
        progress_percentage=request.progress_percentage,
        user=current_user,
    )
    return StandardEnvelope[CourseEnrollmentItem](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
    )
