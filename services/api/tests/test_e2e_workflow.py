"""
MSGI One — End-to-End Integrated Business Workflow Test
Matches Section 14: Concrete Cross-Module Workflow
Student discovers alumni -> Requests mentorship -> Mentor accepts ->
Student discovers internship -> Submits application -> Registers for Webinar.
All modules share one canonical user identity and database.
"""

import pytest
from src.core.dependencies import AuthenticatedUser
from src.services.alumni_service import search_alumni
from src.services.mentor_service import (
    search_mentors,
    create_mentor_request,
    get_my_mentor_requests,
    update_mentor_request_status,
)
from src.services.jobs_service import (
    search_jobs,
    submit_job_application,
    get_student_applications,
)
from src.services.events_service import (
    search_events,
    register_for_event,
    get_user_event_registrations,
    check_event_capacity,
)
from src.schemas.business import (
    MentorRequestCreate,
    MentorRequestStatusUpdate,
    JobApplicationRequest,
)


def test_complete_end_to_end_student_journey():
    """
    Executes the 18-step concrete user scenario across all P0 modules.
    """
    # 1. Student identity
    student = AuthenticatedUser(
        id="student-journey-uuid-999",
        email="journey.student@example.msgi.edu",
        first_name="Ren",
        last_name="Kobayashi",
        roles=["student"],
        is_verified=True,
    )

    # 2. Mentor identity (Alumni)
    mentor = AuthenticatedUser(
        id="user-kenji-001",
        email="kenji.sato@example.msgi.edu",
        first_name="Kenji",
        last_name="Sato",
        roles=["alumni"],
        is_verified=True,
    )

    # STEP 2 & 3: Student searches verified AI alumni in Japan
    alumni_results = search_alumni(
        filters={"industry": "Artificial Intelligence", "country": "Japan", "verified_only": True},
        authenticated_user=student,
    )
    assert alumni_results["total"] >= 1
    found_kenji = next((a for a in alumni_results["items"] if a.full_name == "Kenji Sato"), None)
    assert found_kenji is not None
    assert found_kenji.mentor_opt_in is True

    # STEP 4 & 5: Student discovers mentors
    mentors = search_mentors(
        filters={"topic": "AI", "country": "Japan", "student_goal": "Senior AI Engineer"},
        authenticated_user=student,
    )
    assert len(mentors) >= 1
    target_mentor = next(m for m in mentors if m.user_id == mentor.id)
    assert target_mentor.available_slots > 0

    # STEP 6 & 7: Student submits mentorship request
    req_payload = MentorRequestCreate(
        mentor_id=target_mentor.id,
        topic="AI Career Pathways",
        career_goal="Become a Machine Learning Engineer in Tokyo",
        message="I would appreciate advice on portfolio preparation.",
    )
    request_res = create_mentor_request(req_payload, student=student)
    assert request_res.status == "pending"
    assert request_res.student_id == student.id
    request_id = request_res.id

    # STEP 8 & 9: Mentor views and accepts request
    mentor_inbox = get_my_mentor_requests(mentor)
    assert any(r.id == request_id for r in mentor_inbox)

    accept_payload = MentorRequestStatusUpdate(
        status="accepted",
        mentor_notes="Looking forward to our first session!",
    )
    updated_req = update_mentor_request_status(request_id, accept_payload, user=mentor)
    assert updated_req.status == "accepted"

    # STEP 10: Student verifies status is accepted
    student_requests = get_my_mentor_requests(student)
    accepted_by_student = next(r for r in student_requests if r.id == request_id)
    assert accepted_by_student.status == "accepted"
    assert accepted_by_student.mentor_notes == "Looking forward to our first session!"

    # STEP 11 & 12: Student searches AI internships and checks skill overlap
    jobs = search_jobs(
        filters={"opportunity_type": "internship", "country": "Japan"},
        authenticated_user=student,
    )
    assert len(jobs) >= 1
    target_job = next(j for j in jobs if "Machine Learning" in j.title)
    assert target_job.skill_overlap.match_percentage >= 50
    assert "Python" in target_job.skill_overlap.matched_skills

    # STEP 13 & 14: Student submits internal application
    app_payload = JobApplicationRequest(cover_note="Applying with strong Python and ML foundations.")
    app_res = submit_job_application(target_job.id, app_payload, applicant=student)
    assert app_res.status == "submitted"

    # Verify application persisted
    student_apps = get_student_applications(student)
    assert any(a.job_id == target_job.id for a in student_apps)

    # STEP 15 & 16: Student registers for upcoming career webinar
    events = search_events({"event_type": "webinar"}, authenticated_user=student)
    assert len(events) >= 1
    target_event = next(e for e in events if "Generative AI" in e.title)
    initial_seats = target_event.available_seats

    reg_res = register_for_event(target_event.id, user=student)
    assert reg_res.status == "confirmed"
    assert reg_res.ticket_code.startswith("TICK-")

    # STEP 17 & 18: Capacity updated & records retrievable after simulation
    updated_cap = check_event_capacity(target_event.id)
    assert updated_cap["available_seats"] == initial_seats - 1

    my_events = get_user_event_registrations(student)
    assert any(e.event_id == target_event.id for e in my_events)
