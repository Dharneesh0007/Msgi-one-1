"""
MSGI One — MentorMatch Domain Service
Implements: Opt-in discovery, deterministic candidate ranking, capacity enforcement,
            lifecycle state transitions (pending -> accepted/rejected/completed/cancelled).
Provides Phase 3 Tool Contracts: search_mentors, score_mentor_candidates, prepare_mentor_request
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from src.core.dependencies import AuthenticatedUser
from src.schemas.business import (
    MentorProfileResponse,
    MentorRequestCreate,
    MentorRequestStatusUpdate,
    MentorRequestResponse,
)

# In-memory development store for mentors
_MENTORS_STORE: List[Dict[str, Any]] = [
    {
        "id": "mentor-kenji-001",
        "user_id": "user-kenji-001",
        "db_id": "8df49472-e52b-4ae2-8edd-6e61a32b3f05",
        "db_user_id": "53e6a936-b9a4-431e-aedc-3bf90dc63c3c",
        "full_name": "Kenji Sato",
        "headline": "Staff AI Engineer at Rakuten Symphony",
        "current_company": "Rakuten Symphony",
        "current_title": "Staff AI Engineer",
        "country": "Japan",
        "advisory_topics": ["AI Career Pathways", "Transitioning to Industry in Japan", "Graduate Studies", "Machine Learning"],
        "is_accepting_requests": True,
        "max_active_mentees": 3,
        "current_active_mentees": 1,
    },
    {
        "id": "mentor-ananya-002",
        "user_id": "user-ananya-002",
        "db_id": "f5e5d95b-9bdb-4ce7-8045-2640dcaa714b",
        "db_user_id": "2003cfcc-0883-4b9b-99f3-21d35769ac78",
        "full_name": "Ananya Sharma",
        "headline": "Senior Product Manager at Microsoft",
        "current_company": "Microsoft",
        "current_title": "Senior Product Manager",
        "country": "India",
        "advisory_topics": ["Product Management", "Enterprise Cloud Strategy", "Resume Review"],
        "is_accepting_requests": True,
        "max_active_mentees": 2,
        "current_active_mentees": 0,
    },
    {
        "id": "mentor-full-003",
        "user_id": "user-full-003",
        "full_name": "Tatsuya Mori",
        "headline": "VP of Engineering at CyberSecurity Corp",
        "current_company": "CyberSecurity Corp",
        "current_title": "VP Engineering",
        "country": "Japan",
        "advisory_topics": ["Security Architecture", "Leadership"],
        "is_accepting_requests": True,
        "max_active_mentees": 2,
        "current_active_mentees": 2,  # Fully booked
    },
]

# In-memory store for mentor requests: key is request_id
_MENTOR_REQUESTS_STORE: Dict[str, Dict[str, Any]] = {}


def score_mentor_candidates(
    mentors: List[Dict[str, Any]],
    student_goal: str,
) -> List[Dict[str, Any]]:
    """
    Deterministic mentor scoring function (Phase 3 Tool Contract).
    Calculates match score out of 100 based on keyword overlap with advisory topics.
    """
    goal_words = set(student_goal.lower().split())
    ranked = []

    for m in mentors:
        score = 60  # Base institutional alumni match score
        topics_str = " ".join(m.get("advisory_topics", [])).lower()

        # Bonus for topic match
        for word in goal_words:
            if len(word) > 3 and word in topics_str:
                score += 15

        # Bonus if available capacity > 1
        available = m.get("max_active_mentees", 3) - m.get("current_active_mentees", 0)
        if available > 1:
            score += 10

        score = min(99, max(50, score))
        m_copy = dict(m)
        m_copy["match_score"] = score
        ranked.append(m_copy)

    # Sort descending by match score
    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked


def search_mentors(
    filters: Dict[str, Any],
    authenticated_user: AuthenticatedUser,
) -> List[MentorProfileResponse]:
    """
    Phase 3 Tool Contract & Core Domain Service.
    Retrieves verified alumni who have opted in to mentoring and have open capacity.
    """
    topic = (filters.get("topic") or "").strip().lower()
    country = (filters.get("country") or "").strip().lower()
    student_goal = filters.get("student_goal", "AI Engineer")

    # Only include mentors accepting requests with open slots
    available_mentors = [
        m for m in _MENTORS_STORE
        if m.get("is_accepting_requests", True)
        and (m.get("max_active_mentees", 3) - m.get("current_active_mentees", 0)) > 0
    ]

    # Filter by topic
    if topic:
        available_mentors = [
            m for m in available_mentors
            if any(topic in t.lower() for t in m.get("advisory_topics", []))
        ]

    # Filter by country
    if country:
        available_mentors = [
            m for m in available_mentors
            if country in m.get("country", "").lower()
        ]

    # Score and rank candidates
    ranked = score_mentor_candidates(available_mentors, student_goal)

    return [
        MentorProfileResponse(
            id=m["id"],
            user_id=m["user_id"],
            full_name=m["full_name"],
            headline=m["headline"],
            current_company=m["current_company"],
            current_title=m["current_title"],
            country=m["country"],
            advisory_topics=m["advisory_topics"],
            is_accepting_requests=m["is_accepting_requests"],
            max_active_mentees=m["max_active_mentees"],
            current_active_mentees=m["current_active_mentees"],
            available_slots=m["max_active_mentees"] - m["current_active_mentees"],
            match_score=m.get("match_score"),
        )
        for m in ranked
    ]


def get_mentor_by_id(mentor_id: str, authenticated_user: AuthenticatedUser) -> MentorProfileResponse:
    """Retrieve individual mentor profile."""
    m = next(
        (
            mentor for mentor in _MENTORS_STORE
            if mentor["id"] == mentor_id
            or mentor.get("db_id") == mentor_id
            or mentor.get("user_id") == mentor_id
            or mentor.get("db_user_id") == mentor_id
        ),
        None,
    )
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MENTOR_NOT_FOUND", "message": f"Mentor with ID '{mentor_id}' was not found."},
        )

    return MentorProfileResponse(
        id=m["id"],
        user_id=m["user_id"],
        full_name=m["full_name"],
        headline=m["headline"],
        current_company=m["current_company"],
        current_title=m["current_title"],
        country=m["country"],
        advisory_topics=m["advisory_topics"],
        is_accepting_requests=m["is_accepting_requests"],
        max_active_mentees=m["max_active_mentees"],
        current_active_mentees=m["current_active_mentees"],
        available_slots=m["max_active_mentees"] - m["current_active_mentees"],
        match_score=95,
    )


def prepare_mentor_request(
    mentor_id: str,
    goal: str,
    authenticated_user: AuthenticatedUser,
) -> Dict[str, Any]:
    """
    Phase 3 Tool Contract (Read-only preview).
    Prepares a draft mentorship request without executing it.
    """
    mentor = get_mentor_by_id(mentor_id, authenticated_user)
    return {
        "mentor_id": mentor.id,
        "mentor_name": mentor.full_name,
        "mentor_company": mentor.current_company,
        "student_name": f"{authenticated_user.first_name} {authenticated_user.last_name}",
        "proposed_goal": goal,
        "available_slots": mentor.available_slots,
        "confirmation_required": True,
    }


def create_mentor_request(
    request_data: MentorRequestCreate,
    student: AuthenticatedUser,
) -> MentorRequestResponse:
    """
    Submits a mentorship request after user confirmation.
    Enforces mentor capacity and prevents duplicate pending requests.
    """
    mentor = next(
        (
            m for m in _MENTORS_STORE
            if m["id"] == request_data.mentor_id
            or m.get("db_id") == request_data.mentor_id
            or m.get("user_id") == request_data.mentor_id
            or m.get("db_user_id") == request_data.mentor_id
        ),
        None,
    )
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MENTOR_NOT_FOUND", "message": "The selected mentor could not be found."},
        )

    # Check capacity
    if mentor["current_active_mentees"] >= mentor["max_active_mentees"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MENTOR_CAPACITY_EXCEEDED", "message": "This mentor has reached their maximum active mentee capacity."},
        )

    # Prevent student from requesting mentorship from themselves
    if mentor["user_id"] == student.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_MENTORSHIP_PROHIBITED", "message": "You cannot request mentorship from yourself."},
        )

    # Check duplicate pending request
    for req in _MENTOR_REQUESTS_STORE.values():
        if req["mentor_id"] == mentor["id"] and req["student_id"] == student.id and req["status"] == "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DUPLICATE_PENDING_REQUEST", "message": "You already have a pending mentorship request with this mentor."},
            )

    req_id = f"req-{len(_MENTOR_REQUESTS_STORE) + 1}"
    now = datetime.now(timezone.utc)
    record = {
        "id": req_id,
        "mentor_id": mentor["id"],
        "mentor_user_id": mentor["user_id"],
        "mentor_name": mentor["full_name"],
        "mentor_company": mentor["current_company"],
        "student_id": student.id,
        "student_name": f"{student.first_name or 'Institutional'} {student.last_name or 'Student'}",
        "topic": request_data.topic,
        "career_goal": request_data.career_goal,
        "message": request_data.message,
        "status": "pending",
        "mentor_notes": None,
        "created_at": now,
        "updated_at": now,
    }

    _MENTOR_REQUESTS_STORE[req_id] = record

    return MentorRequestResponse(**record)


def update_mentor_request_status(
    request_id: str,
    status_update: MentorRequestStatusUpdate,
    user: AuthenticatedUser,
) -> MentorRequestResponse:
    """
    Updates mentorship request status.
    Enforces authorization: Only the assigned mentor can accept or reject.
    """
    req = _MENTOR_REQUESTS_STORE.get(request_id)
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REQUEST_NOT_FOUND", "message": f"Mentorship request '{request_id}' not found."},
        )

    new_status = status_update.status
    current_status = req["status"]

    # Student can only cancel their own pending request
    if user.id == req["student_id"]:
        if new_status != "cancelled":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "Students can only cancel their own mentorship requests."},
            )
        if current_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_TRANSITION", "message": f"Cannot cancel a request that is already '{current_status}'."},
            )
    # Mentor can accept or reject
    elif user.id == req["mentor_user_id"]:
        if current_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_TRANSITION", "message": f"Request has already been marked '{current_status}'."},
            )
        # If accepting, atomically increment mentor current_active_mentees
        if new_status == "accepted":
            mentor = next((m for m in _MENTORS_STORE if m["id"] == req["mentor_id"]), None)
            if mentor:
                if mentor["current_active_mentees"] >= mentor["max_active_mentees"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"code": "MENTOR_CAPACITY_EXCEEDED", "message": "You have reached your maximum mentee capacity."},
                    )
                mentor["current_active_mentees"] += 1
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "You are not authorized to modify this mentorship request."},
        )

    req["status"] = new_status
    if status_update.mentor_notes:
        req["mentor_notes"] = status_update.mentor_notes
    req["updated_at"] = datetime.now(timezone.utc)

    return MentorRequestResponse(**req)


def get_my_mentor_requests(user: AuthenticatedUser) -> List[MentorRequestResponse]:
    """Retrieve all requests where the user is either the student or the mentor."""
    user_requests = [
        MentorRequestResponse(**r)
        for r in _MENTOR_REQUESTS_STORE.values()
        if r["student_id"] == user.id or r["mentor_user_id"] == user.id
    ]
    return user_requests
