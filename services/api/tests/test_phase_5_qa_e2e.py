"""
MSGI One — Phase 5 End-to-End Quality Assurance & Multi-User Integration Suite
Validates the 8 multi-user lifecycles from supabase/seed/qa_workflow_cases.jsonl,
exercises the 14 synthetic personas from supabase/seed/csv/qa_test_users.csv,
and verifies a seamless 12-module student journey via direct service contracts.
Principles: Pressman Multi-Level Testing & Sommerville Verification.
"""

import json
import csv
from pathlib import Path
import pytest
from fastapi import HTTPException

from src.core.dependencies import AuthenticatedUser
from src.services.notifications_service import (
    create_notification,
    get_my_notifications,
    mark_notification_as_read,
    _NOTIFICATIONS_STORE,
)
from src.services.learning_service import (
    list_learning_resources,
    enroll_in_course,
    update_learning_progress,
    get_my_learning,
)
from src.services.community_service import (
    list_communities,
    join_community,
    update_membership_status,
    get_my_communities,
)
from src.services.extended_service import (
    list_projects,
    join_project_request,
    list_startups,
    create_startup_connection,
    list_impact_programmes,
    register_volunteer_interest,
)
from src.services.mentor_service import (
    search_mentors,
    create_mentor_request,
    update_mentor_request_status,
)
from src.schemas.business import (
    MentorRequestCreate,
    MentorRequestStatusUpdate,
    JobApplicationRequest,
)
from src.services.jobs_service import (
    search_jobs,
    submit_job_application,
)
from src.services.events_service import (
    search_events,
    register_for_event,
)
from src.services.alumni_service import (
    search_alumni,
    get_alumni_by_id,
)
from src.services.global_service import (
    get_aggregated_locations,
)
from src.services.admin_service import (
    list_pending_verifications,
    get_admin_audit_logs,
)
from src.routers.users import (
    get_my_profile,
    delete_user_account,
)
from src.ai.graph import run_command_centre


_SEED_DIR = Path(__file__).resolve().parent.parent.parent.parent / "supabase" / "seed"
if not _SEED_DIR.exists():
    _SEED_DIR = Path(__file__).resolve().parent.parent.parent / "supabase" / "seed"


# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------

@pytest.fixture
def student_user():
    return AuthenticatedUser(
        id="user-student-001",
        email="alex.rivera@example.msgi.edu",
        first_name="Alex",
        last_name="Rivera",
        roles=["student"],
        is_verified=True,
    )


@pytest.fixture
def second_student_user():
    return AuthenticatedUser(
        id="user-student-002",
        email="jordan.smith@example.msgi.edu",
        first_name="Jordan",
        last_name="Smith",
        roles=["student"],
        is_verified=True,
    )


@pytest.fixture
def mentor_alumni_user():
    return AuthenticatedUser(
        id="user-kenji-001",
        email="kenji.sato@example.msgi.edu",
        first_name="Kenji",
        last_name="Sato",
        roles=["alumni"],
        is_verified=True,
    )


@pytest.fixture
def founder_alumni_user():
    return AuthenticatedUser(
        id="user-ananya-002",
        email="ananya.sharma@example.msgi.edu",
        first_name="Ananya",
        last_name="Sharma",
        roles=["alumni"],
        is_verified=True,
    )


@pytest.fixture
def admin_user():
    return AuthenticatedUser(
        id="user-admin-001",
        email="sarah.jenkins@example.msgi.edu",
        first_name="Sarah",
        last_name="Jenkins",
        roles=["admin"],
        is_verified=True,
    )


# -----------------------------------------------------------------------------
# 1. QA DATASET FIXTURES INTEGRITY
# -----------------------------------------------------------------------------

def test_qa_dataset_fixtures_integrity():
    """Verify that all Phase 5 QA datasets exist and contain expected row counts."""
    users_csv = _SEED_DIR / "csv" / "qa_test_users.csv"
    assert users_csv.exists(), "qa_test_users.csv must exist"
    with open(users_csv, mode="r", encoding="utf-8") as f:
        users = list(csv.DictReader(f))
    assert len(users) == 14, f"Expected 14 test users, found {len(users)}"

    perms_csv = _SEED_DIR / "csv" / "qa_role_permissions.csv"
    assert perms_csv.exists(), "qa_role_permissions.csv must exist"
    with open(perms_csv, mode="r", encoding="utf-8") as f:
        perms = list(csv.DictReader(f))
    assert len(perms) >= 24, f"Expected >= 24 permission definitions, found {len(perms)}"

    wf_jsonl = _SEED_DIR / "qa_workflow_cases.jsonl"
    assert wf_jsonl.exists(), "qa_workflow_cases.jsonl must exist"
    with open(wf_jsonl, mode="r", encoding="utf-8") as f:
        wf_cases = [json.loads(line) for line in f if line.strip()]
    assert len(wf_cases) == 8, f"Expected 8 workflow cases, found {len(wf_cases)}"

    sec_jsonl = _SEED_DIR / "qa_security_cases.jsonl"
    assert sec_jsonl.exists(), "qa_security_cases.jsonl must exist"
    with open(sec_jsonl, mode="r", encoding="utf-8") as f:
        sec_cases = [json.loads(line) for line in f if line.strip()]
    assert len(sec_cases) == 8, f"Expected 8 security cases, found {len(sec_cases)}"


