"""
MSGI One — Extended P1 API Router
Covers:
  - Projects (Module 7: Collaboration & Innovation Hub)
  - Startups (Module 8: Startup Ecosystem)
  - Impact (Module 11: Giving & Social Impact — Volunteering Only)
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.extended import StartupConnectionRequest, VolunteerInterestRequest
from src.services.extended_service import (
    list_projects,
    get_project_by_id,
    join_project_request,
    get_my_projects,
    list_startups,
    get_startup_by_id,
    create_startup_connection,
    list_impact_programmes,
    get_impact_programme,
    register_volunteer_interest,
    ProjectItem,
    ProjectMemberItem,
    StartupItem,
    StartupConnectionItem,
    ImpactProgrammeItem,
    VolunteerInterestItem,
)

router = APIRouter(tags=["Extended P1 Modules"])


# -----------------------------------------------------------------------------
# MODULE 7: PROJECTS
# -----------------------------------------------------------------------------

@router.get(
    "/projects",
    response_model=StandardEnvelope[List[ProjectItem]],
    summary="List Collaborative Projects",
)
def get_projects(
    skill: Optional[str] = Query(None, description="Filter by required skill"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[ProjectItem]]:
    items = list_projects(skill=skill, user=current_user)
    return StandardEnvelope[List[ProjectItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"total": len(items)},
    )


@router.get(
    "/projects/me",
    response_model=StandardEnvelope[List[ProjectMemberItem]],
    summary="Get My Collaborative Projects",
)
def get_user_projects(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[ProjectMemberItem]]:
    items = get_my_projects(user=current_user)
    return StandardEnvelope[List[ProjectMemberItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/projects/{project_id}",
    response_model=StandardEnvelope[ProjectItem],
    summary="Get Project Details",
)
def get_project(
    project_id: str = Path(..., description="Project ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[ProjectItem]:
    res = get_project_by_id(project_id=project_id, user=current_user)
    return StandardEnvelope[ProjectItem](
        status="success",
        data=res,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/projects/{project_id}/join-requests",
    response_model=StandardEnvelope[ProjectMemberItem],
    status_code=status.HTTP_201_CREATED,
    summary="Apply to Join a Project",
)
def apply_project(
    project_id: str = Path(..., description="Project ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[ProjectMemberItem]:
    record = join_project_request(project_id=project_id, user=current_user)
    return StandardEnvelope[ProjectMemberItem](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
    )


# -----------------------------------------------------------------------------
# MODULE 8: STARTUPS
# -----------------------------------------------------------------------------

@router.get(
    "/startups",
    response_model=StandardEnvelope[List[StartupItem]],
    summary="List Alumni and Student Startups",
)
def get_startups(
    industry: Optional[str] = Query(None, description="Industry filter"),
    stage: Optional[str] = Query(None, description="Stage filter"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[StartupItem]]:
    items = list_startups(industry=industry, stage=stage)
    return StandardEnvelope[List[StartupItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"total": len(items)},
    )


@router.get(
    "/startups/{startup_id}",
    response_model=StandardEnvelope[StartupItem],
    summary="Get Startup Details",
)
def get_startup(
    startup_id: str = Path(..., description="Startup ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[StartupItem]:
    res = get_startup_by_id(startup_id=startup_id)
    return StandardEnvelope[StartupItem](
        status="success",
        data=res,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/startups/{startup_id}/connection-requests",
    response_model=StandardEnvelope[StartupConnectionItem],
    status_code=status.HTTP_201_CREATED,
    summary="Request Introduction to a Startup Founder",
)
def request_startup_intro(
    startup_id: str = Path(..., description="Startup ID"),
    request: StartupConnectionRequest = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[StartupConnectionItem]:
    record = create_startup_connection(
        startup_id=startup_id,
        intent=request.intent,
        message=request.message,
        user=current_user,
    )
    return StandardEnvelope[StartupConnectionItem](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
    )


# -----------------------------------------------------------------------------
# MODULE 11: IMPACT
# -----------------------------------------------------------------------------

@router.get(
    "/impact/programmes",
    response_model=StandardEnvelope[List[ImpactProgrammeItem]],
    summary="List Social Impact & Volunteering Programmes",
)
def get_programmes(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[ImpactProgrammeItem]]:
    items = list_impact_programmes(user=current_user)
    return StandardEnvelope[List[ImpactProgrammeItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"total": len(items)},
    )


@router.get(
    "/impact/programmes/{programme_id}",
    response_model=StandardEnvelope[ImpactProgrammeItem],
    summary="Get Impact Programme Details",
)
def get_programme_detail(
    programme_id: str = Path(..., description="Impact Programme ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[ImpactProgrammeItem]:
    res = get_impact_programme(programme_id=programme_id, user=current_user)
    return StandardEnvelope[ImpactProgrammeItem](
        status="success",
        data=res,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/impact/programmes/{programme_id}/volunteer-interest",
    response_model=StandardEnvelope[VolunteerInterestItem],
    status_code=status.HTTP_201_CREATED,
    summary="Register Volunteer Interest for a Programme",
)
def express_volunteer_interest(
    programme_id: str = Path(..., description="Impact Programme ID"),
    request: VolunteerInterestRequest = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[VolunteerInterestItem]:
    record = register_volunteer_interest(
        programme_id=programme_id,
        interest_note=request.interest_note,
        user=current_user,
    )
    return StandardEnvelope[VolunteerInterestItem](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
    )
