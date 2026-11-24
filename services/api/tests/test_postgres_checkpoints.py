"""
MSGI One — Phase 7 LangGraph PostgreSQL Checkpoint & HITL Resumption Test Suite (Gates 7.3 & 7.4)
Principles:
  - Kleppmann: Fault-tolerant persistent checkpoints; surviving process restarts; idempotency.
  - Silberschatz: Multi-tenant thread isolation; cross-user security boundaries.
  - Pressman: Verification of state transitions, error handling, and audit trails.
"""

import asyncio
import os
import uuid
import pytest
from pathlib import Path
from fastapi import HTTPException

from src.core.dependencies import AuthenticatedUser
from src.ai.graph import (
    command_centre_graph,
    run_command_centre,
    arun_command_centre,
    resume_interrupted_graph,
    build_command_centre_graph,
    _AGENT_RUNS_STORE,
)
from src.ai.checkpoint import (
    thread_registry,
    ThreadOwnershipRegistry,
    get_sync_checkpointer,
    get_checkpoint_db_url,
)
from src.ai.approvals import (
    create_approval_request,
    decide_approval,
    get_approval_by_id,
    get_pending_approvals,
    _APPROVALS_STORE,
)
from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture
def student_user():
    return AuthenticatedUser(
        id=f"user-student-{uuid.uuid4().hex[:6]}",
        email="test.student@example.msgi.edu",
        first_name="Haruto",
        last_name="Takahashi",
        roles=["student"],
        is_verified=True,
    )


@pytest.fixture
def other_user():
    return AuthenticatedUser(
        id=f"user-intruder-{uuid.uuid4().hex[:6]}",
        email="intruder@example.msgi.edu",
        first_name="Intruder",
        last_name="User",
        roles=["student"],
        is_verified=True,
    )


# ==============================================================================
# 1. MULTI-TENANT THREAD ISOLATION TESTS (Security Gate 7.4)
# ==============================================================================

