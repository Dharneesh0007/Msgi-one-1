"""
MSGI One — Real-Time Audio/Video Meeting Room Router (Phase 7)
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, Request

from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.rooms import (
    ParticipantActionRequest,
    RoomStateResponse,
    RoomTokenRequest,
    RoomTokenResponse,
)
from src.schemas.user import StandardEnvelope
from src.services.room_service import (
    admit_participant,
    end_meeting_room,
    get_room_state,
    process_livekit_webhook,
    remove_participant,
    request_room_token,
)

router = APIRouter(prefix="/rooms", tags=["Real-Time Audio/Video Rooms"])


@router.post(
    "/{meeting_id}/token",
    response_model=StandardEnvelope[RoomTokenResponse],
    summary="Request Short-Lived LiveKit Room Token",
)
def mint_room_token(
    meeting_id: str,
    payload: RoomTokenRequest = RoomTokenRequest(),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[RoomTokenResponse]:
    data = request_room_token(current_user, meeting_id, payload)
    return StandardEnvelope(status="success", data=data, timestamp=datetime.now(timezone.utc))


@router.get(
    "/{meeting_id}",
    response_model=StandardEnvelope[RoomStateResponse],
    summary="Get Meeting Room & Participant State",
)
def fetch_room_state(
    meeting_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[RoomStateResponse]:
    data = get_room_state(current_user, meeting_id)
    return StandardEnvelope(status="success", data=data, timestamp=datetime.now(timezone.utc))


@router.post(
    "/{meeting_id}/admit",
    response_model=StandardEnvelope[RoomStateResponse],
    summary="Host Admits Waiting Room Participant",
)
def admit_room_participant(
    meeting_id: str,
    payload: ParticipantActionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[RoomStateResponse]:
    data = admit_participant(current_user, meeting_id, payload.target_user_id)
    return StandardEnvelope(status="success", data=data, timestamp=datetime.now(timezone.utc))


@router.post(
    "/{meeting_id}/remove",
    response_model=StandardEnvelope[RoomStateResponse],
    summary="Host Removes Participant",
)
def remove_room_participant(
    meeting_id: str,
    payload: ParticipantActionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[RoomStateResponse]:
    data = remove_participant(current_user, meeting_id, payload.target_user_id)
    return StandardEnvelope(status="success", data=data, timestamp=datetime.now(timezone.utc))


@router.post(
    "/{meeting_id}/end",
    response_model=StandardEnvelope[RoomStateResponse],
    summary="Host Ends Meeting Room",
)
def end_room(
    meeting_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[RoomStateResponse]:
    data = end_meeting_room(current_user, meeting_id)
    return StandardEnvelope(status="success", data=data, timestamp=datetime.now(timezone.utc))


@router.post(
    "/webhooks/livekit",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Signed LiveKit Webhook Receiver",
)
async def livekit_webhook(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> StandardEnvelope[Dict[str, Any]]:
    raw_body = await request.body()
    result = process_livekit_webhook(raw_body, authorization)
    return StandardEnvelope(status="success", data=result, timestamp=datetime.now(timezone.utc))
