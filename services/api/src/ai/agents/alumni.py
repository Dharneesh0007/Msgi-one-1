"""
MSGI One — Alumni Discovery Agent
Discovers verified alumni mentors and peers filtered by industry, location, and topic.
"""

from typing import Dict, Any, List
from src.ai.state import CommandCentreState
from src.ai.tools import search_alumni_network
from src.core.dependencies import AuthenticatedUser


def alumni_agent_node(state: CommandCentreState) -> CommandCentreState:
    prompt = state.get("prompt", "").lower()
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

    country = "Japan" if ("japan" in prompt or "tokyo" in prompt) else None
    industry = "Artificial Intelligence" if ("ai" in prompt or "artificial intelligence" in prompt) else None

    results = search_alumni_network(
        industry=industry,
        country=country,
        authenticated_user=user,
    )

    items = results.get("items", [])
    state["alumni_matches"] = [
        {
            "id": a.id,
            "full_name": a.full_name,
            "company": a.current_company,
            "title": a.current_title,
            "industry": a.industry,
            "country": a.country,
            "mentor_opt_in": a.mentor_opt_in,
        }
        for a in items
    ]

    names = [a["full_name"] for a in state["alumni_matches"]]
    state.setdefault("evidence", []).append({
        "source": "Alumni Network Registry",
        "count": len(items),
        "entities": names,
    })

    state.setdefault("action_logs", []).append({
        "agent": "alumni_agent",
        "action": "search_alumni_network",
        "matches_count": len(items),
        "entities": names,
    })

    return state