# -----------------------------------------------------------------------------
# 2. E2E WORKFLOW CASES (WF-001 to WF-008)
# -----------------------------------------------------------------------------

def test_wf001_mentorship_lifecycle(student_user):
    """WF-001: Mentorship connection lifecycle (Request -> Notify -> Accept -> Active)."""
    mentors = search_mentors(filters={}, authenticated_user=student_user)
    assert len(mentors) >= 1
    target_mentor = mentors[0]

    target_mentor_user = AuthenticatedUser(
        id=target_mentor.user_id,
        email=f"{target_mentor.full_name.lower().replace(' ', '.')}@example.msgi.edu",
        first_name=target_mentor.full_name.split()[0],
        last_name=target_mentor.full_name.split()[-1],
        roles=["alumni"],
        is_verified=True,
    )

    req = create_mentor_request(
        request_data=MentorRequestCreate(
            mentor_id=target_mentor.id,
            topic="Cloud Architecture",
            career_goal="Cloud Architecture & Kubernetes",
            message="Seeking guidance on distributed systems",
        ),
        student=student_user,
    )
    assert req.id.startswith("req-")
    assert req.status == "pending"

    notif = create_notification(
        user_id=target_mentor_user.id,
        event_type="mentorship_requested",
        entity_id=req.id,
        title="New Mentorship Request",
        message=f"{student_user.first_name} requested mentorship in Cloud Architecture.",
    )
    assert notif.id.startswith("notif-")

    mentor_notifs = get_my_notifications(user=target_mentor_user)
    assert any(n.id == notif.id for n in mentor_notifs)

    updated_req = update_mentor_request_status(
        request_id=req.id,
        status_update=MentorRequestStatusUpdate(status="accepted"),
        user=target_mentor_user,
    )
    assert updated_req.status == "accepted"


def test_wf002_job_application_lifecycle(student_user):
    """WF-002: Job discovery and application submission."""
    jobs = search_jobs(filters={}, authenticated_user=student_user)
    assert len(jobs) >= 1
    target_job = jobs[0]

    app_res = submit_job_application(
        job_id=target_job.id,
        application_data=JobApplicationRequest(
            resume_url="https://example.msgi.edu/resumes/alex-rivera.pdf",
            cover_note="Passionate cloud engineering student",
        ),
        applicant=student_user,
    )
    assert app_res.id.startswith("app-")
    assert app_res.status in {"submitted", "pending", "received"}


def test_wf003_event_registration_lifecycle(second_student_user):
    """WF-003: Event discovery and attendee registration."""
    events = search_events(filters={}, authenticated_user=second_student_user)
    assert len(events) >= 1
    target_event = events[0]

    reg = register_for_event(
        event_id=target_event.id,
        user=second_student_user,
    )
    assert reg.status in {"confirmed", "registered"}


def test_wf004_learning_skill_gap_to_enrollment(student_user):
    """WF-004: Learning catalog query, enrollment, and progress update."""
    catalog = list_learning_resources()
    assert len(catalog) >= 1
    enrolled_ids = {e.resource_id for e in get_my_learning(student_user)}
    available = [r for r in catalog if r.resource_id not in enrolled_ids]
    assert len(available) >= 1
    resource = available[0]

    enrollment = enroll_in_course(
        resource_id=resource.resource_id,
        user=student_user,
    )
    assert enrollment.status == "enrolled"

    completed = update_learning_progress(
        enrollment_id=enrollment.id,
        progress_percentage=100,
        user=student_user,
    )
    assert completed.status == "completed"
    assert completed.progress_percentage == 100


