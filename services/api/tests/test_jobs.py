"""
MSGI One — CareerBridge Unit & Integration Tests
Tests: Filter accuracy, expiration exclusion, skill overlap evaluation,
       recruiter RBAC, transactional application submission, and duplicate protection.
"""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException
from src.core.dependencies import AuthenticatedUser
from src.schemas.business import JobCreateRequest, JobApplicationRequest
from src.services.jobs_service import (
    search_jobs,
    get_job_by_id,
    create_job,
    submit_job_application,
    get_student_applications,
    evaluate_skill_overlap,
)


@pytest.fixture
def student_user():
    return AuthenticatedUser(
        id="student-career-001",
        email="student.career@example.msgi.edu",
        first_name="Mei",
        last_name="Kurosawa",
        roles=["student"],
        is_verified=True,
    )


@pytest.fixture
def recruiter_user():
    return AuthenticatedUser(
        id="recruiter-rakuten-001",
        email="recruiter.rakuten@example.msgi.edu",
        first_name="Haruto",
        last_name="Tanaka",
        roles=["recruiter"],
        is_verified=True,
    )


def test_evaluate_skill_overlap_calculation():
    """Deterministic skill match analysis must produce exact percentage and partitions."""
    req = ["Python", "PyTorch", "Docker", "FastAPI"]
    student = ["python", "fastapi", "kubernetes"]

    result = evaluate_skill_overlap(req, student)
    assert result.match_percentage == 50  # 2 out of 4
    assert "Python" in result.matched_skills
    assert "FastAPI" in result.matched_skills
    assert "PyTorch" in result.missing_skills
    assert "Docker" in result.missing_skills


def test_search_jobs_excludes_expired_postings(student_user):
    """Expired job listings must be filtered out automatically."""
    jobs = search_jobs({}, authenticated_user=student_user)
    job_ids = [j.id for j in jobs]
    assert "job-expired-test-004" not in job_ids


def test_search_jobs_with_internship_filter(student_user):
    """Filtering by opportunity_type 'internship' returns matching opportunities."""
    jobs = search_jobs({"opportunity_type": "internship"}, authenticated_user=student_user)
    assert len(jobs) >= 1
    for job in jobs:
        assert job.opportunity_type == "internship"
        assert job.skill_overlap is not None


def test_student_cannot_create_job_listing(student_user):
    """A student attempting to create a job listing must be rejected with 403."""
    job_req = JobCreateRequest(
        title="Unauthorized Job",
        company="Fake Corp",
        location="Tokyo",
        description="This posting should be blocked by RBAC.",
    )
    with pytest.raises(HTTPException) as exc_info:
        create_job(job_req, creator=student_user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "PERMISSION_DENIED"


def test_recruiter_can_create_job_listing(recruiter_user):
    """A verified recruiter can create an institutional job listing."""
    job_req = JobCreateRequest(
        title="AI Research Intern",
        company="Rakuten Symphony",
        location="Tokyo, Japan",
        country="Japan",
        opportunity_type="internship",
        description="Exciting AI research internship working on frontier LLM architectures.",
        required_skills=["Python", "PyTorch"],
    )
    created = create_job(job_req, creator=recruiter_user)
    assert created.title == "AI Research Intern"
    assert created.company == "Rakuten Symphony"
    assert created.is_active is True


def test_submit_job_application_and_duplicate_prevention(student_user):
    """Applying to an active job succeeds; duplicate application is rejected with 409."""
    app_req = JobApplicationRequest(cover_note="I am passionate about platform engineering.")

    # 1. First submission succeeds
    app_res = submit_job_application("job-ai-intern-001", app_req, applicant=student_user)
    assert app_res.job_id == "job-ai-intern-001"
    assert app_res.status == "submitted"

    # 2. Duplicate submission must raise 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        submit_job_application("job-ai-intern-001", app_req, applicant=student_user)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "DUPLICATE_APPLICATION"


def test_student_can_view_own_applications(student_user):
    """Student can retrieve their submitted applications."""
    apps = get_student_applications(applicant=student_user)
    assert len(apps) >= 1
    assert any(a.job_id == "job-ai-intern-001" for a in apps)
