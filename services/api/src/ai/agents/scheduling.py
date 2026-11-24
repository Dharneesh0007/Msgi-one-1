"""
MSGI One — Scheduling Agent Node (Phase 8)
Integrates authorized Phase 5 scheduling tools with Rule 15 HITL gates.
"""

from typing import Any, Dict, List
from src.ai.approvals import create_approval_request
from src.ai.provider import provider
from src.ai.state import CommandCentreState
from src.core.dependencies import AuthenticatedUser
from src.services.scheduling_service import (
    get_alumni_availability_tool,
    list_my_meetings,
    suggest_meeting_slots_tool,
)


def scheduling_agent_node(state: CommandCentreState) -> CommandCentreState:
    prompt = state.get("prompt", "")
    p_lower = prompt.lower()
    user_id = state.get("user_id", "user-student-001")
    roles = state.get("user_roles", ["student"])
    user = AuthenticatedUser(
        id=user_id,
        email=state.get("user_email", "student@example.msgi.edu"),
        first_name="Student",
        last_name="User",
        roles=roles,
        is_verified=True,
    )

    alumni_id = "user-ananya-002" if "ananya" in p_lower else "user-kenji-001"
    alumni_name = "Ananya Sharma" if "ananya" in p_lower else "Kenji Sato"

    availability = get_alumni_availability_tool(alumni_id=alumni_id, days_ahead=7)
    slots = suggest_meeting_slots_tool(alumni_id=alumni_id, duration_minutes=30, max_suggestions=3)
    state["recommended_slots"] = slots

    state.setdefault("evidence", []).append({
        "source": "MSGI Mentorship Scheduling Engine",
        "alumni_id": alumni_id,
        "timezone": availability.get("timezone"),
        "available_slots_count": len(slots),
    })
    state.setdefault("action_logs", []).append({
        "agent": "scheduling_agent",
        "action": "suggest_meeting_slots",
        "alumni_id": alumni_id,
        "slots_found": len(slots),
    })

    analysis = provider.classify_intent_and_entities(prompt)
    action_type = analysis.get("action_type")
    if analysis.get("requires_human_approval") and action_type in (
        "create_meeting_request",
        "reschedule_meeting",
        "cancel_meeting",
    ):
        if action_type == "create_meeting_request":
            proposed = [
                {"start_utc": s["start_utc"], "end_utc": s["end_utc"]}
                for s in slots[:3]
            ]
            approval = create_approval_request(
                run_id=state.get("session_id", "session-default"),
                user_id=user_id,
                action_type="create_meeting_request",
                action_payload={
                    "alumni_id": alumni_id,
                    "title": f"Advisory Session with {alumni_name}",
                    "purpose": prompt[:400],
                    "duration_minutes": 30,
                    "student_timezone": "UTC",
                    "proposed_slots": proposed,
                },
                target_entity_id=alumni_id,
                target_entity_name=f"Meeting Request with {alumni_name}",
            )
        else:
            meetings = list_my_meetings(user)
            target_meeting_id = meetings[0].id if meetings else "meeting-latest"
            payload: Dict[str, Any] = (
                {
                    "new_start_utc": slots[0]["start_utc"],
                    "new_end_utc": slots[0]["end_utc"],
                    "reason": "Rescheduled via AI Command Centre",
                }
                if action_type == "reschedule_meeting" and slots
                else {"reason": "Cancelled via AI Command Centre decision"}
            )
            approval = create_approval_request(
                run_id=state.get("session_id", "session-default"),
                user_id=user_id,
                action_type=action_type,
                action_payload=payload,
                target_entity_id=target_meeting_id,
                target_entity_name=f"{action_type.replace('_', ' ').title()} ({target_meeting_id})",
            )

        state["pending_approval"] = approval.model_dump()
        state["status"] = "interrupted"
        state.setdefault("action_logs", []).append({
            "agent": "scheduling_agent",
            "action": "stage_approval_request",
            "action_type": action_type,
            "approval_id": approval.id,
        })

    return state
