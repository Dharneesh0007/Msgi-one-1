"""
MSGI One — Institutional Admin Operations Agent Node (Phase 8)
Strict RBAC boundary: refuses non-admin users unconditionally before any domain read.
"""

from src.ai.state import CommandCentreState
from src.core.dependencies import AuthenticatedUser
from src.services.admin_service import get_admin_summary, list_pending_verifications


def admin_ops_agent_node(state: CommandCentreState) -> CommandCentreState:
    user_id = state.get("user_id", "user-student-001")
    roles = [r.lower() for r in state.get("user_roles", [])]

    if not any(r in {"admin", "faculty", "superadmin"} for r in roles):
        state["intent"] = "rejected"
        state["status"] = "rejected"
        state["safety_refusal"] = (
            "Authorization Error: Institutional administration summaries and audit queues require "
            "verified admin or faculty role authorization."
        )
        state["final_summary"] = state["safety_refusal"]
        state.setdefault("action_logs", []).append({
            "agent": "admin_ops_agent",
            "action": "rbac_denied",
            "roles": roles,
        })
        return state

    admin_user = AuthenticatedUser(
        id=user_id,
        email=state.get("user_email", "admin@example.msgi.edu"),
        first_name="Admin",
        last_name="User",
        roles=state.get("user_roles", ["admin"]),
        is_verified=True,
    )
    summary = get_admin_summary(admin=admin_user)
    verifications = list_pending_verifications(admin=admin_user)
    summary_dict = summary.model_dump()
    summary_dict["pending_verifications_sample"] = [v.id for v in verifications[:5]]

    state["admin_summary"] = summary_dict
    state.setdefault("evidence", []).append({
        "source": "Institutional Administration Control Plane",
        "pending_verifications": len(verifications),
        "total_users": summary.total_users,
    })
    state.setdefault("action_logs", []).append({
        "agent": "admin_ops_agent",
        "action": "get_admin_summary",
        "pending_verifications": len(verifications),
    })
    return state
