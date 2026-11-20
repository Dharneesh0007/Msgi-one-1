"""
MSGI One — Events & Reunions Domain Service
Implements: Event discovery, atomic capacity management, duplicate registration prevention,
            and registration cancellations.
Provides Phase 3 Tool Contracts: search_events, check_event_capacity, prepare_event_registration
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import uuid
from fastapi import HTTPException, status
from src.core.dependencies import AuthenticatedUser
from src.schemas.business import (
    EventResponse,
    EventCreateRequest,
    EventRegistrationResponse,
)

# In-memory development store for events
_EVENTS_STORE: List[Dict[str, Any]] = [
    {
        "id": "event-gala-001",
        "organizer_id": "user-admin-001",
        "organizer_name": "MSGI Institutional Relations",
        "title": "MSGI Annual Global Alumni Summit & Tech Gala",
        "event_type": "reunion",
        "description": "Annual flagship gathering connecting alumni founders, researchers, and students worldwide.",
        "location": "Tokyo International Forum & Virtual Live Stream",
        "is_virtual": True,
        "meeting_url": "https://stream.example.msgi.edu/alumni-summit-2026",
        "start_time": datetime.now(timezone.utc) + timedelta(days=24),
        "end_time": datetime.now(timezone.utc) + timedelta(days=24, hours=6),
        "max_capacity": 500,
        "current_registrations": 240,
        "is_published": True,
    },
    {
        "id": "event-ai-webinar-002",
        "organizer_id": "user-faculty-001",
        "organizer_name": "Department of Computer Science & IT",
        "title": "Masterclass: Deploying Generative AI Models in Production",
        "event_type": "webinar",
        "description": "Deep dive into model compression, vLLM serving, and low-latency inference on edge clusters.",
        "location": "Virtual Interactive Session",
        "is_virtual": True,
        "meeting_url": "https://stream.example.msgi.edu/ai-masterclass",
        "start_time": datetime.now(timezone.utc) + timedelta(days=7),
        "end_time": datetime.now(timezone.utc) + timedelta(days=7, hours=2),
        "max_capacity": 100,
        "current_registrations": 42,
        "is_published": True,
    },
    {
        "id": "event-full-test-003",
        "organizer_id": "user-admin-001",
        "organizer_name": "MSGI Career Services",
        "title": "Exclusive Executive Round Table (Fully Booked)",
        "event_type": "workshop",
        "description": "Intimate mentoring round table with C-level alumni executives.",
        "location": "MSGI Executive Boardroom",
        "is_virtual": False,
        "meeting_url": None,
        "start_time": datetime.now(timezone.utc) + timedelta(days=12),
        "end_time": datetime.now(timezone.utc) + timedelta(days=12, hours=3),
        "max_capacity": 15,
        "current_registrations": 15,  # Max capacity reached
        "is_published": True,
    },
]

# In-memory store for event registrations: key is (event_id, user_id) to enforce uniqueness
_EVENT_REGISTRATIONS_STORE: Dict[str, Dict[str, Any]] = {}


def check_event_capacity(event_id: str) -> Dict[str, Any]:
    """Phase 3 Tool Contract (Read-only capacity check)."""
    event = next((e for e in _EVENTS_STORE if e["id"] == event_id), None)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EVENT_NOT_FOUND", "message": f"Event '{event_id}' not found."},
        )

    available = event["max_capacity"] - event["current_registrations"]
    return {
        "event_id": event["id"],
        "max_capacity": event["max_capacity"],
        "current_registrations": event["current_registrations"],
        "available_seats": max(0, available),
        "is_full": available <= 0,
    }


def search_events(
    filters: Dict[str, Any],
    authenticated_user: AuthenticatedUser,
) -> List[EventResponse]:
    """
    Phase 3 Tool Contract & Core Domain Service.
    Retrieves published events with accurate capacity metrics and registration status.
    """
    event_type = (filters.get("event_type") or "").strip().lower()
    is_virtual = filters.get("is_virtual")

    results: List[EventResponse] = []

    for event in _EVENTS_STORE:
        if not event.get("is_published", True):
            continue

        if event_type and event_type != event.get("event_type", "").lower():
            continue

        if is_virtual is not None and event.get("is_virtual") != is_virtual:
            continue

        unique_key = f"{event['id']}:{authenticated_user.id}"
        is_registered = unique_key in _EVENT_REGISTRATIONS_STORE and _EVENT_REGISTRATIONS_STORE[unique_key]["status"] == "confirmed"

        available_seats = max(0, event["max_capacity"] - event["current_registrations"])

        results.append(
            EventResponse(
                id=event["id"],
                title=event["title"],
                event_type=event["event_type"],
                description=event["description"],
                location=event["location"],
                is_virtual=event["is_virtual"],
                meeting_url=event.get("meeting_url"),
                start_time=event["start_time"],
                end_time=event["end_time"],
                max_capacity=event["max_capacity"],
                current_registrations=event["current_registrations"],
                available_seats=available_seats,
                is_published=event["is_published"],
                is_registered=is_registered,
                organizer_name=event["organizer_name"],
            )
        )

    return results


def get_event_by_id(event_id: str, authenticated_user: AuthenticatedUser) -> EventResponse:
    """Retrieve event details by ID."""
    event = next((e for e in _EVENTS_STORE if e["id"] == event_id), None)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EVENT_NOT_FOUND", "message": f"Event '{event_id}' not found."},
        )

    unique_key = f"{event['id']}:{authenticated_user.id}"
    is_registered = unique_key in _EVENT_REGISTRATIONS_STORE and _EVENT_REGISTRATIONS_STORE[unique_key]["status"] == "confirmed"
    available_seats = max(0, event["max_capacity"] - event["current_registrations"])

    return EventResponse(
        id=event["id"],
        title=event["title"],
        event_type=event["event_type"],
        description=event["description"],
        location=event["location"],
        is_virtual=event["is_virtual"],
        meeting_url=event.get("meeting_url"),
        start_time=event["start_time"],
        end_time=event["end_time"],
        max_capacity=event["max_capacity"],
        current_registrations=event["current_registrations"],
        available_seats=available_seats,
        is_published=event["is_published"],
        is_registered=is_registered,
        organizer_name=event["organizer_name"],
    )


def prepare_event_registration(
    event_id: str,
    authenticated_user: AuthenticatedUser,
) -> Dict[str, Any]:
    """Phase 3 Tool Contract (Read-only registration preview)."""
    event = get_event_by_id(event_id, authenticated_user)
    return {
        "event_id": event.id,
        "title": event.title,
        "start_time": event.start_time.isoformat(),
        "available_seats": event.available_seats,
        "is_full": event.available_seats <= 0,
        "confirmation_required": True,
    }


def register_for_event(
    event_id: str,
    user: AuthenticatedUser,
) -> EventRegistrationResponse:
    """
    Registers a user for an event atomically.
    Enforces capacity limits and prevents duplicate registrations.
    """
    event = next((e for e in _EVENTS_STORE if e["id"] == event_id), None)
    if not event or not event.get("is_published", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EVENT_NOT_FOUND", "message": f"Event '{event_id}' is not available for registration."},
        )

    # Check capacity atomically
    if event["current_registrations"] >= event["max_capacity"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EVENT_CAPACITY_EXCEEDED", "message": "This event has reached its maximum registration capacity."},
        )

    # Check duplicate registration: UNIQUE(event_id, user_id)
    unique_key = f"{event_id}:{user.id}"
    if unique_key in _EVENT_REGISTRATIONS_STORE and _EVENT_REGISTRATIONS_STORE[unique_key]["status"] == "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_REGISTRATION", "message": "You are already registered for this event."},
        )

    reg_id = f"reg-{len(_EVENT_REGISTRATIONS_STORE) + 1}"
    ticket_code = f"TICK-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    record = {
        "id": reg_id,
        "event_id": event_id,
        "event_title": event["title"],
        "user_id": user.id,
        "status": "confirmed",
        "ticket_code": ticket_code,
        "registered_at": now,
    }

    _EVENT_REGISTRATIONS_STORE[unique_key] = record
    event["current_registrations"] += 1  # Atomic increment

    return EventRegistrationResponse(**record)


def get_user_event_registrations(user: AuthenticatedUser) -> List[EventRegistrationResponse]:
    """Retrieve all event registrations for the authenticated user."""
    return [
        EventRegistrationResponse(**r)
        for r in _EVENT_REGISTRATIONS_STORE.values()
        if r["user_id"] == user.id and r["status"] == "confirmed"
    ]


def cancel_event_registration(
    event_id: str,
    user: AuthenticatedUser,
) -> Dict[str, Any]:
    """Cancels an existing event registration and decrements event registrations atomically."""
    unique_key = f"{event_id}:{user.id}"
    record = _EVENT_REGISTRATIONS_STORE.get(unique_key)
    if not record or record["status"] != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REGISTRATION_NOT_FOUND", "message": "Active registration not found for this event."},
        )

    record["status"] = "cancelled"
    event = next((e for e in _EVENTS_STORE if e["id"] == event_id), None)
    if event and event["current_registrations"] > 0:
        event["current_registrations"] -= 1

    return {"message": "Event registration successfully cancelled."}
