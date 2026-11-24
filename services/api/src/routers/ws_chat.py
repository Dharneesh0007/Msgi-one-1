"""
MSGI One — FastAPI WebSocket Real-Time Chat Transport (/ws/chat) (Phase 6)
Versioned Event Envelope (v1.0):
  connection.ready, message.send, message.accepted, message.created,
  message.delivered, message.read, typing.started, typing.stopped,
  presence.changed, conversation.updated, connection.error
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from src.core.dependencies import authenticate_websocket_token
from src.core.security import SlidingWindowRateLimiter
from src.schemas.messaging import MessageCreateRequest, WSEventEnvelope
from src.services.messaging_service import (
    _CONVERSATIONS_STORE,
    _get_authorized_conversation,
    mark_conversation_read,
    mark_message_delivered,
    send_message,
)
from src.services.realtime_bus import chat_connection_manager

router = APIRouter(tags=["Real-Time Messaging WebSocket"])

_ws_rate_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=10)


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
) -> None:
    raw_token = token or websocket.headers.get("authorization")
    try:
        user = authenticate_websocket_token(raw_token)
    except HTTPException as exc:
        await websocket.close(code=4401, reason=str(exc.detail.get("code", "UNAUTHENTICATED")))
        return

    await chat_connection_manager.connect(user.id, websocket)
    try:
        ready_evt = WSEventEnvelope(
            event_type="connection.ready",
            sender_id=user.id,
            payload={"user_id": user.id, "online": True},
        ).model_dump()
        await chat_connection_manager.send_to_user(user.id, ready_evt)

        while True:
            raw_text = await websocket.receive_text()
            if not _ws_rate_limiter.check(f"ws:{user.id}"):
                err_evt = WSEventEnvelope(
                    event_type="connection.error",
                    sender_id=user.id,
                    payload={"code": "RATE_LIMITED", "message": "WebSocket message rate limit exceeded."},
                ).model_dump()
                await chat_connection_manager.send_to_user(user.id, err_evt)
                continue

            try:
                frame = json.loads(raw_text)
            except json.JSONDecodeError:
                err_evt = WSEventEnvelope(
                    event_type="connection.error",
                    sender_id=user.id,
                    payload={"code": "INVALID_JSON", "message": "WebSocket frame must be valid JSON."},
                ).model_dump()
                await chat_connection_manager.send_to_user(user.id, err_evt)
                continue

            evt_type = frame.get("event_type")
            conv_id = frame.get("conversation_id")
            idem_key = frame.get("client_idempotency_key")
            payload = frame.get("payload") or {}

            if evt_type == "ping":
                await chat_connection_manager.send_to_user(
                    user.id,
                    WSEventEnvelope(event_type="pong", sender_id=user.id, payload={"ts": payload.get("ts")}).model_dump(),
                )
                continue

            if not conv_id:
                await chat_connection_manager.send_to_user(
                    user.id,
                    WSEventEnvelope(
                        event_type="connection.error",
                        sender_id=user.id,
                        payload={"code": "MISSING_CONVERSATION_ID", "message": "conversation_id is required."},
                    ).model_dump(),
                )
                continue

            try:
                if evt_type == "message.send":
                    msg_req = MessageCreateRequest(
                        body=payload.get("body", ""),
                        message_type=payload.get("message_type", "text"),
                        client_idempotency_key=idem_key,
                        reply_to_message_id=payload.get("reply_to_message_id"),
                    )
                    # Persist durably BEFORE emitting acceptance/created fan-out
                    saved = send_message(user, conv_id, msg_req)
                    conv = _CONVERSATIONS_STORE[conv_id]

                    accepted_evt = WSEventEnvelope(
                        event_type="message.accepted",
                        conversation_id=conv_id,
                        sender_id=user.id,
                        client_idempotency_key=idem_key,
                        payload={"message_id": saved.id, "seq": saved.seq, "status": "sent"},
                    ).model_dump()
                    await chat_connection_manager.send_to_user(user.id, accepted_evt)

                    created_evt = WSEventEnvelope(
                        event_type="message.created",
                        conversation_id=conv_id,
                        sender_id=user.id,
                        client_idempotency_key=idem_key,
                        payload=saved.model_dump(mode="json"),
                    ).model_dump()
                    await chat_connection_manager.publish_conversation_event(
                        conv_id,
                        [conv["participant_one_id"], conv["participant_two_id"]],
                        created_evt,
                    )

                elif evt_type == "message.delivered":
                    seq = int(payload.get("seq", 0))
                    res = mark_message_delivered(user, conv_id, seq)
                    conv = _CONVERSATIONS_STORE[conv_id]
                    await chat_connection_manager.publish_conversation_event(
                        conv_id,
                        [conv["participant_one_id"], conv["participant_two_id"]],
                        WSEventEnvelope(
                            event_type="message.delivered",
                            conversation_id=conv_id,
                            sender_id=user.id,
                            payload=res,
                        ).model_dump(),
                    )

                elif evt_type == "message.read":
                    seq = int(payload.get("last_read_seq", 1))
                    res = mark_conversation_read(user, conv_id, seq)
                    conv = _CONVERSATIONS_STORE[conv_id]
                    await chat_connection_manager.publish_conversation_event(
                        conv_id,
                        [conv["participant_one_id"], conv["participant_two_id"]],
                        WSEventEnvelope(
                            event_type="message.read",
                            conversation_id=conv_id,
                            sender_id=user.id,
                            payload=res,
                        ).model_dump(),
                    )

                elif evt_type in ("typing.started", "typing.stopped"):
                    conv = _get_authorized_conversation(user, conv_id, check_block=True)
                    peer_id = conv["participant_two_id"] if conv["participant_one_id"] == user.id else conv["participant_one_id"]
                    await chat_connection_manager.publish_conversation_event(
                        conv_id,
                        [peer_id],
                        WSEventEnvelope(
                            event_type=evt_type,
                            conversation_id=conv_id,
                            sender_id=user.id,
                            payload={"user_id": user.id},
                        ).model_dump(),
                    )
                else:
                    await chat_connection_manager.send_to_user(
                        user.id,
                        WSEventEnvelope(
                            event_type="connection.error",
                            conversation_id=conv_id,
                            sender_id=user.id,
                            payload={"code": "UNKNOWN_EVENT_TYPE", "message": f"Unsupported event_type '{evt_type}'."},
                        ).model_dump(),
                    )
            except HTTPException as http_err:
                await chat_connection_manager.send_to_user(
                    user.id,
                    WSEventEnvelope(
                        event_type="connection.error",
                        conversation_id=conv_id,
                        sender_id=user.id,
                        client_idempotency_key=idem_key,
                        payload=http_err.detail if isinstance(http_err.detail, dict) else {"code": "ERROR", "message": str(http_err.detail)},
                    ).model_dump(),
                )
    except WebSocketDisconnect:
        pass
    finally:
        await chat_connection_manager.disconnect(user.id, websocket)
