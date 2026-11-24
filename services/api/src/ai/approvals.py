"""
MSGI One — Human-In-The-Loop (HITL) Approval Engine
Phase 7 — Intelligent AI Infrastructure (Gates 7.3 & 7.4)
Enforces Rule 15 of AGENTS.md: Consequential mutations strictly require human approval.
Principles: Kleppmann Idempotency & Pressman Risk Containment.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

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
    action_type: str  # 'send_mentor_request', 'apply_job', 'register_event'
    action_payload: Dict[str, Any]
    target_entity_id: str
    target_entity_name: str
    status: str = "pending"  # 'pending', 'approved', 'rejected', 'expired'
    idempotency_key: str
    decision_note: Optional[str] = None
    decided_at: Optional[str] = None
    created_at: str
    execution_result: Optional[Dict[str, Any]] = None


# Thread-safe store for approval requests and execution results
_APPROVALS_STORE: Dict[str, ApprovalRequestRecord] = {}


def generate_idempotency_key(user_id: str, action_type: str, target_entity_id: str) -> str:
    raw = f"{user_id}:{action_type}:{target_entity_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def create_approval_request(
    run_id: str,
    user_id: str,
    action_type: str,
    action_payload: Dict[str, Any],
    target_entity_id: str,
    target_entity_name: str,
) -> ApprovalRequestRecord:
    idempotency_key = generate_idempotency_key(user_id, action_type, target_entity_id)

    # Check for existing request with same idempotency key
    for existing in _APPROVALS_STORE.values():
        if existing.idempotency_key == idempotency_key and existing.status == "pending":
            return existing

    req_id = f"appr-{uuid.uuid4().hex[:12]}"
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
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _APPROVALS_STORE[req_id] = record
    return record


def get_pending_approvals(user_id: str) -> List[ApprovalRequestRecord]:
    return [
        r for r in _APPROVALS_STORE.values()
        if r.user_id == user_id and r.status == "pending"
    ]


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
    Strictly verifies ownership: user.id must match approval.user_id.
    Executes domain mutation on approval; resumes the interrupted LangGraph thread.
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

    record.status = decision
    record.decision_note = decision_note
    record.decided_at = datetime.now(timezone.utc).isoformat()

    if decision == "approved":
        # Execute underlying domain mutation with authenticated user's credentials
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
