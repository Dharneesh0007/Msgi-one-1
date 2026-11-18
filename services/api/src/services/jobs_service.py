"""
MSGI One — CareerBridge Domain Service
Implements: Opportunity discovery, deterministic skill-overlap calculation,
            transactional application submission, and duplicate prevention.
Provides Phase 3 Tool Contracts: search_jobs, evaluate_skill_overlap
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from src.core.dependencies import AuthenticatedUser
from src.schemas.business import (
    JobCreateRequest,
    JobResponse,
    JobApplicationRequest,
    JobApplicationResponse,
    SkillOverlapResult,
)

# In-memory development store for CareerBridge
_JOBS_STORE: List[Dict[str, Any]] = [
    {
        "id": "job-ai-intern-001",
        "creator_id": "user-recruiter-rakuten",
        "title": "Machine Learning Engineer — Platform Intern",
        "company": "Rakuten Symphony",
        "location": "Tokyo, Japan (Hybrid)",
        "country": "Japan",
        "opportunity_type": "internship",
        "workplace_type": "hybrid",
        "description": "Join the Core AI platform team building LLM orchestration and automated model deployment pipelines.",
        "requirements": ["Enrolled in Computer Science or IT", "Proficiency in Python and Linux"],
        "required_skills": ["Python", "Machine Learning", "PyTorch", "FastAPI"],
        "application_deadline": datetime.now(timezone.utc) + timedelta(days=30),
        "is_active": True,
        "is_verified_listing": True,
        "alumni_referral_available": True,
        "alumni_count_at_company": 14,
        "created_at": datetime.now(timezone.utc) - timedelta(days=2),
    },
    {
        "id": "job-cloud-solutions-002",
        "creator_id": "user-recruiter-msft",
        "title": "Cloud Solutions Architect",
        "company": "Microsoft",
        "location": "Bengaluru, India (Hybrid)",
        "country": "India",
        "opportunity_type": "full_time",
        "workplace_type": "hybrid",
        "description": "Architect enterprise cloud landing zones and generative AI deployments on Azure.",
        "requirements": ["B.Tech graduation by 2025/2026", "Cloud networking experience"],
        "required_skills": ["Cloud Architecture", "Azure", "Python", "Kubernetes"],
        "application_deadline": datetime.now(timezone.utc) + timedelta(days=45),
        "is_active": True,
        "is_verified_listing": True,
        "alumni_referral_available": True,
        "alumni_count_at_company": 28,
        "created_at": datetime.now(timezone.utc) - timedelta(days=4),
    },
    {
        "id": "job-robotics-intern-003",
        "creator_id": "user-recruiter-stealth",
        "title": "Autonomous Robotics Perception Intern",
        "company": "Stealth Robotics",
        "location": "San Francisco, USA (On-site)",
        "country": "United States",
        "opportunity_type": "internship",
        "workplace_type": "onsite",
        "description": "Develop visual odometry and lidar feature extraction pipelines for field robots.",
        "requirements": ["Strong C++ and Python fundamentals", "Experience with ROS 2"],
        "required_skills": ["ROS 2", "Embedded C++", "Computer Vision", "Python"],
        "application_deadline": datetime.now(timezone.utc) + timedelta(days=15),
        "is_active": True,
        "is_verified_listing": True,
        "alumni_referral_available": True,
        "alumni_count_at_company": 3,
        "created_at": datetime.now(timezone.utc) - timedelta(days=1),
    },
    {
        "id": "job-expired-test-004",
        "creator_id": "user-recruiter-expired",
        "title": "Legacy Systems Intern (Expired)",
        "company": "Legacy Corp",
        "location": "Tokyo, Japan",
        "country": "Japan",
        "opportunity_type": "internship",
        "workplace_type": "onsite",
        "description": "Expired posting for filter testing.",
        "requirements": ["None"],
        "required_skills": ["Cobol"],
        "application_deadline": datetime.now(timezone.utc) - timedelta(days=5),  # Expired
        "is_active": True,
        "is_verified_listing": True,
        "alumni_referral_available": False,
        "alumni_count_at_company": 0,
        "created_at": datetime.now(timezone.utc) - timedelta(days=30),
    },
]

# In-memory store for applications: key is (job_id, applicant_id) to enforce uniqueness
_JOB_APPLICATIONS_STORE: Dict[str, Dict[str, Any]] = {}


def evaluate_skill_overlap(
    required_skills: List[str],
    student_skills: List[str],
) -> SkillOverlapResult:
    """
    Deterministic skill-overlap evaluator (Phase 3 Tool Contract).
    Calculates exact percentage and matched/missing skill partitions.
    """
    if not required_skills:
        return SkillOverlapResult(match_percentage=100, matched_skills=[], missing_skills=[])

    req_set = {s.strip().lower() for s in required_skills}
    student_set = {s.strip().lower() for s in student_skills}

    matched_lower = req_set.intersection(student_set)
    matched_skills = [s for s in required_skills if s.strip().lower() in matched_lower]
    missing_skills = [s for s in required_skills if s.strip().lower() not in matched_lower]

    match_percentage = int((len(matched_skills) / len(required_skills)) * 100)

    return SkillOverlapResult(
        match_percentage=match_percentage,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )


def search_jobs(
    filters: Dict[str, Any],
    authenticated_user: AuthenticatedUser,
) -> List[JobResponse]:
    """
    Phase 3 Tool Contract & Core Domain Service.
    Retrieves active, non-expired career opportunities with skill match analysis.
    """
    opportunity_type = filters.get("opportunity_type", "").strip().lower()
    country = filters.get("country", "").strip().lower()
    workplace_type = filters.get("workplace_type", "").strip().lower()
    skill = filters.get("skill", "").strip().lower()
    student_skills = filters.get("student_skills", ["Python", "Machine Learning"])

    now = datetime.now(timezone.utc)
    results: List[JobResponse] = []

    for job in _JOBS_STORE:
        # Exclude inactive or expired jobs
        if not job.get("is_active", True):
            continue

        deadline = job.get("application_deadline")
        if deadline and deadline < now:
            continue

        # Filters
        if opportunity_type and opportunity_type != job.get("opportunity_type", "").lower():
            continue

        if country and country not in job.get("country", "").lower():
            continue

        if workplace_type and workplace_type != job.get("workplace_type", "").lower():
            continue

        if skill:
            has_skill = any(skill in s.lower() for s in job.get("required_skills", []))
            if not has_skill:
                continue

        # Calculate skill overlap for authenticated student
        skill_analysis = evaluate_skill_overlap(job.get("required_skills", []), student_skills)

        results.append(
            JobResponse(
                id=job["id"],
                title=job["title"],
                company=job["company"],
                location=job["location"],
                country=job["country"],
                opportunity_type=job["opportunity_type"],
                workplace_type=job["workplace_type"],
                description=job["description"],
                requirements=job["requirements"],
                required_skills=job["required_skills"],
                application_deadline=job.get("application_deadline"),
                is_active=job["is_active"],
                is_verified_listing=job["is_verified_listing"],
                alumni_referral_available=job.get("alumni_referral_available", False),
                alumni_count_at_company=job.get("alumni_count_at_company", 0),
                skill_overlap=skill_analysis,
                created_at=job["created_at"],
            )
        )

    return results


def get_job_by_id(job_id: str, authenticated_user: AuthenticatedUser) -> JobResponse:
    """Retrieve details for a single job listing."""
    job = next((j for j in _JOBS_STORE if j["id"] == job_id), None)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ENTITY_NOT_FOUND", "message": f"Job with ID '{job_id}' was not found."},
        )

    student_skills = ["Python", "Machine Learning"]
    skill_analysis = evaluate_skill_overlap(job.get("required_skills", []), student_skills)

    return JobResponse(
        id=job["id"],
        title=job["title"],
        company=job["company"],
        location=job["location"],
        country=job["country"],
        opportunity_type=job["opportunity_type"],
        workplace_type=job["workplace_type"],
        description=job["description"],
        requirements=job["requirements"],
        required_skills=job["required_skills"],
        application_deadline=job.get("application_deadline"),
        is_active=job["is_active"],
        is_verified_listing=job["is_verified_listing"],
        alumni_referral_available=job.get("alumni_referral_available", False),
        alumni_count_at_company=job.get("alumni_count_at_company", 0),
        skill_overlap=skill_analysis,
        created_at=job["created_at"],
    )


def create_job(job_data: JobCreateRequest, creator: AuthenticatedUser) -> JobResponse:
    """Create a new institutional job opportunity. Requires recruiter or admin role."""
    if not any(r in ["recruiter", "admin"] for r in creator.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Only verified recruiters or administrators can post jobs."},
        )

    new_id = f"job-custom-{len(_JOBS_STORE) + 1}"
    job_record = {
        "id": new_id,
        "creator_id": creator.id,
        "title": job_data.title,
        "company": job_data.company,
        "location": job_data.location,
        "country": job_data.country,
        "opportunity_type": job_data.opportunity_type,
        "workplace_type": job_data.workplace_type,
        "description": job_data.description,
        "requirements": job_data.requirements,
        "required_skills": job_data.required_skills,
        "application_deadline": job_data.application_deadline,
        "is_active": True,
        "is_verified_listing": "admin" in creator.roles or creator.is_verified,
        "alumni_referral_available": True,
        "alumni_count_at_company": 1,
        "created_at": datetime.now(timezone.utc),
    }

    _JOBS_STORE.append(job_record)
    return get_job_by_id(new_id, creator)


def submit_job_application(
    job_id: str,
    application_data: JobApplicationRequest,
    applicant: AuthenticatedUser,
) -> JobApplicationResponse:
    """
    Submits an application to an active job opportunity.
    Enforces transactional duplicate prevention UNIQUE(job_id, applicant_id).
    """
    # Verify job exists and is active
    job = next((j for j in _JOBS_STORE if j["id"] == job_id), None)
    if not job or not job.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job with ID '{job_id}' is not available."},
        )

    # Check expiration
    if job.get("application_deadline") and job["application_deadline"] < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DEADLINE_PASSED", "message": "The application deadline for this position has passed."},
        )

    # Duplicate check: UNIQUE(job_id, applicant_id)
    unique_key = f"{job_id}:{applicant.id}"
    if unique_key in _JOB_APPLICATIONS_STORE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_APPLICATION", "message": "You have already submitted an application for this position."},
        )

    app_id = f"app-{len(_JOB_APPLICATIONS_STORE) + 1}"
    record = {
        "id": app_id,
        "job_id": job_id,
        "job_title": job["title"],
        "company": job["company"],
        "applicant_id": applicant.id,
        "status": "submitted",
        "resume_url": application_data.resume_url,
        "cover_note": application_data.cover_note,
        "submitted_at": datetime.now(timezone.utc),
    }

    _JOB_APPLICATIONS_STORE[unique_key] = record

    return JobApplicationResponse(
        id=record["id"],
        job_id=record["job_id"],
        job_title=record["job_title"],
        company=record["company"],
        applicant_id=record["applicant_id"],
        status=record["status"],
        cover_note=record.get("cover_note"),
        submitted_at=record["submitted_at"],
    )


def get_student_applications(applicant: AuthenticatedUser) -> List[JobApplicationResponse]:
    """Retrieve all applications submitted by the current authenticated user."""
    user_apps = [
        JobApplicationResponse(
            id=app["id"],
            job_id=app["job_id"],
            job_title=app["job_title"],
            company=app["company"],
            applicant_id=app["applicant_id"],
            status=app["status"],
            cover_note=app.get("cover_note"),
            submitted_at=app["submitted_at"],
        )
        for app in _JOB_APPLICATIONS_STORE.values()
        if app["applicant_id"] == applicant.id
    ]
    return user_apps
