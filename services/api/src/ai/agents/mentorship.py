"""
MSGI One — Mentor Matching Agent
Ranks and matches institutional alumni mentors; stages mentorship requests for human approval.
"""

from typing import Dict, Any, List
from src.ai.state import CommandCentreState
from src.ai.tools import find_recommended_mentors
from src.ai.approvals import create_approval_request
from src.ai.provider import provider
from src.core.dependencies import AuthenticatedUser


def mentorship_agent_node(state: CommandCentreState) -> CommandCentreState:
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

    topic = "AI" if ("ai" in p_lower or "artificial intelligence" in p_lower or "machine learning" in p_lower) else None
    if "cloud" in p_lower or "architecture" in p_lower or "product" in p_lower:
        topic = "Cloud"
    country = "Japan" if ("japan" in p_lower or "tokyo" in p_lower) else None

    mentors = find_recommended_mentors(
        student_goal=state.get("target_role") or "AI Career Pathways",
        topic=topic,
        country=country,
        authenticated_user=user,
    )
    state["recommended_mentors"] = mentors

    mentor_names = [m.get("full_name") for m in mentors]
    mentor_ids = [m.get("id") or m.get("mentor_id") for m in mentors]
    state.setdefault("evidence", []).append({
        "source": "MentorMatch Advisory Directory",
        "count": len(mentors),
        "mentors": mentor_names,
        "mentor_ids": mentor_ids,
    })
    state.setdefault("action_logs", []).append({
        "agent": "mentorship_agent",
        "action": "find_recommended_mentors",
        "matches": mentor_names,
        "mentor_ids": mentor_ids,
    })

    # Check for consequential mentor request
    analysis = provider.classify_intent_and_entities(prompt)
    if analysis.get("requires_human_approval") and analysis.get("action_type") == "send_mentor_request":
        target_id = analysis["target_entity_id"] or (mentors[0]["mentor_id"] if mentors else "mentor-kenji-001")
        target_name = analysis["target_entity_name"] or (mentors[0]["full_name"] if mentors else "Kenji Sato")

        approval = create_approval_request(
            run_id=state.get("session_id", "session-default"),
            user_id=user_id,
            action_type="send_mentor_request",
            action_payload={
                "mentor_user_id": "user-kenji-001" if "kenji" in target_id else "user-ananya-002",
                "topic": "AI Career Pathways",
                "message": "Hello, I am seeking guidance on transitioning into industry as an AI Engineer.",
            },
            target_entity_id=target_id,
            target_entity_name=target_name,
        )
        state["pending_approval"] = approval.model_dump()
        state["status"] = "interrupted"
        state.setdefault("action_logs", []).append({
            "agent": "mentorship_agent",
            "action": "stage_approval_request",
            "action_type": "send_mentor_request",
            "approval_id": approval.id,
        })

    return state
