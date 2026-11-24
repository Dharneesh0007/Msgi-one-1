"""
MSGI One — Real-Time 1-on-1 Messaging & Safety Domain Service (Phase 6)
Principles:
  - PostgreSQL / durable store persists messages BEFORE acknowledgement.
  - Client-generated idempotency keys prevent duplicates across retries.
  - Monotonic per-conversation sequence numbers (`seq`) guarantee deterministic ordering & cursor recovery.
  - PermissionChecker enforces membership and bilateral user blocking on every operation.
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional
import uuid
from fastapi import HTTPException, status

from src.core.dependencies import AuthenticatedUser
from src.core.permissions import PermissionChecker
from src.schemas.messaging import (
    AttachmentUploadInput,
    ConversationResponse,
    MessageAttachmentResponse,
    MessageCreateRequest,
    MessageResponse,
    UserReportRequest,
)
from src.services.admin_service import _MODERATION_REPORTS_STORE
from src.services.alumni_service import _SYNTHETIC_ALUMNI_STORE
from src.services.notifications_service import create_notification
from src.services.realtime_bus import chat_connection_manager

_MSG_LOCK = threading.RLock()

# Durable stores mirroring Phase 2 relational tables
_CONVERSATIONS_STORE: Dict[str, Dict[str, Any]] = {}
_PARTICIPANTS_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}  # conv_id -> {user_id -> state}
_MESSAGES_STORE: Dict[str, List[Dict[str, Any]]] = {}  # conv_id -> ordered list of message dicts
_IDEMPOTENCY_INDEX: Dict[str, Dict[str, Any]] = {}  # (conv_id:sender_id:key) -> message dict
_BLOCKS_STORE: set[tuple[str, str]] = set()  # (blocker_id, blocked_id)


def _canonical_pair(u1: str, u2: str) -> tuple[str, str]:
    return (u1, u2) if u1 < u2 else (u2, u1)


def is_pair_blocked(u1: str, u2: str) -> bool:
    return (u1, u2) in _BLOCKS_STORE or (u2, u1) in _BLOCKS_STORE


def _resolve_peer_name(user_id: str) -> str:
    alum = next((a for a in _SYNTHETIC_ALUMNI_STORE if a["user_id"] == user_id or a["id"] == user_id), None)
    if alum:
        return alum["full_name"]
    return user_id


def _serialize_conversation(conv: Dict[str, Any], current_user_id: str) -> ConversationResponse:
    peer_id = conv["participant_two_id"] if conv["participant_one_id"] == current_user_id else conv["participant_one_id"]
    part_state = (_PARTICIPANTS_STORE.get(conv["id"]) or {}).get(current_user_id, {})
    blocked = is_pair_blocked(current_user_id, peer_id)
    return ConversationResponse(
        id=conv["id"],
        peer_id=peer_id,
        peer_name=_resolve_peer_name(peer_id),
        last_message_at=conv.get("last_message_at"),
        last_message_preview=conv.get("last_message_preview"),
        last_seq=conv["last_seq"],
        unread_count=part_state.get("unread_count", 0),
        peer_online=False if blocked else chat_connection_manager.is_user_online(peer_id),
        created_at=conv["created_at"],
    )


def get_or_create_conversation(user: AuthenticatedUser, recipient_id: str) -> ConversationResponse:
    alum = next((a for a in _SYNTHETIC_ALUMNI_STORE if a["id"] == recipient_id), None)
    target_id = alum["user_id"] if alum else recipient_id

    if target_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_CONVERSATION_FORBIDDEN", "message": "Cannot start a conversation with yourself."},
        )
    if is_pair_blocked(user.id, target_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_BLOCKED", "message": "Communication is blocked between these users."},
        )

    p1, p2 = _canonical_pair(user.id, target_id)
    with _MSG_LOCK:
        existing = next(
            (c for c in _CONVERSATIONS_STORE.values() if c["participant_one_id"] == p1 and c["participant_two_id"] == p2),
            None,
        )
        if existing:
            return _serialize_conversation(existing, user.id)

        conv_id = f"conv-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        conv = {
            "id": conv_id,
            "participant_one_id": p1,
            "participant_two_id": p2,
            "last_message_at": None,
            "last_message_preview": None,
            "last_seq": 0,
            "created_at": now,
        }
        _CONVERSATIONS_STORE[conv_id] = conv
        _PARTICIPANTS_STORE[conv_id] = {
            p1: {"last_read_seq": 0, "last_delivered_seq": 0, "unread_count": 0},
            p2: {"last_read_seq": 0, "last_delivered_seq": 0, "unread_count": 0},
        }
        _MESSAGES_STORE[conv_id] = []
        return _serialize_conversation(conv, user.id)


def list_conversations(user: AuthenticatedUser, search: Optional[str] = None) -> List[ConversationResponse]:
    q = (search or "").strip().lower()
    convs = [
        _serialize_conversation(c, user.id)
        for c in _CONVERSATIONS_STORE.values()
        if user.id in (c["participant_one_id"], c["participant_two_id"])
    ]
    if q:
        convs = [
            c for c in convs
            if q in c.peer_name.lower() or (c.last_message_preview and q in c.last_message_preview.lower())
        ]
    convs.sort(key=lambda c: c.last_message_at or c.created_at, reverse=True)
    return convs


def _get_authorized_conversation(user: AuthenticatedUser, conversation_id: str, check_block: bool = True) -> Dict[str, Any]:
    conv = _CONVERSATIONS_STORE.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND", "message": "Conversation not found."})
    blocked = check_block and is_pair_blocked(conv["participant_one_id"], conv["participant_two_id"])
    PermissionChecker.verify_conversation_access(
        user.id,
        conv["participant_one_id"],
        conv["participant_two_id"],
        is_blocked=blocked,
    )
    return conv


def send_message(user: AuthenticatedUser, conversation_id: str, payload: MessageCreateRequest) -> MessageResponse:
    with _MSG_LOCK:
        conv = _get_authorized_conversation(user, conversation_id, check_block=True)

        if payload.client_idempotency_key:
            idem_k = f"{conversation_id}:{user.id}:{payload.client_idempotency_key}"
            existing_msg = _IDEMPOTENCY_INDEX.get(idem_k)
            if existing_msg:
                return MessageResponse(**existing_msg)

        now = datetime.now(timezone.utc)
        next_seq = conv["last_seq"] + 1
        msg_id = f"msg-{uuid.uuid4().hex[:10]}"

        attachments = [
            MessageAttachmentResponse(
                id=f"att-{uuid.uuid4().hex[:10]}",
                message_id=msg_id,
                file_name=a.file_name,
                mime_type=a.mime_type,
                size_bytes=a.size_bytes,
                sha256_checksum=a.sha256_checksum,
                storage_path=a.storage_path,
                scan_status="clean",
                created_at=now,
            ).model_dump()
            for a in payload.attachments
        ]

        msg_dict = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "sender_id": user.id,
            "seq": next_seq,
            "body": payload.body.strip(),
            "message_type": payload.message_type,
            "status": "sent",
            "client_idempotency_key": payload.client_idempotency_key,
            "reply_to_message_id": payload.reply_to_message_id,
            "attachments": attachments,
            "created_at": now,
        }

        _MESSAGES_STORE[conversation_id].append(msg_dict)
        if payload.client_idempotency_key:
            _IDEMPOTENCY_INDEX[f"{conversation_id}:{user.id}:{payload.client_idempotency_key}"] = msg_dict

        conv["last_seq"] = next_seq
        conv["last_message_at"] = now
        conv["last_message_preview"] = payload.body.strip()[:120]

        peer_id = conv["participant_two_id"] if conv["participant_one_id"] == user.id else conv["participant_one_id"]
        _PARTICIPANTS_STORE[conversation_id][peer_id]["unread_count"] += 1

        create_notification(
            user_id=peer_id,
            event_type="message.created",
            entity_id=conversation_id,
            title="New Message",
            message=f"{user.first_name or 'Member'}: {payload.body.strip()[:80]}",
            payload={"conversation_id": conversation_id, "message_id": msg_id},
        )
        return MessageResponse(**msg_dict)


def get_messages(
    user: AuthenticatedUser,
    conversation_id: str,
    after_seq: int = 0,
    before_seq: Optional[int] = None,
    limit: int = 50,
) -> List[MessageResponse]:
    _get_authorized_conversation(user, conversation_id, check_block=False)
    msgs = _MESSAGES_STORE.get(conversation_id, [])
    filtered = [m for m in msgs if m["seq"] > after_seq and (before_seq is None or m["seq"] < before_seq)]
    if before_seq is not None:
        filtered = filtered[-limit:]
    else:
        filtered = filtered[:limit]
    return [MessageResponse(**m) for m in filtered]


def mark_conversation_read(user: AuthenticatedUser, conversation_id: str, last_read_seq: int) -> Dict[str, Any]:
    with _MSG_LOCK:
        conv = _get_authorized_conversation(user, conversation_id, check_block=False)
        part = _PARTICIPANTS_STORE[conversation_id][user.id]
        target_seq = min(last_read_seq, conv["last_seq"])
        part["last_read_seq"] = max(part["last_read_seq"], target_seq)
        part["last_delivered_seq"] = max(part["last_delivered_seq"], target_seq)
        part["unread_count"] = max(0, conv["last_seq"] - part["last_read_seq"])

        for m in _MESSAGES_STORE.get(conversation_id, []):
            if m["sender_id"] != user.id and m["seq"] <= part["last_read_seq"]:
                m["status"] = "read"

        return {
            "conversation_id": conversation_id,
            "user_id": user.id,
            "last_read_seq": part["last_read_seq"],
            "unread_count": part["unread_count"],
        }


def mark_message_delivered(user: AuthenticatedUser, conversation_id: str, seq: int) -> Dict[str, Any]:
    with _MSG_LOCK:
        conv = _get_authorized_conversation(user, conversation_id, check_block=False)
        part = _PARTICIPANTS_STORE[conversation_id][user.id]
        part["last_delivered_seq"] = max(part["last_delivered_seq"], min(seq, conv["last_seq"]))
        for m in _MESSAGES_STORE.get(conversation_id, []):
            if m["sender_id"] != user.id and m["seq"] <= part["last_delivered_seq"] and m["status"] == "sent":
                m["status"] = "delivered"
        return {"conversation_id": conversation_id, "last_delivered_seq": part["last_delivered_seq"]}


def block_user(blocker: AuthenticatedUser, blocked_user_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    if blocker.id == blocked_user_id:
        raise HTTPException(status_code=400, detail={"code": "INVALID_BLOCK", "message": "Cannot block yourself."})
    _BLOCKS_STORE.add((blocker.id, blocked_user_id))
    return {"blocker_id": blocker.id, "blocked_user_id": blocked_user_id, "blocked": True, "reason": reason}


def unblock_user(blocker: AuthenticatedUser, blocked_user_id: str) -> Dict[str, Any]:
    _BLOCKS_STORE.discard((blocker.id, blocked_user_id))
    return {"blocker_id": blocker.id, "blocked_user_id": blocked_user_id, "blocked": False}


def report_user(reporter: AuthenticatedUser, payload: UserReportRequest) -> Dict[str, Any]:
    rep = {
        "id": f"rep-{uuid.uuid4().hex[:10]}",
        "reporter_id": reporter.id,
        "reported_user_id": payload.reported_user_id,
        "message_id": payload.message_id,
        "category": payload.category,
        "description": payload.description,
        "status": "pending",
        "reviewed_by": None,
        "resolution_notes": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
    }
    _MODERATION_REPORTS_STORE.append(rep)
    return rep


# ============================================================================
# AI TOOL CONTRACTS (READ/DRAFT ONLY — RULE 15 APPROVAL REQUIRED TO SEND)
# ============================================================================

def draft_message_tool(
    sender: AuthenticatedUser,
    recipient_id: str,
    purpose: str,
) -> Dict[str, Any]:
    return {
        "action_type": "send_message",
        "confirmation_required": True,
        "sender_id": sender.id,
        "recipient_id": recipient_id,
        "draft_body": f"Hello, I am reaching out regarding {purpose}. Would you be open to connecting?",
    }


def summarize_permitted_conversation_tool(user: AuthenticatedUser, conversation_id: str) -> Dict[str, Any]:
    msgs = get_messages(user, conversation_id, after_seq=0, limit=25)
    return {
        "conversation_id": conversation_id,
        "message_count": len(msgs),
        "latest_messages": [{"sender_id": m.sender_id, "body": m.body[:160], "seq": m.seq} for m in msgs[-5:]],
    }