def test_wf005_community_moderation_lifecycle(second_student_user, admin_user):
    """WF-005: Community discovery, private join request, and moderator approval."""
    from src.services.community_service import _COMMUNITIES_STORE
    private_comms = [c for c in _COMMUNITIES_STORE if c.get("is_private", False)]
    assert len(private_comms) >= 1
    target_comm = private_comms[0]

    membership = join_community(
        community_id=target_comm["id"],
        user=second_student_user,
    )
    assert membership.status == "pending"

    approved = update_membership_status(
        community_id=target_comm["id"],
        membership_id=membership.id,
        new_status="active",
        moderator=admin_user,
    )
    assert approved.status == "active"


def test_wf006_project_collaboration_team_formation(second_student_user):
    """WF-006: Collaboration project discovery and join request."""
    projects = list_projects(skill=None, user=second_student_user)
    assert len(projects) >= 1
    target_proj = projects[0]

    join_res = join_project_request(
        project_id=target_proj.id,
        user=second_student_user,
    )
    assert join_res.project_id == target_proj.id
    assert join_res.user_id == second_student_user.id


def test_wf007_startup_founder_inquiry(student_user):
    """WF-007: Startup discovery and founder connection inquiry."""
    startups = list_startups()
    assert len(startups) >= 1
    target_startup = startups[0]

    conn = create_startup_connection(
        startup_id=target_startup.id,
        intent="internship",
        message="Interested in joining your machine learning engineering team.",
        user=student_user,
    )
    assert conn.id.startswith("conn-")
    assert conn.status == "pending"


def test_wf008_social_impact_volunteering_pledge(student_user):
    """WF-008: Non-monetary impact volunteering pledge."""
    programmes = list_impact_programmes(user=student_user)
    assert len(programmes) >= 1
    target_prog = programmes[0]

    pledge = register_volunteer_interest(
        programme_id=target_prog.id,
        interest_note="Python Programming & Algorithm Tutoring - 10 hours",
        user=student_user,
    )
    assert pledge.id.startswith("vol-")


# -----------------------------------------------------------------------------
# 3. CONTINUOUS 12-MODULE STUDENT JOURNEY TEST
# -----------------------------------------------------------------------------

def test_continuous_12_module_student_journey():
    """
    Simulates a continuous end-to-end journey for student 'student-journey-uuid-999'
    across all 12 platform modules in sequence using direct domain services.
    """
    journey_user = AuthenticatedUser(
        id="student-journey-uuid-999",
        email="student.journey@example.msgi.edu",
        first_name="Journey",
        last_name="Student",
        roles=["student"],
        is_verified=True,
    )

    # Module 1: Identity & Profile
    profile_envelope = get_my_profile(current_user=journey_user)
    assert profile_envelope.status == "success"
    assert profile_envelope.data.id == journey_user.id

    # Module 2: Alumni Network
    alumni_res = search_alumni(filters={}, authenticated_user=journey_user)
    assert alumni_res["total"] >= 1

    # Module 3: CareerBridge Jobs
    jobs = search_jobs(filters={}, authenticated_user=journey_user)
    assert len(jobs) >= 1

    # Module 4: MentorMatch
    mentors = search_mentors(filters={}, authenticated_user=journey_user)
    assert len(mentors) >= 1

    # Module 5: Events & Reunions
    events = search_events(filters={}, authenticated_user=journey_user)
    assert len(events) >= 1

    # Module 6: Global Connect
    locations = get_aggregated_locations(authenticated_user=journey_user)
    assert len(locations) >= 1

    # Module 7: Learning & Upskilling
    resources = list_learning_resources()
    assert len(resources) >= 1

    # Module 8: Communities
    communities = list_communities(user=journey_user)
    assert len(communities) >= 1

    # Module 9: Institutional Verification (Non-admin student blocked)
    with pytest.raises(HTTPException) as exc_info:
        list_pending_verifications(admin=journey_user)
    assert exc_info.value.status_code == 403

    # Module 10: Admin & Audit (Non-admin student blocked)
    with pytest.raises(HTTPException) as exc_info:
        get_admin_audit_logs(admin=journey_user)
    assert exc_info.value.status_code == 403

    # Module 11: Collaborative Projects
    projects = list_projects(user=journey_user)
    assert len(projects) >= 1

    # Module 12: Startups & Social Impact
    startups = list_startups()
    assert len(startups) >= 1
    programmes = list_impact_programmes(user=journey_user)
    assert len(programmes) >= 1

    # Notifications Hub
    notifs = get_my_notifications(user=journey_user)
    assert isinstance(notifs, list)

    # AI Command Centre Dispatch
    ai_result = run_command_centre(
        prompt="Find mentors in cloud architecture",
        user=journey_user,
    )
    assert ai_result.get("status") in {"completed", "interrupted"}
    assert len(ai_result.get("final_summary", "")) > 0
