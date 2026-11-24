"""
MSGI One — Conversational & Institutional Advisory Agent Node (Phase 8 Enhancement)
Handles greetings, general institutional inquiries, and open-ended mentorship/career
questions using the active primary LLM provider configured in the encrypted Admin Vault,
grounded in real institutional context without triggering hardcoded skill-gap templates.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from src.ai.multi_provider import ClassifiedProviderError, ProviderCompletionResult, execute_with_failover
from src.ai.state import CommandCentreState
from src.ai.vault import list_provider_configs
from src.services import alumni_service, mentor_service


def _run_async_coro(coro):
    """Runs an async coroutine safely from either a plain sync thread or inside an active loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result(timeout=30)


def build_institutional_context(state: CommandCentreState) -> Dict[str, Any]:
    """Assembles a concise, PII-safe institutional context snapshot from active domain stores."""
    roles = state.get("user_roles") or ["student"]
    mentors = [
        f"{m['full_name']} ({m['headline']})"
        for m in mentor_service._MENTORS_STORE
        if m.get("is_accepting_requests")
    ][:3]
    alumni_count = len(alumni_service._SYNTHETIC_ALUMNI_STORE)
    return {
        "user_role": roles[0] if roles else "student",
        "verified_alumni_count": alumni_count,
        "featured_mentors": mentors,
        "capabilities": [
            "Verified Alumni Directory & Semantic Matching",
            "MentorMatch Advisory Requests & Timezone-Aware 1:1 Meeting Scheduling",
            "CareerBridge Opportunities & Skill-Gap / Learning Roadmaps",
            "Real-Time 1:1 Direct Messaging & LiveKit Video Rooms",
            "Institutional Events & Admin Credential Verification",
        ],
    }


def _build_offline_conversational_reply(prompt: str, ctx: Dict[str, Any]) -> str:
    p_lower = prompt.lower().strip()
    role_label = ctx.get("user_role", "student")
    mentors = ctx.get("featured_mentors") or []
    mentor_hint = f" Active verified mentors include {'; '.join(mentors[:2])}." if mentors else ""

    if any(g in p_lower for g in ("hi", "hii", "hiii", "hello", "hey", "howdy", "morning", "afternoon", "evening")):
        return (
            f"Hello! Welcome to the MSGI One AI Command Centre ({role_label} workspace). "
            "I can help you discover verified alumni, prepare mentorship advice or meeting requests, "
            "explore career opportunities, analyze competency gaps for specific roles, or draft messages."
            f"{mentor_hint} What would you like to work on today?"
        )

    if any(t in p_lower for t in ("thank", "thanks")):
        return "You're welcome! Let me know whenever you'd like help connecting with MSGI alumni, scheduling mentorship sessions, or exploring career pathways."

    return (
        "I'm ready to help with institutional guidance across MSGI One's Alumni Network, MentorMatch advisory, "
        "CareerBridge opportunities, meeting scheduling, and event discovery."
        f"{mentor_hint} Feel free to ask a specific mentorship question, name a target career role, or ask me to find alumni or schedule a session."
    )


def conversational_agent_node(state: CommandCentreState) -> CommandCentreState:
    prompt = (state.get("prompt") or "").strip()
    user_id = state.get("user_id", "user-student-001")
    session_id = state.get("session_id", "session-default")
    ctx = build_institutional_context(state)

    system_instruction = (
        "You are the MSGI One Institutional AI Assistant serving verified students, alumni, faculty, recruiters, and admins. "
        "Respond naturally, warmly, and concisely to conversational greetings and general mentorship/career advice questions. "
        "Stay strictly grounded in this verified institutional context and NEVER invent alumni names, job listings, or statistics:\n"
        f"- Active User Role: {ctx['user_role']}\n"
        f"- Verified Institutional Alumni Records: {ctx['verified_alumni_count']}\n"
        f"- Featured Accepting Mentors: {', '.join(ctx['featured_mentors']) or 'None currently listed'}\n"
        f"- Supported Platform Modules: {', '.join(ctx['capabilities'])}\n"
        "Per MSGI Rule 15, do not claim to have sent messages, applied to jobs, or booked meetings without explicit user approval."
    )

    enabled_providers = list_provider_configs(include_disabled=False)
    reply_text: Optional[str] = None
    provider_used = "deterministic"
    model_used = "deterministic-conversational"
    total_tokens = int(state.get("total_tokens") or 0)
    estimated_cost = 0.0

    if enabled_providers:
        try:
            completion: ProviderCompletionResult = _run_async_coro(
                execute_with_failover(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    user_id=user_id,
                    run_id=session_id,
                )
            )
            if completion and completion.content.strip():
                reply_text = completion.content.strip()
                provider_used = completion.provider
                model_used = completion.model_id
                total_tokens = completion.total_tokens or total_tokens
                estimated_cost = completion.estimated_cost_usd
        except ClassifiedProviderError as exc:
            state.setdefault("action_logs", []).append({
                "agent": "conversational_agent",
                "action": "vault_llm_fallback",
                "error_code": exc.error_code,
            })
        except Exception as exc:
            state.setdefault("action_logs", []).append({
                "agent": "conversational_agent",
                "action": "vault_llm_fallback",
                "error": str(exc),
            })

    if not reply_text:
        reply_text = _build_offline_conversational_reply(prompt, ctx)

    state["conversational_reply"] = reply_text
    state["provider_used"] = provider_used
    state["model_used"] = model_used
    state["total_tokens"] = total_tokens
    state["estimated_cost_usd"] = estimated_cost
    state.setdefault("evidence", []).append({
        "source": f"MSGI Institutional Assistant ({provider_used}:{model_used})",
        "verified_alumni_count": ctx["verified_alumni_count"],
        "featured_mentors": ctx["featured_mentors"],
    })
    state.setdefault("action_logs", []).append({
        "agent": "conversational_agent",
        "action": "respond_conversational",
        "provider": provider_used,
        "model_id": model_used,
    })
    return state
