"""
MSGI One — AI Command Centre State Definition
Principles: Kleppmann Data Flow & LangGraph Typed State Contracts.
Gate 7.3 & Gate 7.4 Typed Architecture.
"""

from typing import TypedDict, Any, Optional, List, Dict


class CommandCentreState(TypedDict, total=False):
    # 1. Trusted User Context & Identity Boundaries
    session_id: str
    user_id: str
    user_roles: List[str]
    user_email: str
    thread_owner_id: str  # For multi-tenant checkpoint isolation (Gate 7.4)

    # 2. User Query & Intent Classification
    prompt: str
    intent: str  # 'alumni', 'career', 'mentorship', 'events', 'orchestrator', 'rejected'
    target_role: Optional[str]
    extracted_skills: List[str]

    # 3. Domain Outputs
    skill_gap: Optional[Dict[str, Any]]
    learning_roadmap: Optional[List[Dict[str, Any]]]
    recommended_mentors: Optional[List[Dict[str, Any]]]
    recommended_jobs: Optional[List[Dict[str, Any]]]
    recommended_events: Optional[List[Dict[str, Any]]]
    alumni_matches: Optional[List[Dict[str, Any]]]

    # 4. Human-In-The-Loop Approval Gates (Rule 15)
    pending_approval: Optional[Dict[str, Any]]
    approval_status: Optional[str]  # 'pending', 'approved', 'rejected'

    # 5. RAG Retrieval & Citation Grounding (Gate 7.6)
    retrieved_docs: Optional[List[Dict[str, Any]]]
    validated_citations: List[str]

    # 6. Audit & Observability
    completed_actions: List[Dict[str, Any]]
    action_logs: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    final_summary: str

    # 7. Execution State & Metrics
    status: str  # 'running', 'interrupted', 'completed', 'failed', 'rejected'
    safety_refusal: Optional[str]
    error: Optional[str]
    total_tokens: int
    latency_ms: int
