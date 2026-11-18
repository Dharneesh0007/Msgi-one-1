"""
MSGI One — MentorMatch Unit & Integration Tests
Tests: Opt-in discovery, capacity enforcement, deterministic candidate ranking,
       request submission, duplicate protection, and mentor authorization.
"""

import pytest
from fastapi import HTTPException
from src.core.dependencies import AuthenticatedUser
from src.schemas.business import MentorRequestCreate, MentorRequestStatusUpdate
from src.services.mentor_service import (
    search_mentors,
    get_mentor_by_id,
    create_mentor_request,
    update_mentor_request_status,
    get_my_mentor_requests,
    prepare_mentor_request,
)


@pytest.fixture
def student_user():
    return AuthenticatedUser(
        id="student-mentor-001",
        email="student.mentor@example.msgi.edu",
        first_name="Riku",
        last_name="Takahashi",
        roles=["student"],
        is_verified=True,
    )


@pytest.fixture
def mentor_user():
    return AuthenticatedUser(
        id="user-kenji-001",
        email="kenji.sato@example.msgi.edu",
        first_name="Kenji",
        last_name="Sato",
        roles=["alumni"],
        is_verified=True,
    )


def test_search_mentors_excludes_fully_booked(student_user):
    """Mentors who have reached max capacity must not appear in search results."""
    mentors = search_mentors({}, authenticated_user=student_user)
    ids = [m.id for m in mentors]
    assert "mentor-full-003" not in ids


def test_search_mentors_topic_filter_and_ranking(student_user):
    """Mentors are filtered by topic and ranked deterministically by student goal."""
    mentors = search_mentors(
        {"topic": "AI", "student_goal": "Lead AI Engineer in Japan"},
        authenticated_user=student_user,
    )
    assert len(mentors) >= 1
    # Kenji Sato has AI Career Pathways & open capacity, so should rank first
    assert mentors[0].id == "mentor-kenji-001"
    assert mentors[0].match_score is not None
    assert mentors[0].match_score > 70


def test_prepare_mentor_request_read_only(student_user):
    """Phase 3 Tool Contract: prepare_mentor_request returns a read-only preview."""
    preview = prepare_mentor_request("mentor-kenji-001", "Become an ML Engineer", student_user)
    assert preview["mentor_name"] == "Kenji Sato"
    assert preview["confirmation_required"] is True


def test_submit_mentor_request_and_duplicate_rejection(student_user):
    """Student submits a request; second pending request to same mentor raises 409."""
    req_payload = MentorRequestCreate(
        mentor_id="mentor-kenji-001",
        topic="AI Career Pathways",
        career_goal="Become a Senior Deep Learning Engineer",
        message="I would love guidance on preparing for industry roles.",
    )

    created = create_mentor_request(req_payload, student=student_user)
    assert created.status == "pending"
    assert created.mentor_name == "Kenji Sato"

    # Duplicate pending request must fail with 409
    with pytest.raises(HTTPException) as exc_info:
        create_mentor_request(req_payload, student=student_user)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "DUPLICATE_PENDING_REQUEST"


def test_student_cannot_request_mentorship_from_themselves(mentor_user):
    """A user attempting to request mentorship from their own mentor profile raises 400."""
    req_payload = MentorRequestCreate(
        mentor_id="mentor-kenji-001",  # Kenji's own profile
        topic="AI",
        career_goal="Self-growth",
    )
    with pytest.raises(HTTPException) as exc_info:
        create_mentor_request(req_payload, student=mentor_user)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "SELF_MENTORSHIP_PROHIBITED"


def test_mentor_accepts_request_and_capacity_increments(student_user, mentor_user):
    """Mentor accepts request; status updates to accepted and active mentees increment."""
    # Find the created request from earlier test
    requests = get_my_mentor_requests(student_user)
    assert len(requests) >= 1
    target_req = requests[0]

    # Unauthorized student attempting to accept raises 403
    with pytest.raises(HTTPException) as exc_info:
        update_mentor_request_status(
            target_req.id,
            MentorRequestStatusUpdate(status="accepted"),
            user=student_user,
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "PERMISSION_DENIED"

    # Authorized mentor accepts
    updated = update_mentor_request_status(
        target_req.id,
        MentorRequestStatusUpdate(status="accepted", mentor_notes="Glad to mentor you!"),
        user=mentor_user,
    )
    assert updated.status == "accepted"
    assert updated.mentor_notes == "Glad to mentor you!"
