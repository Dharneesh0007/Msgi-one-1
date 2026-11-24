"""
MSGI One — AI Command Centre API Router
Endpoints:
  POST /api/v1/ai/chat — Execute goal-driven multi-agent query
  POST /api/v1/ai/workflows — Run multi-agent orchestrator workflow
  GET  /api/v1/ai/workflows/{id} — Retrieve workflow state
  GET  /api/v1/ai/approvals/pending — List user's pending approval requests
  POST /api/v1/ai/approvals/{id}/decision — Human decision on consequential action
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    ApprovalItem,
    ApprovalDecisionRequest,
)
from src.ai.graph import run_command_centre, _AGENT_RUNS_STORE
from src.ai.streaming import stream_command_centre_events
from src.ai.approvals import (
    get_pending_approvals,
    get_approval_by_id,
    decide_approval,
)

router = APIRouter(prefix="/ai", tags=["AI Command Centre"])


@router.post(
    "/chat",
    response_model=StandardEnvelope[AIChatResponse],
    summary="Chat with MSGI AI Command Centre",
    description="Processes goal-driven queries through LangGraph master orchestrator and specialized domain agents.",
)
def chat_with_command_centre(
    request: AIChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[AIChatResponse]:
    state = run_command_centre(
        prompt=request.prompt,
        user=current_user,
        session_id=request.session_id,
    )

    pending_obj = None
    if state.get("pending_approval"):
        pending_obj = ApprovalItem(**state["pending_approval"])

    data = AIChatResponse(
        session_id=state.get("session_id", "session-unknown"),
        status=state.get("status", "completed"),
        intent=state.get("intent", "orchestrator"),
        target_role=state.get("target_role"),
        skill_gap=state.get("skill_gap"),
        learning_roadmap=state.get("learning_roadmap"),
        recommended_mentors=state.get("recommended_mentors"),
        recommended_jobs=state.get("recommended_jobs"),
        recommended_events=state.get("recommended_events"),
        alumni_matches=state.get("alumni_matches"),
        recommended_slots=state.get("recommended_slots"),
        drafted_message=state.get("drafted_message"),
        admin_summary=state.get("admin_summary"),
        pending_approval=pending_obj,
        final_summary=state.get("final_summary", ""),
        evidence=state.get("evidence", []),
        action_logs=state.get("action_logs", []),
        latency_ms=state.get("latency_ms", 0),
        total_tokens=state.get("total_tokens", 0),
    )

    return StandardEnvelope[AIChatResponse](
        status="success",
        data=data,
        timestamp=datetime.now(timezone.utc),
        meta={"execution_mode": "sandboxed_deterministic", "engine": "LangGraph 1.2"},
    )


@router.post(
    "/chat/stream",
    summary="Stream Real-Time AI Command Centre Response (SSE)",
    description="Streams LangGraph status, tool telemetry, approval requests, tokens, citations, and usage over Server-Sent Events.",
)
async def stream_chat_with_command_centre(
    request: AIChatRequest,
    provider_config_id: Optional[str] = Query(default=None, description="Optional override provider config ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return StreamingResponse(
        stream_command_centre_events(
            prompt=request.prompt,
            user=current_user,
            session_id=request.session_id,
            preferred_config_id=provider_config_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/workflows",
    response_model=StandardEnvelope[AIChatResponse],
    summary="Trigger Multi-Agent Career Workflow",
    description="Executes full end-to-end multi-agent orchestration across Alumni, Career, Mentors, and Events.",
)
def trigger_workflow(
    request: AIChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[AIChatResponse]:
    return chat_with_command_centre(request=request, current_user=current_user)


@router.get(
    "/workflows/{session_id}",
    response_model=StandardEnvelope[dict],
    summary="Get Workflow Run Status",
    description="Retrieves the state and audit summary of a previously triggered agent session.",
)
def get_workflow_status(
    session_id: str = Path(..., description="Agent session ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[dict]:
    run = _AGENT_RUNS_STORE.get(session_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "WORKFLOW_NOT_FOUND", "message": f"Session '{session_id}' not found."},
        )
    if run.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Cannot access a workflow session owned by another user."},
        )
    return StandardEnvelope[dict](
        status="success",
        data=run,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/approvals/pending",
    response_model=StandardEnvelope[List[ApprovalItem]],
    summary="List Pending Consequential Actions",
    description="Returns all actions waiting for explicit human confirmation under Rule 15.",
)
def list_pending_approvals(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[ApprovalItem]]:
    items = get_pending_approvals(user_id=current_user.id)
    out = [ApprovalItem(**r.model_dump()) for r in items]
    return StandardEnvelope[List[ApprovalItem]](
        status="success",
        data=out,
        timestamp=datetime.now(timezone.utc),
        meta={"pending_count": len(out)},
    )


@router.post(
    "/approvals/{approval_id}/decision",
    response_model=StandardEnvelope[ApprovalItem],
    summary="Approve or Reject Consequential Action",
    description="Submits human authorization decision on an interrupted agent action.",
)
def submit_approval_decision(
    approval_id: str = Path(..., description="Approval request ID"),
    request: ApprovalDecisionRequest = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[ApprovalItem]:
    record = decide_approval(
        approval_id=approval_id,
        decision=request.decision,
        user=current_user,
        decision_note=request.decision_note,
    )
    return StandardEnvelope[ApprovalItem](
        status="success",
        data=ApprovalItem(**record.model_dump()),
        timestamp=datetime.now(timezone.utc),
        meta={"decision": request.decision},
    )
