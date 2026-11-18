"""
MSGI One — AI Command Centre State Definition
Principles: Kleppmann Data Flow & LangGraph Typed State Contracts.
"""

from typing import TypedDict, Any, Optional, List, Dict


class CommandCentreState(TypedDict, total=False):
    # User Context & Identity
    session_id: str
    user_id: str
    user_roles: List[str]
    user_email: str

    # User Query & Intent Classification
    prompt: str
    intent: str  # 'alumni', 'career', 'mentorship', 'events', 'orchestrator', 'rejected'
    target_role: Optional[str]
    extracted_skills: List[str]

    # Domain Outputs
    skill_gap: Optional[Dict[str, Any]]
    learning_roadmap: Optional[List[Dict[str, Any]]]
    recommended_mentors: Optional[List[Dict[str, Any]]]
    recommended_jobs: Optional[List[Dict[str, Any]]]
    recommended_events: Optional[List[Dict[str, Any]]]
    alumni_matches: Optional[List[Dict[str, Any]]]

    # Human-In-The-Loop Approval Gates
    pending_approval: Optional[Dict[str, Any]]
    approval_status: Optional[str]  # 'pending', 'approved', 'rejected'

    # Audit & Observability
    completed_actions: List[Dict[str, Any]]
    action_logs: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    final_summary: str

    # Execution State
    status: str  # 'running', 'interrupted', 'completed', 'failed', 'rejected'
    safety_refusal: Optional[str]
    error: Optional[str]
    total_tokens: int
    latency_ms: int
