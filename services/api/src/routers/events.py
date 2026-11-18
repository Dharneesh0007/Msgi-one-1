"""
MSGI One — Events and Reunions API Router
Endpoints: GET /api/v1/events, GET /api/v1/events/{id}, POST /api/v1/events,
           POST /api/v1/events/{id}/registrations, GET /api/v1/me/event-registrations,
           DELETE /api/v1/events/{id}/registrations
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.business import (
    EventResponse,
    EventCreateRequest,
    EventRegistrationResponse,
)
from src.services.events_service import (
    search_events,
    get_event_by_id,
    register_for_event,
    get_user_event_registrations,
    cancel_event_registration,
)

router = APIRouter(tags=["Events & Reunions"])


@router.get(
    "/events",
    response_model=StandardEnvelope[List[EventResponse]],
    summary="List Institutional Events",
    description="Retrieve published events, webinars, and reunions with capacity counters.",
)
def list_events(
    event_type: Optional[str] = Query(None, description="webinar, reunion, workshop, career_fair"),
    is_virtual: Optional[bool] = Query(None, description="Filter for virtual events"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[EventResponse]]:
    filters = {"event_type": event_type, "is_virtual": is_virtual}
    events = search_events(filters=filters, authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=events,
        error=None,
        meta={"total": len(events)},
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/events/{event_id}",
    response_model=StandardEnvelope[EventResponse],
    summary="Get Event Details",
)
def get_event(
    event_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[EventResponse]:
    event = get_event_by_id(event_id=event_id, authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=event,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/events/{event_id}/registrations",
    response_model=StandardEnvelope[EventRegistrationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register for Event",
    description="Atomically books a seat and generates a ticket code. Rejects overbooking and duplicate registrations.",
)
def register_event(
    event_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[EventRegistrationResponse]:
    registration = register_for_event(event_id=event_id, user=current_user)
    return StandardEnvelope(
        status="success",
        data=registration,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/me/event-registrations",
    response_model=StandardEnvelope[List[EventRegistrationResponse]],
    summary="Get My Event Registrations",
)
def list_my_registrations(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[EventRegistrationResponse]]:
    registrations = get_user_event_registrations(user=current_user)
    return StandardEnvelope(
        status="success",
        data=registrations,
        error=None,
        meta={"total": len(registrations)},
        timestamp=datetime.now(timezone.utc),
    )


@router.delete(
    "/events/{event_id}/registrations",
    summary="Cancel Event Registration",
)
def cancel_registration(
    event_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    result = cancel_event_registration(event_id=event_id, user=current_user)
    return StandardEnvelope(
        status="success",
        data=result,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )
