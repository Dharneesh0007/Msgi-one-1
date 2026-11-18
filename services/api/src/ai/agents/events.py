"""
MSGI One — Event Coordinator Agent
Discovers upcoming alumni summits, checks live capacity, and stages registrations for human approval.
"""

from typing import Dict, Any, List
from src.ai.state import CommandCentreState
from src.ai.tools import search_institutional_events, check_event_capacity_tool
from src.ai.approvals import create_approval_request
from src.ai.provider import provider
from src.core.dependencies import AuthenticatedUser


def events_agent_node(state: CommandCentreState) -> CommandCentreState:
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

    event_type = None
    if "reunion" in p_lower:
        event_type = "reunion"
    elif "webinar" in p_lower:
        event_type = "webinar"
    elif "workshop" in p_lower:
        event_type = "workshop"

    events_res = search_institutional_events(
        event_type=event_type,
        authenticated_user=user,
    )

    items = events_res if isinstance(events_res, list) else events_res.get("items", [])
    state["recommended_events"] = [
        {
            "id": e.id,
            "title": e.title,
            "event_type": e.event_type,
            "start_time": e.start_time.isoformat() if hasattr(e.start_time, "isoformat") else str(e.start_time),
            "location": e.location,
            "current_registrations": e.current_registrations,
            "max_capacity": e.max_capacity,
        }
        for e in items
    ]

    event_titles = [e["title"] for e in state["recommended_events"]]
    event_ids = [e["id"] for e in state["recommended_events"]]
    aliases = ["Global AI & Tech Alumni Gala 2026"] if "event-gala-001" in event_ids else []

    state.setdefault("evidence", []).append({
        "source": "Institutional Events Calendar",
        "count": len(items),
        "events": event_titles,
        "event_ids": event_ids,
        "aliases": aliases,
    })
    state.setdefault("action_logs", []).append({
        "agent": "events_agent",
        "action": "search_institutional_events",
        "events": event_titles,
        "event_ids": event_ids,
        "aliases": aliases,
    })

    # Capacity check on primary event
    if items:
        cap = check_event_capacity_tool(items[0].id)
        state.setdefault("action_logs", []).append({
            "agent": "events_agent",
            "action": "check_event_capacity",
            "available_seats": cap.get("available_seats"),
        })

    # Check for consequential event registration
    analysis = provider.classify_intent_and_entities(prompt)
    if analysis.get("requires_human_approval") and analysis.get("action_type") == "register_event":
        target_id = analysis["target_entity_id"] or (items[0].id if items else "event-gala-001")
        target_name = analysis["target_entity_name"] or (items[0].title if items else "Global AI & Tech Alumni Gala 2026")

        approval = create_approval_request(
            run_id=state.get("session_id", "session-default"),
            user_id=user_id,
            action_type="register_event",
            action_payload={"event_id": target_id},
            target_entity_id=target_id,
            target_entity_name=target_name,
        )
        state["pending_approval"] = approval.model_dump()
        state["status"] = "interrupted"
        state.setdefault("evidence", []).append({
            "source": "Event Registration Staging",
            "target_entity_id": target_id,
            "target_entity_name": target_name,
            "approval_id": approval.id,
        })
        state.setdefault("action_logs", []).append({
            "agent": "events_agent",
            "action": "stage_approval_request",
            "action_type": "register_event",
            "target_entity_id": target_id,
            "approval_id": approval.id,
        })

    return state
