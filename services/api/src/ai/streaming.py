"""
MSGI One — Real-Time SSE Streaming Engine for AI Command Centre (Phase 8)
Emits canonical Server-Sent Events:
  run.started, agent.status, tool.started, tool.completed,
  approval.required, response.delta, citation, usage, response.completed, run.error
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from src.ai.graph import run_command_centre
from src.ai.multi_provider import (
    ProviderCompletionResult,
    UsageLedgerRecord,
    execute_with_failover,
    record_usage_ledger,
)
from src.ai.vault import list_provider_configs
from src.core.dependencies import AuthenticatedUser


def format_sse_event(event_type: str, payload: Dict[str, Any]) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload, default=str)}\n\n"


async def stream_command_centre_events(
    *,
    prompt: str,
    user: AuthenticatedUser,
    session_id: Optional[str] = None,
    preferred_config_id: Optional[str] = None,
    chunk_size: int = 8,
) -> AsyncIterator[str]:
    """
    Executes the LangGraph Command Centre pipeline and streams structured
    real-time SSE events suitable for mobile/web incremental rendering.
    """
    sid = session_id or f"sess-{uuid.uuid4().hex[:12]}"
    yield format_sse_event("run.started", {"session_id": sid, "user_id": user.id})
    yield format_sse_event("agent.status", {"agent": "supervisor", "status": "routing", "session_id": sid})

    try:
        state = await asyncio.to_thread(
            run_command_centre,
            prompt=prompt,
            user=user,
            session_id=sid,
        )
    except Exception as exc:
        yield format_sse_event("run.error", {"session_id": sid, "code": "GRAPH_EXECUTION_ERROR", "message": str(exc)})
        return

    intent = state.get("intent", "orchestrator")
    yield format_sse_event(
        "agent.status",
        {"agent": "supervisor", "status": "routed", "intent": intent, "run_status": state.get("status")},
    )

    for log in state.get("action_logs") or []:
        agent_name = log.get("agent", "agent")
        action_name = log.get("action", "tool_call")
        yield format_sse_event("tool.started", {"agent": agent_name, "tool": action_name})
        yield format_sse_event("tool.completed", {"agent": agent_name, "tool": action_name, "details": log})

    # Emit verified citations
    for cit in state.get("validated_citations") or []:
        yield format_sse_event("citation", {"citation_id": cit})

    # If Rule 15 interrupted execution for human approval, surface event explicitly
    pending = state.get("pending_approval")
    if state.get("status") == "interrupted" and pending:
        yield format_sse_event("approval.required", {"session_id": sid, "approval": pending})

    summary_text = state.get("final_summary") or "Request processed."
    active_provider = "deterministic"
    active_model = "deterministic-rule-engine"
    total_tokens = int(state.get("total_tokens") or 0)
    estimated_cost = 0.0

    # Optionally refine wording via configured vault provider when enabled & not rejected/interrupted
    enabled_configs = list_provider_configs(include_disabled=False)
    if enabled_configs and state.get("status") == "completed":
        try:
            completion: ProviderCompletionResult = await execute_with_failover(
                prompt=(
                    f"User request: {prompt}\n"
                    f"Verified grounded facts: {summary_text}\n"
                    "Rewrite concisely preserving all verified facts without inventing new names or metrics."
                ),
                system_instruction="You are the MSGI One institutional response synthesizer. Preserve verified facts only.",
                user_id=user.id,
                run_id=sid,
                preferred_config_id=preferred_config_id,
            )
            if completion.content.strip():
                summary_text = completion.content.strip()
                active_provider = completion.provider
                active_model = completion.model_id
                total_tokens = completion.total_tokens or total_tokens
                estimated_cost = completion.estimated_cost_usd
        except Exception:
            # Deterministic verified summary remains intact on upstream provider failure
            pass
    else:
        record_usage_ledger(
            UsageLedgerRecord(
                provider="deterministic",
                model_id="deterministic-rule-engine",
                user_id=user.id,
                run_id=sid,
                prompt_tokens=total_tokens // 2,
                output_tokens=total_tokens - (total_tokens // 2),
                total_tokens=total_tokens,
                estimated_cost_usd=0.0,
                latency_ms=int(state.get("latency_ms") or 0),
                status="completed",
            )
        )

    words = summary_text.split(" ")
    for i in range(0, len(words), max(chunk_size, 1)):
        segment = " ".join(words[i : i + max(chunk_size, 1)])
        if i > 0:
            segment = " " + segment
        yield format_sse_event("response.delta", {"delta": segment, "index": i // max(chunk_size, 1)})
        await asyncio.sleep(0)

    yield format_sse_event(
        "usage",
        {
            "provider": active_provider,
            "model_id": active_model,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost,
            "latency_ms": int(state.get("latency_ms") or 0),
        },
    )

    yield format_sse_event(
        "response.completed",
        {
            "session_id": sid,
            "status": state.get("status", "completed"),
            "intent": intent,
            "final_summary": summary_text,
            "pending_approval": pending,
            "skill_gap": state.get("skill_gap"),
            "learning_roadmap": state.get("learning_roadmap"),
            "recommended_mentors": state.get("recommended_mentors"),
            "recommended_jobs": state.get("recommended_jobs"),
            "recommended_events": state.get("recommended_events"),
            "recommended_slots": state.get("recommended_slots"),
            "drafted_message": state.get("drafted_message"),
            "admin_summary": state.get("admin_summary"),
            "alumni_matches": state.get("alumni_matches"),
            "validated_citations": state.get("validated_citations", []),
            "evidence": state.get("evidence", []),
            "action_logs": state.get("action_logs", []),
            "latency_ms": int(state.get("latency_ms") or 0),
            "total_tokens": total_tokens,
        },
    )
