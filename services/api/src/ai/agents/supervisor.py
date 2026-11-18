"""
MSGI One — Master Orchestrator (Supervisor Node)
Routes user queries to specialized domain agents or triggers safe refusals.
Principles: Evans Bounded Contexts & Silberschatz Authorization Controls.
"""

from typing import Dict, Any
from src.ai.state import CommandCentreState
from src.ai.provider import provider


def supervisor_node(state: CommandCentreState) -> CommandCentreState:
    prompt = state.get("prompt", "")
    analysis = provider.classify_intent_and_entities(prompt)

    state["intent"] = analysis["intent"]
    state["safety_refusal"] = analysis.get("reason")
    if analysis.get("target_role"):
        state["target_role"] = analysis["target_role"]

    action_log = {
        "agent": "supervisor",
        "action": "classify_intent",
        "intent": analysis["intent"],
        "safety_check": analysis.get("safety_check", "PASS"),
    }
    state.setdefault("action_logs", []).append(action_log)

    if analysis["intent"] == "rejected":
        state["status"] = "rejected"
        state["final_summary"] = analysis.get("reason", "Query rejected by security policies.")
    else:
        state["status"] = "running"

    return state
