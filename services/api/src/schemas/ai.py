"""
MSGI One — AI Command Centre Request & Response Schemas
Principles: Typed Contracts (Pydantic v2) matching packages/contracts/types.ts.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="User goal or natural language prompt")
    session_id: Optional[str] = Field(None, description="Optional ongoing session/thread ID")


class ApprovalItem(BaseModel):
    id: str
    run_id: str
    user_id: str
    action_type: str
    target_entity_id: str
    target_entity_name: str
    status: str
    decision_note: Optional[str] = None
    decided_at: Optional[str] = None
    created_at: str
    execution_result: Optional[Dict[str, Any]] = None


class AIChatResponse(BaseModel):
    session_id: str
    status: str  # 'completed', 'interrupted', 'rejected', 'failed'
    intent: str
    target_role: Optional[str] = None
    skill_gap: Optional[Dict[str, Any]] = None
    learning_roadmap: Optional[List[Dict[str, Any]]] = None
    recommended_mentors: Optional[List[Dict[str, Any]]] = None
    recommended_jobs: Optional[List[Dict[str, Any]]] = None
    recommended_events: Optional[List[Dict[str, Any]]] = None
    alumni_matches: Optional[List[Dict[str, Any]]] = None
    pending_approval: Optional[ApprovalItem] = None
    final_summary: str
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    action_logs: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: int = 0
    total_tokens: int = 0


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$", description="'approved' or 'rejected'")
    decision_note: Optional[str] = Field(None, max_length=500, description="Optional reasoning note")
