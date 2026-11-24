"""
MSGI One — AI Security, Observability, Telemetry & Cost Controls Tests (Gates 7.7 & 7.8)
Validates:
1. PII sanitization: credit cards, national IDs, emails, phone numbers.
2. Official Gemini API cost calculation logic ($0.075/$0.300 per 1M).
3. Request-level token budget enforcement.
4. Circuit breaker state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED).
5. Observability telemetry and persistent audit recording.
"""

import time
import pytest
from src.core.dependencies import AuthenticatedUser
from src.ai.provider import sanitize_prompt_for_privacy
from src.ai.observability import (
    calculate_request_cost,
    BudgetManager,
    CircuitBreaker,
    global_circuit_breaker,
)
from src.ai.graph import run_command_centre, _AGENT_RUNS_STORE


@pytest.fixture
def student_user():
    return AuthenticatedUser(
        id="user-student-001",
        email="student@example.msgi.edu",
        first_name="Haruto",
        last_name="Takahashi",
        roles=["student"],
        is_verified=True,
    )


def test_pii_sanitization_masks_sensitive_identifiers():
    """Verify that credit cards, SSN/Aadhaar, emails, and phone numbers are redacted."""
    raw_prompt = (
        "My corporate credit card is 4111-2222-3333-4444 and my SSN is 123-45-6789. "
        "Contact me at private.individual@gmail.com or call +1-555-867-5309."
    )
    sanitized = sanitize_prompt_for_privacy(raw_prompt)

    assert "4111-2222-3333-4444" not in sanitized
    assert "[REDACTED_FINANCIAL]" in sanitized
    assert "123-45-6789" not in sanitized
    assert "[REDACTED_NATIONAL_ID]" in sanitized
    assert "private.individual@gmail.com" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "+1-555-867-5309" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized


def test_official_pricing_calculation():
    """Verify that request cost calculations conform strictly to official Gemini 2.5 Flash pricing."""
    # 1,000,000 input tokens = $0.300; 1,000,000 output tokens = $2.500 -> Total = $2.800
    cost_million = calculate_request_cost(1_000_000, 1_000_000)
    assert abs(cost_million - 2.800) < 1e-4

    # 1,000 input tokens + 500 output tokens = (0.000300 + 0.001250) = $0.001550
    cost_small = calculate_request_cost(1_000, 500)
    assert abs(cost_small - 0.001550) < 1e-6

    # Embedding cost: 1,000,000 tokens = $0.020
    cost_embed = calculate_request_cost(1_000_000, 0, is_embedding=True)
    assert abs(cost_embed - 0.020) < 1e-4


def test_official_pricing_calculation_with_thinking_tokens():
    """
    Verify that thinking/reasoning tokens are billed at candidate output rate
    per official Google Gemini 2.0 / 2.5 Flash billing specifications.
    """
    # 10,000 prompt tokens + 2,000 candidate tokens + 1,000 thinking tokens:
    # prompt: (10,000 / 1M) * 0.300 = $0.003000
    # output (candidate 2k + thinking 1k = 3k): (3,000 / 1M) * 2.500 = $0.007500
    # total = $0.010500
    cost_with_thinking = calculate_request_cost(
        prompt_tokens=10_000,
        candidate_tokens=2_000,
        thinking_tokens=1_000,
    )
    assert abs(cost_with_thinking - 0.010500) < 1e-6

    # Extended context (> 128k prompt tokens):
    # in_rate = $0.600 / 1M, out_rate = $5.000 / 1M
    # 200,000 prompt tokens + 10,000 candidate tokens + 5,000 thinking tokens
    # prompt: (200,000 / 1M) * 0.600 = $0.120000
    # output (15,000 / 1M) * 5.000 = $0.075000
    # total = $0.195000
    cost_extended = calculate_request_cost(
        prompt_tokens=200_000,
        candidate_tokens=10_000,
        thinking_tokens=5_000,
        is_extended_context=True,
    )
    assert abs(cost_extended - 0.195000) < 1e-6


def test_persist_agent_run_to_db_record_generation():
    """Verify that persist_agent_run_to_db constructs valid AgentRun and AgentAction entities."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from src.ai.observability import persist_agent_run_to_db

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    run_id = asyncio.run(persist_agent_run_to_db(
        session_id="test-session-persist-001",
        user_id="user-student-001",
        intent="alumni_search",
        prompt_summary="Find AI alumni",
        status="completed",
        total_tokens=120,
        latency_ms=250,
        routing_decision={"agent": "alumni"},
        final_response={"summary": "Found 3 alumni"},
        action_logs=[
            {"agent": "alumni", "action": "search", "status": "success", "latency_ms": 150}
        ],
        db_session=mock_session,
    ))

    assert run_id is not None
    assert mock_session.add.call_count == 2  # 1 AgentRun + 1 AgentAction
    assert mock_session.commit.await_count == 1


def test_budget_manager_enforces_token_limits():
    """Verify that BudgetManager rejects requests exceeding configured max token threshold."""
    bm = BudgetManager(max_request_tokens=2000)
    assert bm.check_request_budget(1500) is True
    assert bm.check_request_budget(2000) is True
    assert bm.check_request_budget(2001) is False

    bm.record_user_usage("user-test-001", 800)
    bm.record_user_usage("user-test-001", 400)
    assert bm.get_user_usage("user-test-001") == 1200


def test_circuit_breaker_state_transitions():
    """Verify that CircuitBreaker opens after 3 failures and respects timeout cooldown."""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=0.2)
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True

    cb.record_failure()
    assert cb.state == "CLOSED"
    cb.record_failure()
    assert cb.state == "CLOSED"
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False

    # Wait for cooldown timeout
    time.sleep(0.25)
    assert cb.can_execute() is True
    assert cb.state == "HALF_OPEN"

    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True


def test_telemetry_recording_in_command_centre(student_user):
    """Verify that command centre executions record tokens, latency, and estimated cost."""
    sid = "sess-telemetry-test-001"
    res = run_command_centre(
        "Find verified alumni working in Artificial Intelligence in Japan",
        student_user,
        session_id=sid,
    )
    assert res["status"] == "completed"
    assert sid in _AGENT_RUNS_STORE

    log = _AGENT_RUNS_STORE[sid]
    assert log["id"] == sid
    assert log["user_id"] == student_user.id
    assert log["status"] == "completed"
    assert log["latency_ms"] >= 0
    assert log["tokens"] > 0
    assert "estimated_cost_usd" in log
    assert log["estimated_cost_usd"] >= 0.0
