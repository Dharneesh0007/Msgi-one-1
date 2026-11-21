"""
MSGI One — Declarative SQLAlchemy 2.0 AI Intelligence & Audit Models (Phase 3)
Maps to canonical Supabase PostgreSQL migration: 20261120000001_phase_3_agent_intelligence.sql.
Contains all 6 AI Intelligence & Audit Tables: CareerRoleSkills, LearningResources, StudentSkills, AgentRuns, AgentActions, ApprovalRequests.
Principles: Silberschatz et al. (Referential Integrity), Kleppmann (Immutable Action Logs), Evans (Domain Models).
"""

from datetime import datetime, timezone
from typing import List, Optional, Any
import uuid
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.models.base import Base


class CareerRoleSkill(Base):
    __tablename__ = "career_role_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    role_name: Mapped[str] = mapped_column(String(128), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    required_level: Mapped[str] = mapped_column(String(32), default="Intermediate", nullable=False)
    importance_weight: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="Technical", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("role_id", "skill_name", name="uq_career_role_skill"),
        CheckConstraint("importance_weight BETWEEN 1 AND 5", name="chk_importance_weight"),
    )


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    target_skill: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(32), default="Intermediate", nullable=False)
    duration_hours: Mapped[float] = mapped_column(Numeric(5, 1), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=4.5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False)
    proficiency_level: Mapped[str] = mapped_column(String(32), default="Beginner", nullable=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "skill_name", name="uq_student_skill"),
        CheckConstraint("years_experience >= 0", name="chk_years_experience"),
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    intent: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False, index=True)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    routing_decision: Mapped[Any] = mapped_column(JSONB, default=dict, nullable=False)
    final_response: Mapped[Any] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    actions: Mapped[List["AgentAction"]] = relationship("AgentAction", back_populates="run", cascade="all, delete-orphan")


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_input: Mapped[Any] = mapped_column(JSONB, default=dict, nullable=False)
    action_output: Mapped[Optional[Any]] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="actions")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action_payload: Mapped[Any] = mapped_column(JSONB, nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    target_entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    decision_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
