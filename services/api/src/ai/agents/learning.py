"""
MSGI One — Learning Roadmap Agent
Sequences educational courseware to bridge identified competency gaps.
"""

from typing import Dict, Any, List
from src.ai.state import CommandCentreState
from src.ai.tools import generate_learning_roadmap
from src.core.dependencies import AuthenticatedUser


def learning_agent_node(state: CommandCentreState) -> CommandCentreState:
    gap = state.get("skill_gap")
    missing_skills: List[str] = []

    if gap and gap.get("missing_skills"):
        missing_skills = [s["skill_name"] for s in gap["missing_skills"]]
    else:
        # Fallback missing skills for AI Engineer if no prior gap node
        missing_skills = ["PyTorch", "FastAPI", "Docker", "LangGraph", "Vector Databases"]

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

    roadmap = generate_learning_roadmap(
        missing_skills=missing_skills,
        authenticated_user=user,
    )
    state["learning_roadmap"] = roadmap

    titles = [step["course_title"] for step in roadmap]
    state.setdefault("evidence", []).append({
        "source": "Institutional Curriculum Registry",
        "total_courses": len(roadmap),
        "courses": titles,
    })
    state.setdefault("action_logs", []).append({
        "agent": "learning_agent",
        "action": "generate_learning_roadmap",
        "steps_count": len(roadmap),
        "courses": titles,
    })

    return state
