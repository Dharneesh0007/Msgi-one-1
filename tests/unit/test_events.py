"""
MSGI One — Events & Reunions Unit & Integration Tests
Tests: Event discovery, atomic capacity management, duplicate registration prevention,
       ticket generation, and cancellation.
"""

import pytest
from fastapi import HTTPException
from src.core.dependencies import AuthenticatedUser
from src.services.events_service import (
    search_events,
    get_event_by_id,
    check_event_capacity,
    prepare_event_registration,
    register_for_event,
    get_user_event_registrations,
    cancel_event_registration,
)


@pytest.fixture
def student_user():
    return AuthenticatedUser(
        id="student-events-001",
        email="student.events@example.msgi.edu",
        first_name="Hina",
        last_name="Amano",
        roles=["student"],
        is_verified=True,
    )


def test_list_published_events_with_capacity(student_user):
    """Listing events returns published events with accurate available seats."""
    events = search_events({}, authenticated_user=student_user)
    assert len(events) >= 2
    for event in events:
        assert event.is_published is True
        assert event.available_seats == event.max_capacity - event.current_registrations


def test_check_event_capacity_tool(student_user):
    """Phase 3 Tool Contract: check_event_capacity returns real-time seat availability."""
    cap = check_event_capacity("event-ai-webinar-002")
    assert cap["event_id"] == "event-ai-webinar-002"
    assert cap["available_seats"] == cap["max_capacity"] - cap["current_registrations"]
    assert cap["is_full"] is False


def test_register_for_event_and_duplicate_prevention(student_user):
    """Registering for an event generates a ticket; second attempt raises 409."""
    event_id = "event-ai-webinar-002"

    # Initial check
    initial_cap = check_event_capacity(event_id)["available_seats"]

    # 1. First registration succeeds
    reg = register_for_event(event_id, user=student_user)
    assert reg.event_id == event_id
    assert reg.status == "confirmed"
    assert reg.ticket_code.startswith("TICK-")

    # Verify capacity atomically decremented
    updated_cap = check_event_capacity(event_id)["available_seats"]
    assert updated_cap == initial_cap - 1

    # 2. Duplicate registration raises 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        register_for_event(event_id, user=student_user)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "DUPLICATE_REGISTRATION"


def test_cannot_register_for_fully_booked_event(student_user):
    """Attempting to register for an event with 0 available seats raises 400."""
    with pytest.raises(HTTPException) as exc_info:
        register_for_event("event-full-test-003", user=student_user)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "EVENT_CAPACITY_EXCEEDED"


def test_cancel_event_registration(student_user):
    """Cancelling a confirmed registration frees up a seat."""
    event_id = "event-ai-webinar-002"
    pre_cancel_cap = check_event_capacity(event_id)["available_seats"]

    cancel_res = cancel_event_registration(event_id, user=student_user)
    assert "cancelled" in cancel_res["message"]

    post_cancel_cap = check_event_capacity(event_id)["available_seats"]
    assert post_cancel_cap == pre_cancel_cap + 1
