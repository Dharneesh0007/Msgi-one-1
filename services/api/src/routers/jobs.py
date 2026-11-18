"""
MSGI One — CareerBridge API Router
Endpoints: GET /api/v1/jobs, GET /api/v1/jobs/{id}, POST /api/v1/jobs,
           POST /api/v1/jobs/{id}/applications, GET /api/v1/me/applications
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.business import (
    JobResponse,
    JobCreateRequest,
    JobApplicationRequest,
    JobApplicationResponse,
)
from src.services.jobs_service import (
    search_jobs,
    get_job_by_id,
    create_job,
    submit_job_application,
    get_student_applications,
)

router = APIRouter(tags=["CareerBridge"])


@router.get(
    "/jobs",
    response_model=StandardEnvelope[List[JobResponse]],
    summary="List Career Opportunities",
    description="Search active jobs and internships with automatic skill match analysis.",
)
def list_jobs(
    opportunity_type: Optional[str] = Query(None, description="internship, full_time, contract"),
    country: Optional[str] = Query(None, description="Country filter"),
    workplace_type: Optional[str] = Query(None, description="remote, hybrid, onsite"),
    skill: Optional[str] = Query(None, description="Filter by required skill"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[JobResponse]]:
    filters = {
        "opportunity_type": opportunity_type,
        "country": country,
        "workplace_type": workplace_type,
        "skill": skill,
        "student_skills": ["Python", "Machine Learning"],
    }
    jobs = search_jobs(filters=filters, authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=jobs,
        error=None,
        meta={"total": len(jobs)},
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/jobs/{job_id}",
    response_model=StandardEnvelope[JobResponse],
    summary="Get Job Opportunity Details",
)
def get_job(
    job_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[JobResponse]:
    job = get_job_by_id(job_id=job_id, authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=job,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/jobs",
    response_model=StandardEnvelope[JobResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create New Job Opportunity",
    description="Restricted to verified recruiters and administrators.",
)
def post_job(
    job_data: JobCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[JobResponse]:
    new_job = create_job(job_data=job_data, creator=current_user)
    return StandardEnvelope(
        status="success",
        data=new_job,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/jobs/{job_id}/applications",
    response_model=StandardEnvelope[JobApplicationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Application to Opportunity",
    description="Submits an application to an active job. Rejects duplicate submissions with HTTP 409.",
)
def apply_to_job(
    job_id: str,
    application_data: JobApplicationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[JobApplicationResponse]:
    application = submit_job_application(
        job_id=job_id,
        application_data=application_data,
        applicant=current_user,
    )
    return StandardEnvelope(
        status="success",
        data=application,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/me/applications",
    response_model=StandardEnvelope[List[JobApplicationResponse]],
    summary="Get My Submitted Job Applications",
)
def list_my_applications(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[JobApplicationResponse]]:
    apps = get_student_applications(applicant=current_user)
    return StandardEnvelope(
        status="success",
        data=apps,
        error=None,
        meta={"total": len(apps)},
        timestamp=datetime.now(timezone.utc),
    )