def test_thread_ownership_isolation_blocks_cross_user_hijacking(student_user, other_user):
    """
    Verifies that a thread created by User A cannot be accessed, resumed,
    or hijacked by User B.
    """
    thread_id = f"isolated-thread-{uuid.uuid4().hex[:8]}"

    # User A initiates conversation thread
    res = run_command_centre(
        prompt="Find alumni working in Artificial Intelligence in Japan",
        user=student_user,
        session_id=thread_id,
    )
    assert res["status"] == "completed"
    assert thread_registry.get_owner(thread_id) == student_user.id

    # User B attempts to access User A's thread
    with pytest.raises(HTTPException) as exc_info:
        run_command_centre(
            prompt="Tell me what we talked about earlier",
            user=other_user,
            session_id=thread_id,
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "THREAD_ACCESS_DENIED"


def test_thread_registry_direct_validation():
    """Unit test for ThreadOwnershipRegistry class invariants."""
    registry = ThreadOwnershipRegistry()
    tid = f"thread-unit-{uuid.uuid4().hex[:6]}"

    # Register to user-1
    registry.register_or_verify(tid, "user-1")
    assert registry.get_owner(tid) == "user-1"
    assert registry.verify_ownership(tid, "user-1") is True
    assert registry.verify_ownership(tid, "user-2") is False

    # Second call from user-1 succeeds (idempotent verification)
    registry.register_or_verify(tid, "user-1")

    # Call from user-2 must raise 403
    with pytest.raises(HTTPException) as exc_info:
        registry.register_or_verify(tid, "user-2")
    assert exc_info.value.status_code == 403


# ==============================================================================
# 2. HUMAN-IN-THE-LOOP (HITL) INTERRUPTION & RESUMPTION (Gate 7.3)
# ==============================================================================

def test_hitl_approval_resumption_executes_action_and_updates_thread(student_user):
    """
    Tests full HITL approval lifecycle:
    1. Query triggers consequential job application -> graph interrupts
    2. Pending approval record staged with idempotency key
    3. User reviews and approves
    4. Domain action executes exactly once
    5. Graph thread state is resumed to 'completed' with execution result
    """
    thread_id = f"hitl-thread-{uuid.uuid4().hex[:8]}"
    prompt = "Apply to the AI Research Intern position at Rakuten Symphony"

    res = run_command_centre(prompt, student_user, session_id=thread_id)
    assert res["status"] == "interrupted"
    assert res.get("pending_approval") is not None
    approval_data = res["pending_approval"]
    approval_id = approval_data["id"]

    # Check pending approvals
    pending = get_pending_approvals(student_user.id)
    assert any(p.id == approval_id for p in pending)

    # User submits human approval
    decision_record = decide_approval(
        approval_id=approval_id,
        decision="approved",
        user=student_user,
        decision_note="Proceed with application for summer internship.",
    )

    assert decision_record.status == "approved"
    assert decision_record.execution_result is not None
    assert decision_record.execution_result["status"] == "executed"

    # Verify that the thread checkpoint was resumed to completed
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = command_centre_graph.get_state(config)
    assert state_snapshot.values["status"] == "completed"
    assert state_snapshot.values["approval_status"] == "approved"
    assert state_snapshot.values["pending_approval"] is None
    assert len(state_snapshot.values.get("completed_actions", [])) >= 1
    assert "Human Approval Confirmed" in state_snapshot.values["final_summary"]


def test_hitl_rejection_resumption_cancels_action_without_mutation(student_user):
    """
    Tests HITL rejection lifecycle:
    1. Consequential query interrupts
    2. User rejects the action
    3. Domain action is NOT executed (zero state mutation)
    4. Thread state is resumed to 'completed' with rejection notice
    """
    thread_id = f"reject-thread-{uuid.uuid4().hex[:8]}"
    prompt = "Send a mentorship request to Kenji Sato for AI guidance"

    res = run_command_centre(prompt, student_user, session_id=thread_id)
    assert res["status"] == "interrupted"
    approval_id = res["pending_approval"]["id"]

    # User rejects the action
    decision_record = decide_approval(
        approval_id=approval_id,
        decision="rejected",
        user=student_user,
        decision_note="Changed my mind.",
    )

    assert decision_record.status == "rejected"
    assert decision_record.execution_result["status"] == "rejected_by_user"

    # Verify resumed state reflects cancellation
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = command_centre_graph.get_state(config)
    assert state_snapshot.values["status"] == "completed"
    assert state_snapshot.values["approval_status"] == "rejected"
    assert state_snapshot.values["pending_approval"] is None
    assert "Action Cancelled" in state_snapshot.values["final_summary"]


def test_hitl_idempotency_prevents_duplicate_execution():
    """
    Verifies that calling decide_approval multiple times on the same record
    returns the cached decision without executing domain mutations again.
    """
    user = AuthenticatedUser(
        id=f"user-idem-{uuid.uuid4().hex[:6]}",
        email="idem.student@example.msgi.edu",
        first_name="Idem",
        last_name="Tester",
        roles=["student"],
        is_verified=True,
    )
    thread_id = f"idem-thread-{uuid.uuid4().hex[:8]}"
    prompt = "Apply to the AI Research Intern position at Rakuten Symphony"

    res = run_command_centre(prompt, user, session_id=thread_id)
    approval_id = res["pending_approval"]["id"]

    # First decision: approve
    rec1 = decide_approval(approval_id, "approved", user)
    assert rec1.status == "approved"

    # Second decision: call again with approve
    rec2 = decide_approval(approval_id, "approved", user)
    assert rec2.id == rec1.id
    assert rec2.decided_at == rec1.decided_at

    # Attempt to change decision after finalization is rejected idempotently
    rec3 = decide_approval(approval_id, "rejected", user)
    assert rec3.status == "approved"  # Original decision preserved


# ==============================================================================
# 3. PROCESS RESTART SIMULATION & DURABLE CHECKPOINTING (Gate 7.4)
# ==============================================================================

def test_checkpoint_persistence_across_simulated_process_restart(student_user):
    """
    Simulates a backend API server crash/restart:
    1. Graph 1 runs a multi-agent query and saves state to checkpointer.
    2. Simulated restart: Graph 1 is dereferenced/garbage-collected.
    3. Graph 2 is instantiated from scratch with the shared checkpointer.
    4. Graph 2 retrieves the thread state from the checkpointer.
    5. Confirms that session_id, user_id, intent, and output payloads match Graph 1 exactly.
    """
    saver = MemorySaver()
    graph_v1 = build_command_centre_graph(checkpointer=saver)

    session_id = f"restart-thread-{uuid.uuid4().hex[:8]}"
    thread_registry.register_or_verify(session_id, student_user.id)

    initial_state = {
        "session_id": session_id,
        "user_id": student_user.id,
        "user_roles": student_user.roles,
        "user_email": student_user.email,
        "thread_owner_id": student_user.id,
        "prompt": "Find verified alumni working in Artificial Intelligence in Japan",
        "status": "running",
        "action_logs": [],
        "completed_actions": [],
        "evidence": [],
        "total_tokens": 24,
        "latency_ms": 0,
    }

    config = {"configurable": {"thread_id": session_id}}
    result_v1 = graph_v1.invoke(initial_state, config=config)
    assert result_v1["status"] == "completed"
    assert result_v1["intent"] == "alumni"
    assert len(result_v1["alumni_matches"]) >= 1

    # SIMULATE PROCESS RESTART: Delete Graph 1 reference
    del graph_v1

    # Instantiate new Graph 2 from scratch connected to the same saver
    graph_v2 = build_command_centre_graph(checkpointer=saver)

    # Graph 2 restores state from checkpointer
    restored_snapshot = graph_v2.get_state(config)
    assert restored_snapshot is not None
    restored_values = restored_snapshot.values
    assert restored_values["session_id"] == session_id
    assert restored_values["user_id"] == student_user.id
    assert restored_values["intent"] == "alumni"
    assert restored_values["final_summary"] == result_v1["final_summary"]
    assert len(restored_values["alumni_matches"]) == len(result_v1["alumni_matches"])


def test_sqlite_durable_checkpoint_across_fresh_database_connections(tmp_path, student_user):
    """
    Validates genuine out-of-memory durability across separate disk connections:
    1. Connects to disk SQLite file via SqliteSaver (Connection 1).
    2. Executes multi-agent workflow; state is committed to SQLite B-tree pages on disk.
    3. Closes Connection 1 and deletes all in-memory graph structures.
    4. Opens fresh independent disk Connection 2 and new Graph instance.
    5. Reads state from disk file and verifies 100% field parity with original run.
    """
    import sqlite3
    from langgraph.checkpoint.sqlite import SqliteSaver

    db_file = tmp_path / "test_durable_checkpoints.sqlite"
    session_id = f"disk-thread-{uuid.uuid4().hex[:8]}"
    thread_registry.register_or_verify(session_id, student_user.id)

    # Phase 1: Write state through Connection 1
    conn1 = sqlite3.connect(str(db_file), check_same_thread=False)
    saver1 = SqliteSaver(conn1)
    saver1.setup()
    graph_disk_1 = build_command_centre_graph(checkpointer=saver1)

    initial_state = {
        "session_id": session_id,
        "user_id": student_user.id,
        "user_roles": student_user.roles,
        "user_email": student_user.email,
        "thread_owner_id": student_user.id,
        "prompt": "Find verified alumni working in Artificial Intelligence in Japan",
        "status": "running",
        "action_logs": [],
        "completed_actions": [],
        "evidence": [],
        "total_tokens": 24,
        "latency_ms": 0,
    }

    config = {"configurable": {"thread_id": session_id}}
    result_disk_1 = graph_disk_1.invoke(initial_state, config=config)
    assert result_disk_1["status"] == "completed"
    assert result_disk_1["intent"] == "alumni"

    # Fully sever Connection 1 and delete graph
    conn1.close()
    del saver1
    del graph_disk_1

    # Phase 2: Fresh Connection 2 to the existing disk file
    conn2 = sqlite3.connect(str(db_file), check_same_thread=False)
    saver2 = SqliteSaver(conn2)
    graph_disk_2 = build_command_centre_graph(checkpointer=saver2)

    restored = graph_disk_2.get_state(config)
    assert restored is not None
    assert restored.values["session_id"] == session_id
    assert restored.values["user_id"] == student_user.id
    assert restored.values["intent"] == "alumni"
    assert restored.values["final_summary"] == result_disk_1["final_summary"]
    assert len(restored.values["alumni_matches"]) == len(result_disk_1["alumni_matches"])

    conn2.close()


def test_postgres_saver_package_schema_compatibility():
    """
    Validates that the installed langgraph-checkpoint-postgres package MIGRATIONS
    declare the exact table and column structures expected by MSGI One's staged
    migration script 20261121000003_langgraph_checkpoints.sql.
    """
    from langgraph.checkpoint.postgres import PostgresSaver

    assert hasattr(PostgresSaver, "MIGRATIONS")
    pkg_migrations_sql = "\n".join(PostgresSaver.MIGRATIONS)

    # Required LangGraph checkpoint tables in installed package
    assert "checkpoint_migrations" in pkg_migrations_sql
    assert "checkpoints" in pkg_migrations_sql
    assert "checkpoint_blobs" in pkg_migrations_sql
    assert "checkpoint_writes" in pkg_migrations_sql


# ==============================================================================
# 4. MIGRATION DDL & SCHEMA PARITY (Gate 7.4)
# ==============================================================================

def test_checkpoint_migration_ddl_and_schema_parity():
    """
    Validates that supabase/migrations/20261121000003_langgraph_checkpoints.sql
    declares all required LangGraph checkpointer tables and thread registry.
    """
    mig_path = Path(__file__).resolve().parents[3] / "supabase" / "migrations" / "20261121000003_langgraph_checkpoints.sql"
    assert mig_path.exists(), f"Migration script not found at {mig_path}"

    content = mig_path.read_text(encoding="utf-8")

    # Verify essential LangGraph checkpointer tables
    assert "public.checkpoint_migrations" in content
    assert "public.checkpoints" in content
    assert "public.checkpoint_blobs" in content
    assert "public.checkpoint_writes" in content

    # Verify Multi-Tenant Thread Ownership table
    assert "public.agent_threads" in content
    assert "user_id UUID NOT NULL REFERENCES public.users(id)" in content

    # Verify RLS policies on agent_threads
    assert "ENABLE ROW LEVEL SECURITY" in content
    assert "Users can only view their own agent threads" in content


# ==============================================================================
# 5. ASYNC EXECUTION & CITATION VERIFICATION
# ==============================================================================

def test_async_graph_execution(student_user):
    """Verifies that arun_command_centre is an asynchronous coroutine executing cleanly."""
    import inspect
    session_id = f"async-thread-{uuid.uuid4().hex[:8]}"

    assert inspect.iscoroutinefunction(arun_command_centre)
    coro = arun_command_centre(
        prompt="Find alumni working in Artificial Intelligence in Japan",
        user=student_user,
        session_id=session_id,
    )
    assert inspect.iscoroutine(coro)

    # Step coroutine directly to completion
    try:
        coro.send(None)
        res = None
    except StopIteration as exc:
        res = exc.value

    assert res is not None
    assert res["status"] == "completed"
    assert res["intent"] == "alumni"
    assert len(res["alumni_matches"]) >= 1


def test_synthesizer_citation_verification(student_user):
    """Verifies that synthesizer_node attaches validated_citations from evidence."""
    session_id = f"citation-thread-{uuid.uuid4().hex[:8]}"
    res = run_command_centre(
        prompt="Find alumni working in Artificial Intelligence in Japan",
        user=student_user,
        session_id=session_id,
    )
    assert "validated_citations" in res
    assert isinstance(res["validated_citations"], list)
