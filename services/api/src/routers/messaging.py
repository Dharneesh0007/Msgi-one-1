"""
MSGI One — Real-Time Messaging & Safety REST Router (Phase 6)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.messaging import (
    AttachmentUploadInput,
    ConversationCreateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessageResponse,
    ReadReceiptRequest,
    UserBlockRequest,
    UserReportRequest,
    WSEventEnvelope,
)
from src.schemas.user import StandardEnvelope
from src.services.messaging_service import (
    _CONVERSATIONS_STORE,
    block_user,
    get_messages,
    get_or_create_conversation,
    list_conversations,
    mark_conversation_read,
    report_user,
    send_message,
    unblock_user,
)
from src.services.realtime_bus import chat_connection_manager

router = APIRouter(tags=["Real-Time Messaging & Safety"])


@router.get(
    "/conversations",
    response_model=StandardEnvelope[List[ConversationResponse]],
    summary="List My Conversations",
)
def get_my_conversations(
    search: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[ConversationResponse]]:
    items = list_conversations(current_user, search=search)
    return StandardEnvelope(status="success", data=items, timestamp=datetime.now(timezone.utc))


@router.post(
    "/conversations",
    response_model=StandardEnvelope[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Get or Create 1-on-1 Conversation",
)
def create_or_fetch_conversation(
    payload: ConversationCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[ConversationResponse]:
    conv = get_or_create_conversation(current_user, payload.recipient_id)
    return StandardEnvelope(status="success", data=conv, timestamp=datetime.now(timezone.utc))


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=StandardEnvelope[List[MessageResponse]],
    summary="Fetch Cursor-Paginated Message History",
)
def list_conversation_messages(
    conversation_id: str,
    after_seq: int = Query(0, ge=0),
    before_seq: Optional[int] = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[MessageResponse]]:
    msgs = get_messages(current_user, conversation_id, after_seq=after_seq, before_seq=before_seq, limit=limit)
    return StandardEnvelope(status="success", data=msgs, timestamp=datetime.now(timezone.utc))


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=StandardEnvelope[MessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Send Durable Message (REST / Offline Queue Sync)",
)
async def post_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[MessageResponse]:
    msg = send_message(current_user, conversation_id, payload)
    conv = _CONVERSATIONS_STORE[conversation_id]
    evt = WSEventEnvelope(
        event_type="message.created",
        conversation_id=conversation_id,
        sender_id=current_user.id,
        client_idempotency_key=payload.client_idempotency_key,
        payload=msg.model_dump(mode="json"),
    ).model_dump()
    await chat_connection_manager.publish_conversation_event(
        conversation_id,
        [conv["participant_one_id"], conv["participant_two_id"]],
        evt,
    )
    return StandardEnvelope(status="success", data=msg, timestamp=datetime.now(timezone.utc))


@router.post(
    "/conversations/{conversation_id}/read",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Mark Conversation Messages Read",
)
async def mark_read(
    conversation_id: str,
    payload: ReadReceiptRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    res = mark_conversation_read(current_user, conversation_id, payload.last_read_seq)
    conv = _CONVERSATIONS_STORE[conversation_id]
    evt = WSEventEnvelope(
        event_type="message.read",
        conversation_id=conversation_id,
        sender_id=current_user.id,
        payload=res,
    ).model_dump()
    await chat_connection_manager.publish_conversation_event(
        conversation_id,
        [conv["participant_one_id"], conv["participant_two_id"]],
        evt,
    )
    return StandardEnvelope(status="success", data=res, timestamp=datetime.now(timezone.utc))


@router.post(
    "/conversations/{conversation_id}/attachments/validate",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Validate Attachment Metadata & Security Constraints",
)
def validate_attachment(
    conversation_id: str,
    payload: AttachmentUploadInput,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    return StandardEnvelope(
        status="success",
        data={"conversation_id": conversation_id, "validated": True, "file_name": payload.file_name, "mime_type": payload.mime_type},
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/safety/blocks",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Block a User",
)
def create_block(
    payload: UserBlockRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    res = block_user(current_user, payload.blocked_user_id, reason=payload.reason)
    return StandardEnvelope(status="success", data=res, timestamp=datetime.now(timezone.utc))


@router.delete(
    "/safety/blocks/{blocked_user_id}",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Unblock a User",
)
def remove_block(
    blocked_user_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    res = unblock_user(current_user, blocked_user_id)
    return StandardEnvelope(status="success", data=res, timestamp=datetime.now(timezone.utc))


@router.post(
    "/safety/reports",
    response_model=StandardEnvelope[Dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="Report User or Message for Moderation",
)
def create_report(
    payload: UserReportRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    rep = report_user(current_user, payload)
    return StandardEnvelope(status="success", data=rep, timestamp=datetime.now(timezone.utc))
