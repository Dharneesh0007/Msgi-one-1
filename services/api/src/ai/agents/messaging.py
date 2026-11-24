"""
MSGI One — Messaging Advisory Agent Node (Phase 8)
Drafts institutional messages & summarizes authorized threads without ever sending silently.
"""

from src.ai.approvals import create_approval_request
from src.ai.provider import provider
from src.ai.state import CommandCentreState
from src.core.dependencies import AuthenticatedUser
from src.services.messaging_service import (
    draft_message_tool,
    list_conversations,
    summarize_permitted_conversation_tool,
)


def messaging_agent_node(state: CommandCentreState) -> CommandCentreState:
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

    recipient_id = "user-ananya-002" if "ananya" in p_lower else "user-kenji-001"
    recipient_name = "Ananya Sharma" if "ananya" in p_lower else "Kenji Sato"

    if "summarize" in p_lower or "summary" in p_lower:
        convs = list_conversations(user=user)
        if convs:
            summary_data = summarize_permitted_conversation_tool(user=user, conversation_id=convs[0].id)
            state["drafted_message"] = summary_data
            state.setdefault("evidence", []).append({
                "source": "Authorized Direct Messaging Thread",
                "conversation_id": convs[0].id,
                "message_count": summary_data.get("message_count", 0),
            })
        else:
            state["drafted_message"] = {"message_count": 0, "summary": "No active conversations found."}
        state.setdefault("action_logs", []).append({
            "agent": "messaging_agent",
            "action": "summarize_permitted_conversation",
            "conversation_count": len(convs),
        })
        return state

    draft = draft_message_tool(sender=user, recipient_id=recipient_id, purpose=prompt)
    state["drafted_message"] = draft
    state.setdefault("evidence", []).append({
        "source": "Institutional Messaging Assistant",
        "recipient_id": recipient_id,
        "recipient_name": recipient_name,
    })
    state.setdefault("action_logs", []).append({
        "agent": "messaging_agent",
        "action": "draft_message",
        "recipient_id": recipient_id,
    })

    analysis = provider.classify_intent_and_entities(prompt)
    if analysis.get("requires_human_approval") and analysis.get("action_type") == "send_message":
        approval = create_approval_request(
            run_id=state.get("session_id", "session-default"),
            user_id=user_id,
            action_type="send_message",
            action_payload={
                "recipient_id": recipient_id,
                "content": draft["draft_text"],
                "message_type": "text",
            },
            target_entity_id=recipient_id,
            target_entity_name=f"Direct Message to {recipient_name}",
        )
        state["pending_approval"] = approval.model_dump()
        state["status"] = "interrupted"
        state.setdefault("action_logs", []).append({
            "agent": "messaging_agent",
            "action": "stage_approval_request",
            "action_type": "send_message",
            "approval_id": approval.id,
        })

    return state
