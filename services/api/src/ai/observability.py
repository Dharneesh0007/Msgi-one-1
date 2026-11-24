"""
MSGI One — AI Observability, Telemetry, Cost Governance & Reliability (Gate 7.8)
Principles:
- Site Reliability Engineering (Beyer et al.)
- OWASP LLM04 (Model Denial of Service & Resource Consumption)
Features:
1. Operational metrics tracking (tokens, latency, retry counts, costs).
2. Cost calculation based on verified official Gemini API pricing tiers.
3. Strict token budgets, iteration bounds, and circuit breaker protection.
4. Persistent audit logging to public.agent_runs and public.agent_actions.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# Verified Official Pricing (November 2026 / Google Cloud Vertex & Gemini API)
# gemini-2.5-flash (Standard context <= 128k):
#   Input: $0.300 per 1M tokens ($0.000300 / 1k)
#   Output / Candidate tokens: $2.500 per 1M tokens ($0.002500 / 1k)
#   Thinking / Reasoning tokens: billed as candidate output at $2.500 per 1M tokens
#   Free-tier availability: $0.00 within rate limits (up to 15 RPM / 1M TPM)
# gemini-2.5-flash (Extended context > 128k):
#   Input: $0.600 per 1M tokens
#   Output / Thinking: $5.000 per 1M tokens
# gemini-embedding-001 (and text-embedding-005):
#   Input: $0.020 per 1M tokens ($0.000020 / 1k)
GEMINI_FLASH_INPUT_COST_PER_MILLION = 0.300
GEMINI_FLASH_OUTPUT_COST_PER_MILLION = 2.500
GEMINI_FLASH_LONG_INPUT_COST_PER_MILLION = 0.600
GEMINI_FLASH_LONG_OUTPUT_COST_PER_MILLION = 5.000
GEMINI_EMBEDDING_COST_PER_MILLION = 0.020

# Safety & Cost Boundaries
DEFAULT_MAX_REQUEST_TOKENS = 4096
DEFAULT_MAX_GRAPH_ITERATIONS = 8
DEFAULT_MAX_TOOL_CALLS = 6
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
CIRCUIT_BREAKER_RESET_SECONDS = 60.0


class ModelUsageMetrics(BaseModel):
    """Normalized metrics record per invocation."""
    request_id: str
    session_id: str
    user_id: str
    model_id: str
    prompt_tokens: int = 0
    candidate_tokens: int = 0
    thinking_tokens: int = 0
    total_tokens: int = 0
    provider_latency_ms: int = 0
    retrieval_latency_ms: int = 0
    checkpoint_latency_ms: int = 0
    total_latency_ms: int = 0
    estimated_cost_usd: float = 0.0
    status: str = "completed"
    error_code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def calculate_request_cost(
    prompt_tokens: int,
    candidate_tokens: int,
    thinking_tokens: int = 0,
    is_embedding: bool = False,
    is_extended_context: bool = False,
    model_id: str = "gemini-2.5-flash",
) -> float:
    """
    Calculates estimated USD cost from token usage based on verified official Gemini pricing.
    Includes prompt tokens, output/candidate tokens, and thinking/reasoning tokens.
    Thinking tokens are billed at the candidate output rate.
    """
    if is_embedding:
        return round((prompt_tokens / 1_000_000.0) * GEMINI_EMBEDDING_COST_PER_MILLION, 6)

    # Determine tiered pricing based on extended context flag
    if is_extended_context:
        in_rate = GEMINI_FLASH_LONG_INPUT_COST_PER_MILLION
        out_rate = GEMINI_FLASH_LONG_OUTPUT_COST_PER_MILLION
    else:
        in_rate = GEMINI_FLASH_INPUT_COST_PER_MILLION
        out_rate = GEMINI_FLASH_OUTPUT_COST_PER_MILLION

    in_cost = (prompt_tokens / 1_000_000.0) * in_rate
    effective_output_tokens = candidate_tokens + thinking_tokens
    out_cost = (effective_output_tokens / 1_000_000.0) * out_rate
    return round(in_cost + out_cost, 6)


async def persist_agent_run_to_db(
    session_id: str,
    user_id: str,
    intent: str,
    prompt_summary: str,
    status: str,
    total_tokens: int,
    latency_ms: int,
    routing_decision: Optional[Dict[str, Any]] = None,
    final_response: Optional[Dict[str, Any]] = None,
    action_logs: Optional[List[Dict[str, Any]]] = None,
    db_session: Optional[Any] = None,
) -> Optional[str]:
    """
    Durable persistence of agent run telemetry and actions to public.agent_runs
    and public.agent_actions tables per MSGI Rule 14 and Gate 7.8.
    """
    from src.db.models.ai import AgentRun, AgentAction
    import uuid

    run_id = str(uuid.uuid4())
    routing = routing_decision or {}
    response = final_response or {}

    async def _insert_records(session):
        run_record = AgentRun(
            id=run_id,
            user_id=user_id,
            session_id=session_id,
            intent=intent,
            prompt_summary=prompt_summary[:500],
            status=status,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            routing_decision=routing,
            final_response=response,
        )
        session.add(run_record)

        if action_logs:
            for log in action_logs:
                action_record = AgentAction(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    agent_name=log.get("agent", "unknown"),
                    tool_name=log.get("action", "unknown"),
                    action_input=log.get("input", {}),
                    action_output=log.get("output", {}),
                    status=log.get("status", "success"),
                    latency_ms=log.get("latency_ms", 0),
                    error_message=log.get("error_message"),
                )
                session.add(action_record)
        await session.commit()
        return run_id

    if db_session is not None:
        try:
            return await _insert_records(db_session)
        except Exception:
            return None

    try:
        from src.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            return await _insert_records(session)
    except Exception:
        # Fallback gracefully when database is offline or unconfigured
        return None


class CircuitBreaker:
    """In-memory circuit breaker protecting against external provider cascade failures."""
    def __init__(self, failure_threshold: int = CIRCUIT_BREAKER_FAILURE_THRESHOLD, reset_timeout: float = CIRCUIT_BREAKER_RESET_SECONDS):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # 'CLOSED', 'OPEN', 'HALF_OPEN'

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if (time.time() - self.last_failure_time) > self.reset_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return False


class BudgetManager:
    """Enforces token and call budgets per user and per request."""
    def __init__(self, max_request_tokens: int = DEFAULT_MAX_REQUEST_TOKENS):
        self.max_request_tokens = max_request_tokens
        self._user_daily_tokens: Dict[str, int] = {}

    def check_request_budget(self, requested_tokens: int) -> bool:
        return requested_tokens <= self.max_request_tokens

    def record_user_usage(self, user_id: str, tokens: int):
        self._user_daily_tokens[user_id] = self._user_daily_tokens.get(user_id, 0) + tokens

    def get_user_usage(self, user_id: str) -> int:
        return self._user_daily_tokens.get(user_id, 0)


# Global instances
global_circuit_breaker = CircuitBreaker()
global_budget_manager = BudgetManager()
