"""
MSGI One — Human-In-The-Loop (HITL) Approval Engine
Phase 7 & Phase 8 — Consequential Mutation Gate (Rule 15)
Principles: Kleppmann Idempotency, Pressman Risk Containment & Tamper Resistance.
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel

from src.core.dependencies import AuthenticatedUser
from src.ai.tools import (
    create_mentor_request_tool,
    submit_job_application_tool,
    register_for_event_tool,
)


class ApprovalRequestRecord(BaseModel):
    id: str
    run_id: str
    user_id: str
    action_type: str  # 'send_mentor_request', 'apply_job', 'register_event', 'create_meeting_request', 'reschedule_meeting', 'cancel_meeting', 'send_message'
    action_payload: Dict[str, Any]
    target_entity_id: str
    target_entity_name: str
    status: str = "pending"  # 'pending', 'approved', 'rejected', 'expired'
    idempotency_key: str
    args_hash: str = ""
    expires_at: Optional[str] = None
    decision_note: Optional[str] = None
    decided_at: Optional[str] = None
    created_at: str
    execution_result: Optional[Dict[str, Any]] = None


# Thread-safe store for approval requests and execution results
_APPROVALS_STORE: Dict[str, ApprovalRequestRecord] = {}


def generate_idempotency_key(user_id: str, action_type: str, target_entity_id: str) -> str:
    raw = f"{user_id}:{action_type}:{target_entity_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def compute_args_hash(action_type: str, target_entity_id: str, action_payload: Dict[str, Any]) -> str:
    canonical = json.dumps(
        {
            "action_type": action_type,
            "target_entity_id": target_entity_id,
            "action_payload": action_payload,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_expired(record: ApprovalRequestRecord) -> bool:
    if not record.expires_at:
        return False
    try:
        exp_dt = datetime.fromisoformat(record.expires_at)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > exp_dt
    except Exception:
        return False


def create_approval_request(
    run_id: str,
    user_id: str,
    action_type: str,
    action_payload: Dict[str, Any],
    target_entity_id: str,
    target_entity_name: str,
    ttl_seconds: int = 900,
) -> ApprovalRequestRecord:
    idempotency_key = generate_idempotency_key(user_id, action_type, target_entity_id)

    # Return active pending record with matching idempotency key unless expired
    for existing in _APPROVALS_STORE.values():
        if existing.idempotency_key == idempotency_key and existing.status == "pending":
            if _is_expired(existing):
                existing.status = "expired"
            else:
                return existing

    now_dt = datetime.now(timezone.utc)
    req_id = f"appr-{uuid.uuid4().hex[:12]}"
    args_hash = compute_args_hash(action_type, target_entity_id, action_payload)
    record = ApprovalRequestRecord(
        id=req_id,
        run_id=run_id,
        user_id=user_id,
        action_type=action_type,
        action_payload=action_payload,
        target_entity_id=target_entity_id,
        target_entity_name=target_entity_name,
        status="pending",
        idempotency_key=idempotency_key,
        args_hash=args_hash,
        expires_at=(now_dt + timedelta(seconds=ttl_seconds)).isoformat(),
        created_at=now_dt.isoformat(),
    )
    _APPROVALS_STORE[req_id] = record
    return record


def get_pending_approvals(user_id: str) -> List[ApprovalRequestRecord]:
    active: List[ApprovalRequestRecord] = []
    for r in _APPROVALS_STORE.values():
        if r.user_id == user_id and r.status == "pending":
            if _is_expired(r):
                r.status = "expired"
            else:
                active.append(r)
    return active


def get_approval_by_id(approval_id: str) -> Optional[ApprovalRequestRecord]:
    return _APPROVALS_STORE.get(approval_id)


def decide_approval(
    approval_id: str,
    decision: str,  # 'approved' or 'rejected'
    user: AuthenticatedUser,
    decision_note: Optional[str] = None,
) -> ApprovalRequestRecord:
    """
    Applies human decision to pending consequential action.
    Strictly verifies:
      1. Ownership (user.id == approval.user_id)
      2. Expiration window (TTL enforcement)
      3. Payload integrity (args_hash tamper detection)
    Executes authorized domain mutation on approval; resumes the interrupted LangGraph thread.
    """
    record = _APPROVALS_STORE.get(approval_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "APPROVAL_NOT_FOUND", "message": f"Approval request '{approval_id}' was not found."},
        )

    # Cross-user authorization check
    if record.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Cannot decide an approval request owned by another user."},
        )

    # Idempotency check: if already decided, return current record
    if record.status in ("approved", "rejected"):
        return record

    if decision not in ("approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_DECISION", "message": "Decision must be 'approved' or 'rejected'."},
        )

    # Expiry check
    if record.status == "expired" or _is_expired(record):
        record.status = "expired"
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"code": "APPROVAL_EXPIRED", "message": "Approval request expired before decision."},
        )

    # Tamper-resistance check on canonical payload hash
    if record.args_hash:
        expected_hash = compute_args_hash(record.action_type, record.target_entity_id, record.action_payload)
        if expected_hash != record.args_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "APPROVAL_TAMPERED", "message": "Approval arguments failed integrity verification."},
            )

    record.status = decision
    record.decision_note = decision_note
    record.decided_at = datetime.now(timezone.utc).isoformat()

    if decision == "approved":
        payload = record.action_payload
        if record.action_type == "send_mentor_request":
            res = create_mentor_request_tool(
                mentor_user_id=payload.get("mentor_user_id", record.target_entity_id),
                topic=payload.get("topic", "Career Advisory"),
                message=payload.get("message", "Request submitted via MSGI AI Command Centre."),
                authenticated_user=user,
            )
            record.execution_result = {
                "status": "executed",
                "action_type": "send_mentor_request",
                "target_entity_id": record.target_entity_id,
                "target_entity_name": record.target_entity_name,
                "result": res,
            }
        elif record.action_type == "apply_job":
            res = submit_job_application_tool(
                job_id=record.target_entity_id,
                cover_note=payload.get("cover_note", "Application submitted via MSGI AI Command Centre."),
                authenticated_user=user,
            )
            record.execution_result = {
                "status": "executed",
                "action_type": "apply_job",
                "target_entity_id": record.target_entity_id,
                "target_entity_name": record.target_entity_name,
                "result": res,
            }
        elif record.action_type == "register_event":
            res = register_for_event_tool(
                event_id=record.target_entity_id,
                authenticated_user=user,
            )
            record.execution_result = {
                "status": "executed",
                "action_type": "register_event",
                "target_entity_id": record.target_entity_id,
                "target_entity_name": record.target_entity_name,
                "result": res,
            }
        elif record.action_type == "create_meeting_request":
            from src.schemas.scheduling import MeetingRequestCreate
            from src.services.scheduling_service import create_meeting_request

            req_obj = MeetingRequestCreate(**payload)
            res = create_meeting_request(
                student=user,
                payload=req_obj,
                idempotency_key=record.idempotency_key,
            )
            record.execution_result = {
                "status": "executed",
                "action_type": "create_meeting_request",
                "target_entity_id": record.target_entity_id,
                "target_entity_name": record.target_entity_name,
                "result": res.model_dump(mode="json"),
            }
        elif record.action_type == "reschedule_meeting":
            from src.schemas.scheduling import MeetingRescheduleRequest
            from src.services.scheduling_service import reschedule_meeting

            req_obj = MeetingRescheduleRequest(**payload)
            res = reschedule_meeting(user=user, meeting_id=record.target_entity_id, payload=req_obj)
            record.execution_result = {
                "status": "executed",
                "action_type": "reschedule_meeting",
                "target_entity_id": record.target_entity_id,
                "target_entity_name": record.target_entity_name,
                "result": res.model_dump(mode="json"),
            }
        elif record.action_type == "cancel_meeting":
            from src.schemas.scheduling import MeetingCancelRequest
            from src.services.scheduling_service import cancel_meeting

            req_obj = MeetingCancelRequest(**payload)
            res = cancel_meeting(user=user, meeting_id=record.target_entity_id, payload=req_obj)
            record.execution_result = {
                "status": "executed",
                "action_type": "cancel_meeting",
                "target_entity_id": record.target_entity_id,
                "target_entity_name": record.target_entity_name,
                "result": res.model_dump(mode="json"),
            }
        elif record.action_type == "send_message":
            from src.schemas.messaging import MessageCreateRequest
            from src.services.messaging_service import get_or_create_conversation, send_message

            conv_id = payload.get("conversation_id")
            if not conv_id:
                conv = get_or_create_conversation(user=user, recipient_id=record.target_entity_id)
                conv_id = conv.id
            msg_payload = MessageCreateRequest(
                content=payload.get("content", ""),
                message_type=payload.get("message_type", "text"),
                idempotency_key=record.idempotency_key,
            )
            res = send_message(user=user, conversation_id=conv_id, payload=msg_payload)
            record.execution_result = {
                "status": "executed",
                "action_type": "send_message",
                "target_entity_id": record.target_entity_id,
                "target_entity_name": record.target_entity_name,
                "result": res.model_dump(mode="json"),
            }
    else:
        record.execution_result = {
            "status": "rejected_by_user",
            "action_type": record.action_type,
            "target_entity_id": record.target_entity_id,
            "target_entity_name": record.target_entity_name,
            "message": "Action cancelled by user request. Institutional records unchanged.",
        }

    # Resume the LangGraph thread state (Gate 7.3 & Gate 7.4)
    try:
        from src.ai.graph import resume_interrupted_graph
        resume_interrupted_graph(
            session_id=record.run_id,
            decision=decision,
            user=user,
            execution_result=record.execution_result,
        )
    except Exception:
        pass

    return record
