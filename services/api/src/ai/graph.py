"""
MSGI One — LangGraph Master Orchestrator Graph
Assembles Supervisor, Domain Agents, Synthesizer, and Checkpointer.
Principles: Kleppmann Fault Tolerance & Pressman Process Management.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.ai.state import CommandCentreState
from src.ai.agents.supervisor import supervisor_node
from src.ai.agents.alumni import alumni_agent_node
from src.ai.agents.career import career_agent_node
from src.ai.agents.learning import learning_agent_node
from src.ai.agents.mentorship import mentorship_agent_node
from src.ai.agents.events import events_agent_node
from src.core.dependencies import AuthenticatedUser


# In-memory audit store for agent runs (conforming to public.agent_runs)
_AGENT_RUNS_STORE: Dict[str, Dict[str, Any]] = {}


def synthesizer_node(state: CommandCentreState) -> CommandCentreState:
    """
    Synthesizes domain outputs into a structured executive brief grounded in verified evidence.
    """
    if state.get("status") == "interrupted":
        pending = state.get("pending_approval") or {}
        state["final_summary"] = (
            f"Action Pending Human Approval: An action to '{pending.get('action_type')}' for "
            f"'{pending.get('target_entity_name')}' has been prepared. Per MSGI Safety Rule 15, "
            f"please confirm approval before this action is executed."
        )
        return state

    parts: List[str] = []

    # 1. Career & Skill Gap
    gap = state.get("skill_gap")
    if gap:
        parts.append(
            f"Career Analysis for {gap['target_role']}: Current match is {gap['match_percentage']}%. "
            f"Identified {gap['missing_skills_count']} competency gaps to target."
        )

    # 2. Learning Roadmap
    roadmap = state.get("learning_roadmap")
    if roadmap:
        parts.append(
            f"Learning Path: Recommended {len(roadmap)} sequenced course(s), starting with '{roadmap[0]['course_title']}' ({roadmap[0]['provider']})."
        )

    # 3. Mentors
    mentors = state.get("recommended_mentors")
    if mentors:
        m_names = ", ".join(m.get("full_name", "") for m in mentors[:2])
        parts.append(f"Recommended Mentor(s): {m_names}.")

    # 4. Jobs
    jobs = state.get("recommended_jobs")
    if jobs:
        j_titles = ", ".join(j.get("title", "") for j in jobs[:2])
        parts.append(f"Matching Opportunity(s): {j_titles}.")

    # 5. Events
    events = state.get("recommended_events")
    if events:
        e_titles = ", ".join(e.get("title", "") for e in events[:2])
        parts.append(f"Upcoming Event(s): {e_titles}.")

    # 6. Alumni
    alumni = state.get("alumni_matches")
    if alumni:
        a_names = ", ".join(a.get("full_name", "") for a in alumni[:2])
        parts.append(f"Alumni Network Match(es): {a_names}.")

    if not parts:
        state["final_summary"] = "Your request was processed successfully. No immediate matching records were found."
    else:
        state["final_summary"] = " ".join(parts)

    state["status"] = "completed"
    return state


def route_supervisor(state: CommandCentreState) -> str:
    intent = state.get("intent", "orchestrator")
    if intent == "rejected":
        return END
    if intent == "alumni":
        return "alumni_agent"
    if intent == "career":
        return "career_agent"
    if intent == "mentorship":
        return "mentorship_agent"
    if intent == "events":
        return "events_agent"
    # Default: multi-agent orchestrator
    return "career_agent"


def build_command_centre_graph():
    builder = StateGraph(CommandCentreState)

    # Add Nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("alumni_agent", alumni_agent_node)
    builder.add_node("career_agent", career_agent_node)
    builder.add_node("learning_agent", learning_agent_node)
    builder.add_node("mentorship_agent", mentorship_agent_node)
    builder.add_node("events_agent", events_agent_node)
    builder.add_node("synthesizer", synthesizer_node)

    # Define Workflow Edges
    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            END: END,
            "alumni_agent": "alumni_agent",
            "career_agent": "career_agent",
            "mentorship_agent": "mentorship_agent",
            "events_agent": "events_agent",
        },
    )

    # Alumni Branch
    builder.add_edge("alumni_agent", "synthesizer")

    # Career Branch (Career -> Learning -> Synthesizer or Orchestrator cascade)
    def route_after_career(state: CommandCentreState) -> str:
        if state.get("status") == "interrupted":
            return "synthesizer"
        return "learning_agent"

    builder.add_conditional_edges("career_agent", route_after_career, {"synthesizer": "synthesizer", "learning_agent": "learning_agent"})

    def route_after_learning(state: CommandCentreState) -> str:
        intent = state.get("intent")
        if intent == "orchestrator":
            return "mentorship_agent"
        return "synthesizer"

    builder.add_conditional_edges("learning_agent", route_after_learning, {"mentorship_agent": "mentorship_agent", "synthesizer": "synthesizer"})

    # Mentorship Branch
    def route_after_mentorship(state: CommandCentreState) -> str:
        if state.get("status") == "interrupted":
            return "synthesizer"
        if state.get("intent") == "orchestrator":
            return "alumni_agent"
        return "synthesizer"

    builder.add_conditional_edges("mentorship_agent", route_after_mentorship, {"synthesizer": "synthesizer", "alumni_agent": "alumni_agent"})

    # Events Branch
    builder.add_edge("events_agent", "synthesizer")

    # Synthesis to End
    builder.add_edge("synthesizer", END)

    # Compile with MemorySaver checkpointer
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


# Global compiled graph
command_centre_graph = build_command_centre_graph()


def run_command_centre(
    prompt: str,
    user: AuthenticatedUser,
    session_id: Optional[str] = None,
) -> CommandCentreState:
    start_time = time.time()
    sid = session_id or f"sess-{uuid.uuid4().hex[:12]}"

    initial_state: CommandCentreState = {
        "session_id": sid,
        "user_id": user.id,
        "user_roles": user.roles,
        "user_email": user.email,
        "prompt": prompt,
        "status": "running",
        "action_logs": [],
        "completed_actions": [],
        "evidence": [],
        "total_tokens": max(len(prompt.split()) * 4, 12),
        "latency_ms": 0,
    }

    config = {"configurable": {"thread_id": sid}}
    result_state = command_centre_graph.invoke(initial_state, config=config)

    elapsed_ms = int((time.time() - start_time) * 1000)
    result_state["latency_ms"] = elapsed_ms

    # Audit log in-memory
    _AGENT_RUNS_STORE[sid] = {
        "id": sid,
        "user_id": user.id,
        "prompt_summary": prompt[:100],
        "status": result_state.get("status", "completed"),
        "latency_ms": elapsed_ms,
        "tokens": result_state.get("total_tokens", 0),
        "final_summary": result_state.get("final_summary", ""),
    }

    return result_state
