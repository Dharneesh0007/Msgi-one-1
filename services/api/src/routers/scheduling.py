"""
MSGI One — Mentorship & Meeting Scheduling API Router (Phase 5)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import PlainTextResponse

from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.scheduling import (
    AvailabilityUpdateRequest,
    AvailabilityWindowResponse,
    MeetingCancelRequest,
    MeetingFeedbackRequest,
    MeetingRequestAccept,
    MeetingRequestConfirm,
    MeetingRequestCounterPropose,
    MeetingRequestCreate,
    MeetingRequestDecline,
    MeetingRequestResponse,
    MeetingRescheduleRequest,
    MeetingResponse,
)
from src.schemas.user import StandardEnvelope
from src.services.scheduling_service import (
    accept_meeting_request,
    cancel_meeting,
    cancel_meeting_request,
    confirm_counter_proposal,
    counter_propose_meeting_request,
    create_meeting_request,
    decline_meeting_request,
    export_meeting_ics,
    get_alumni_availability_and_slots,
    get_meeting,
    list_my_meeting_requests,
    list_my_meetings,
    reschedule_meeting,
    set_alumni_availability,
    submit_meeting_feedback,
)

router = APIRouter(tags=["Scheduling & Meetings"])


@router.put(
    "/scheduling/availability/me",
    response_model=StandardEnvelope[List[AvailabilityWindowResponse]],
    summary="Configure Alumni Weekly Availability & Exceptions",
)
def update_my_availability(
    payload: AvailabilityUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[AvailabilityWindowResponse]]:
    windows = set_alumni_availability(current_user, payload)
    return StandardEnvelope(status="success", data=windows, timestamp=datetime.now(timezone.utc))


@router.get(
    "/scheduling/availability/{alumni_id}",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Get Alumni Availability & Open UTC Slots",
)
def read_alumni_availability(
    alumni_id: str,
    days_ahead: int = Query(default=7, ge=1, le=30),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    data = get_alumni_availability_and_slots(alumni_id=alumni_id, days_ahead=days_ahead)
    return StandardEnvelope(status="success", data=data, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/requests",
    response_model=StandardEnvelope[MeetingRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Meeting Request with up to 3 Proposed Slots",
)
def submit_meeting_request(
    payload: MeetingRequestCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingRequestResponse]:
    created = create_meeting_request(current_user, payload, idempotency_key=idempotency_key)
    return StandardEnvelope(status="success", data=created, timestamp=datetime.now(timezone.utc))


@router.get(
    "/meetings/requests",
    response_model=StandardEnvelope[List[MeetingRequestResponse]],
    summary="List My Sent and Received Meeting Requests",
)
def get_my_meeting_requests(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[MeetingRequestResponse]]:
    items = list_my_meeting_requests(current_user)
    return StandardEnvelope(status="success", data=items, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/requests/{request_id}/accept",
    response_model=StandardEnvelope[MeetingResponse],
    summary="Alumni Accepts a Proposed Slot (Atomic Booking)",
)
def accept_request(
    request_id: str,
    payload: MeetingRequestAccept,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingResponse]:
    meeting = accept_meeting_request(current_user, request_id, payload)
    return StandardEnvelope(status="success", data=meeting, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/requests/{request_id}/decline",
    response_model=StandardEnvelope[MeetingRequestResponse],
    summary="Alumni Declines Meeting Request",
)
def decline_request(
    request_id: str,
    payload: MeetingRequestDecline,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingRequestResponse]:
    updated = decline_meeting_request(current_user, request_id, payload)
    return StandardEnvelope(status="success", data=updated, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/requests/{request_id}/counter-propose",
    response_model=StandardEnvelope[MeetingRequestResponse],
    summary="Alumni Proposes Alternative Slots",
)
def counter_propose_request(
    request_id: str,
    payload: MeetingRequestCounterPropose,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingRequestResponse]:
    updated = counter_propose_meeting_request(current_user, request_id, payload)
    return StandardEnvelope(status="success", data=updated, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/requests/{request_id}/confirm",
    response_model=StandardEnvelope[MeetingResponse],
    summary="Student Confirms Counter-Proposed Slot",
)
def confirm_request_slot(
    request_id: str,
    payload: MeetingRequestConfirm,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingResponse]:
    meeting = confirm_counter_proposal(current_user, request_id, payload)
    return StandardEnvelope(status="success", data=meeting, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/requests/{request_id}/cancel",
    response_model=StandardEnvelope[MeetingRequestResponse],
    summary="Cancel Meeting Request",
)
def cancel_request(
    request_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingRequestResponse]:
    updated = cancel_meeting_request(current_user, request_id)
    return StandardEnvelope(status="success", data=updated, timestamp=datetime.now(timezone.utc))


@router.get(
    "/meetings",
    response_model=StandardEnvelope[List[MeetingResponse]],
    summary="List My Upcoming & Past Meetings",
)
def get_my_meetings(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[MeetingResponse]]:
    items = list_my_meetings(current_user)
    return StandardEnvelope(status="success", data=items, timestamp=datetime.now(timezone.utc))


@router.get(
    "/meetings/{meeting_id}",
    response_model=StandardEnvelope[MeetingResponse],
    summary="Get Confirmed Meeting Details",
)
def get_meeting_detail(
    meeting_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingResponse]:
    meeting = get_meeting(current_user, meeting_id)
    return StandardEnvelope(status="success", data=meeting, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/{meeting_id}/reschedule",
    response_model=StandardEnvelope[MeetingResponse],
    summary="Reschedule Confirmed Meeting Atomically",
)
def reschedule_confirmed_meeting(
    meeting_id: str,
    payload: MeetingRescheduleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingResponse]:
    new_meeting = reschedule_meeting(current_user, meeting_id, payload)
    return StandardEnvelope(status="success", data=new_meeting, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/{meeting_id}/cancel",
    response_model=StandardEnvelope[MeetingResponse],
    summary="Cancel Confirmed Meeting",
)
def cancel_confirmed_meeting(
    meeting_id: str,
    payload: MeetingCancelRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingResponse]:
    updated = cancel_meeting(current_user, meeting_id, payload)
    return StandardEnvelope(status="success", data=updated, timestamp=datetime.now(timezone.utc))


@router.post(
    "/meetings/{meeting_id}/feedback",
    response_model=StandardEnvelope[MeetingResponse],
    summary="Submit Post-Meeting Feedback",
)
def post_meeting_feedback(
    meeting_id: str,
    payload: MeetingFeedbackRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MeetingResponse]:
    updated = submit_meeting_feedback(current_user, meeting_id, payload)
    return StandardEnvelope(status="success", data=updated, timestamp=datetime.now(timezone.utc))


@router.get(
    "/meetings/{meeting_id}/ics",
    response_class=PlainTextResponse,
    summary="Export Confirmed Meeting as RFC 5545 iCalendar (.ics)",
)
def download_meeting_ics(
    meeting_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PlainTextResponse:
    ics_text = export_meeting_ics(current_user, meeting_id)
    return PlainTextResponse(
        content=ics_text,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="meeting-{meeting_id}.ics"'},
    )
