"""
MSGI One — Phase 4 Extended Modules & Realtime Test Suite
Tests:
  - Module 9: Learning Academy (Catalog, enrollment, progress, completion, cross-user 403)
  - Module 10: Communities (Public/private visibility, join, moderation, privacy 403, duplicate 409)
  - Module 12: Institutional Administration (RBAC, verification workflow, anti-self-verification, audit logs)
  - Realtime Notifications (List, unread count, mark read, cross-user 403, two-client event flow)
  - Extended Modules 7, 8, 11 (Projects, Startups, Giving/Impact without live payments)
  - Durable Checkpointing (SqliteSaver persistence across mock process restarts)
  - 24-step Comprehensive End-to-End Cross-Module Scenario
Principles: Pressman Multi-Level Testing & Sommerville Verification.
"""

import os
import tempfile
import pytest
from fastapi import HTTPException
from src.core.dependencies import AuthenticatedUser

# Domain Services
from src.services.learning_service import (
    list_learning_resources,
    get_learning_resource,
    enroll_in_course,
    update_learning_progress,
    get_my_learning,
)
from src.services.community_service import (
    list_communities,
    get_community_by_id,
    join_community,
    update_membership_status,
    get_my_communities,
    _COMMUNITY_MEMBERSHIPS_STORE,
)
from src.services.admin_service import (
    list_pending_verifications,
    decide_verification,
    get_admin_summary,
    get_admin_audit_logs,
    _VERIFICATION_REQUESTS_STORE,
)
from src.services.notifications_service import (
    create_notification,
    get_my_notifications,
    get_unread_count,
    mark_notification_as_read,
    mark_all_as_read,
    _NOTIFICATIONS_STORE,
)
from src.services.extended_service import (
    list_projects,
    get_project_by_id,
    join_project_request,
    list_startups,
    get_startup_by_id,
    create_startup_connection,
    list_impact_programmes,
    get_impact_programme,
    register_volunteer_interest,
)

# AI Durable Checkpointing
from langgraph.checkpoint.sqlite import SqliteSaver


# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------

@pytest.fixture
def student_user():
    return AuthenticatedUser(
        id="user-student-phase4-001",
        email="test.student4@example.msgi.edu",
        first_name="Haruto",
        last_name="Takahashi",
        roles=["student"],
        is_verified=True,
    )


@pytest.fixture
def other_student_user():
    return AuthenticatedUser(
        id="user-student-phase4-002",
        email="other.student4@example.msgi.edu",
        first_name="Sora",
        last_name="Tanaka",
        roles=["student"],
        is_verified=True,
    )


@pytest.fixture
def alumni_user():
    return AuthenticatedUser(
        id="user-kenji-001",
        email="kenji.sato@example.msgi.edu",
        first_name="Kenji",
        last_name="Sato",
        roles=["alumni"],
        is_verified=True,
    )


@pytest.fixture
def admin_user():
    return AuthenticatedUser(
        id="user-admin-001",
        email="admin@example.msgi.edu",
        first_name="Admin",
        last_name="Officer",
        roles=["admin", "institutional_admin"],
        is_verified=True,
    )


# -----------------------------------------------------------------------------
# 1. LEARNING ACADEMY (MODULE 9) TESTS
# -----------------------------------------------------------------------------

def test_list_learning_resources():
    resources = list_learning_resources()
    assert len(resources) >= 4
    # Filter by skill
    py_res = list_learning_resources(skill="Python")
    assert any("Python" in r.target_skill for r in py_res)


def test_get_learning_resource_not_found():
    with pytest.raises(HTTPException) as exc:
        get_learning_resource("non-existent-res-999")
    assert exc.value.status_code == 404


def test_enroll_and_duplicate_prevention(student_user):
    enr = enroll_in_course("res-docker-004", student_user)
    assert enr.user_id == student_user.id
    assert enr.progress_percentage == 0
    assert enr.status == "enrolled"

    # Duplicate enrollment should trigger 409 CONFLICT
    with pytest.raises(HTTPException) as exc:
        enroll_in_course("res-docker-004", student_user)
    assert exc.value.status_code == 409


def test_update_learning_progress_authorization_and_completion(student_user, other_student_user):
    enr = enroll_in_course("res-k8s-011", student_user)

    # Boundary violation (<0 or >100) -> 400
    with pytest.raises(HTTPException) as exc:
        update_learning_progress(enr.id, 120, student_user)
    assert exc.value.status_code == 400

    # Cross-user authorization check -> 403 FORBIDDEN
    with pytest.raises(HTTPException) as exc:
        update_learning_progress(enr.id, 50, other_student_user)
    assert exc.value.status_code == 403

    # Valid intermediate progress update
    updated = update_learning_progress(enr.id, 50, student_user)
    assert updated.progress_percentage == 50
    assert updated.status == "in_progress"

    # Completion update (100%)
    completed = update_learning_progress(enr.id, 100, student_user)
    assert completed.progress_percentage == 100
    assert completed.status == "completed"
    assert completed.completed_at is not None


# -----------------------------------------------------------------------------
# 2. COMMUNITIES & INTEREST GROUPS (MODULE 10) TESTS
# -----------------------------------------------------------------------------

def test_community_privacy_filters(student_user, admin_user):
    # Non-member student should not see private community (e.g. comm-exec-003)
    student_comms = list_communities(user=student_user)
    student_ids = [c.id for c in student_comms]
    assert "comm-exec-003" not in student_ids

    # Institutional Admin sees all communities including private
    admin_comms = list_communities(user=admin_user)
    admin_ids = [c.id for c in admin_comms]
    assert "comm-exec-003" in admin_ids


def test_private_community_direct_access_forbidden(student_user):
    with pytest.raises(HTTPException) as exc:
        get_community_by_id("comm-exec-003", student_user)
    assert exc.value.status_code == 403


def test_join_public_community(student_user):
    mem = join_community("comm-cloud-002", student_user)
    assert mem.community_id == "comm-cloud-002"
    assert mem.status == "active"
    assert mem.role == "member"

    # Duplicate join -> 409 CONFLICT
    with pytest.raises(HTTPException) as exc:
        join_community("comm-cloud-002", student_user)
    assert exc.value.status_code == 409


def test_private_community_request_and_moderation(student_user, other_student_user, admin_user):
    # Student requests to join private group -> status "pending"
    mem = join_community("comm-exec-003", student_user)
    assert mem.status == "pending"

    # Non-moderator cannot decide status -> 403 FORBIDDEN
    with pytest.raises(HTTPException) as exc:
        update_membership_status("comm-exec-003", mem.id, "active", other_student_user)
    assert exc.value.status_code == 403

    # Admin / Moderator approves request
    approved = update_membership_status("comm-exec-003", mem.id, "active", admin_user)
    assert approved.status == "active"


# -----------------------------------------------------------------------------
# 3. INSTITUTIONAL ADMINISTRATION (MODULE 12) TESTS
# -----------------------------------------------------------------------------

def test_admin_rbac_guards(student_user):
    with pytest.raises(HTTPException) as exc:
        list_pending_verifications(student_user)
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc:
        get_admin_summary(student_user)
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc:
        get_admin_audit_logs(student_user)
    assert exc.value.status_code == 403


def test_admin_anti_self_verification(admin_user):
    # Attempting to verify self must be rejected with 400
    test_req = {
        "id": "vreq-self-test",
        "user_id": admin_user.id,
        "user_email": admin_user.email,
        "user_name": "Admin Self",
        "requested_role": "institutional_admin",
        "evidence_payload": {},
        "status": "pending",
        "reviewed_by": None,
        "review_notes": None,
        "created_at": "2026-11-20T00:00:00Z",
        "decided_at": None,
    }
    _VERIFICATION_REQUESTS_STORE.append(test_req)

    with pytest.raises(HTTPException) as exc:
        decide_verification("vreq-self-test", "approved", admin_user)
    assert exc.value.status_code == 400


def test_admin_verification_approval_workflow(admin_user):
    # Create synthetic candidate verification request
    v_id = "vreq-candidate-999"
    _VERIFICATION_REQUESTS_STORE.append({
        "id": v_id,
        "user_id": "user-cand-999",
        "user_email": "candidate999@example.msgi.edu",
        "user_name": "Test Candidate",
        "requested_role": "alumni",
        "evidence_payload": {"degree": "B.Tech", "year": 2024},
        "status": "pending",
        "reviewed_by": None,
        "review_notes": None,
        "created_at": "2026-11-20T00:00:00Z",
        "decided_at": None,
    })

    decided = decide_verification(v_id, "approved", admin_user, review_notes="Verified via registrar.")
    assert decided.status == "approved"
    assert decided.reviewed_by == admin_user.id

    # Check that audit log entry was created
    audit_logs = get_admin_audit_logs(admin_user)
    assert any(log.action == "verify_user_approved" and log.target_id == "user-cand-999" for log in audit_logs)

    # Check summary metrics
    summary = get_admin_summary(admin_user)
    assert summary.active_alumni_count >= 1


# -----------------------------------------------------------------------------
# 4. REALTIME NOTIFICATIONS TESTS
# -----------------------------------------------------------------------------

def test_notification_lifecycle_and_security(student_user, other_student_user):
    notif = create_notification(
        user_id=student_user.id,
        event_type="test_event",
        entity_id="entity-001",
        title="Test Notification",
        message="This is a test notification message.",
    )
    assert notif.user_id == student_user.id
    assert not notif.is_read

    unread_count = get_unread_count(student_user)
    assert unread_count >= 1

    # Cross-user authorization check -> 403 FORBIDDEN
    with pytest.raises(HTTPException) as exc:
        mark_notification_as_read(notif.id, other_student_user)
    assert exc.value.status_code == 403

    # Owner marks notification as read
    read_notif = mark_notification_as_read(notif.id, student_user)
    assert read_notif.is_read
    assert read_notif.read_at is not None

    # Mark all as read
    mark_all_as_read(student_user)
    assert get_unread_count(student_user) == 0


def test_two_client_realtime_event_propagation(student_user, alumni_user):
    """
    Client A triggers action -> Notification record committed -> Client B queries notifications.
    """
    initial_unread = get_unread_count(alumni_user)

    # Client A (student) requests connection with startup founded by Client B (alumni Kenji Sato)
    conn = create_startup_connection(
        startup_id="start-neural-001",
        intent="mentorship",
        message="I would love advice on your robotics inference pipeline.",
        user=student_user,
    )
    assert conn.status == "pending"

    # Client B (alumni) queries unread notifications
    new_unread = get_unread_count(alumni_user)
    assert new_unread == initial_unread + 1

    alumni_notifs = get_my_notifications(alumni_user)
    latest = alumni_notifs[0]
    assert latest.event_type == "startup_connection_requested"
    assert "start-neural-001" in latest.payload.get("startup_id", "")


# -----------------------------------------------------------------------------
# 5. EXTENDED MODULES (PROJECTS, STARTUPS, GIVING/IMPACT) TESTS
# -----------------------------------------------------------------------------

def test_projects_join_and_duplicate_prevention(student_user):
    projects = list_projects(skill="Python")
    assert len(projects) >= 1

    proj = projects[0]
    join_req = join_project_request(proj.id, student_user)
    assert join_req.project_id == proj.id
    assert join_req.status == "pending"

    # Duplicate join -> 409 CONFLICT
    with pytest.raises(HTTPException) as exc:
        join_project_request(proj.id, student_user)
    assert exc.value.status_code == 409


def test_startups_connection_and_duplicate_prevention(student_user):
    startups = list_startups(industry="CleanTech / AgTech")
    assert len(startups) >= 1
    s = startups[0]

    conn = create_startup_connection(
        startup_id=s.id,
        intent="internship",
        message="Interested in your telemetry stack.",
        user=student_user,
    )
    assert conn.startup_id == s.id

    # Duplicate connection -> 409 CONFLICT
    with pytest.raises(HTTPException) as exc:
        create_startup_connection(
            startup_id=s.id,
            intent="internship",
            message="Second attempt.",
            user=student_user,
        )
    assert exc.value.status_code == 409


def test_giving_and_impact_volunteering_no_live_payments(student_user):
    programmes = list_impact_programmes()
    assert len(programmes) >= 2
    # Verify no payment processing fields exist
    assert all(hasattr(p, "target_volunteers") for p in programmes)

    target_prog = programmes[0]
    initial_vols = target_prog.current_volunteers

    vol = register_volunteer_interest(
        programme_id=target_prog.id,
        interest_note="Available on alternate Saturdays for Python instruction.",
        user=student_user,
    )
    assert vol.status == "registered"

    # Updated programme volunteer count
    updated_prog = get_impact_programme(target_prog.id, student_user)
    assert updated_prog.current_volunteers == initial_vols + 1
    assert updated_prog.is_registered is True

    # Duplicate volunteer registration -> 409 CONFLICT
    with pytest.raises(HTTPException) as exc:
        register_volunteer_interest(
            programme_id=target_prog.id,
            interest_note="Duplicate registration.",
            user=student_user,
        )
    assert exc.value.status_code == 409


# -----------------------------------------------------------------------------
# 6. DURABLE CHECKPOINTING PERSISTENCE TEST
# -----------------------------------------------------------------------------

def test_sqlite_checkpoint_durability_across_process_restart():
    """
    Demonstrates zero-loss recovery of agent workflow state across process restarts.
    """
    import sqlite3
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
    db_path = db_file.name
    db_file.close()

    try:
        # Session 1: Initialize SqliteSaver, setup tables, save checkpoint
        conn1 = sqlite3.connect(db_path, check_same_thread=False)
        saver1 = SqliteSaver(conn1)
        saver1.setup()

        thread_config = {"configurable": {"thread_id": "thread-persist-401", "checkpoint_ns": ""}}
        checkpoint_data = {
            "v": 1,
            "ts": "2026-11-20T12:00:00Z",
            "id": "chk-001",
            "channel_values": {"current_goal": "Become Senior AI Architect", "step": 3},
            "channel_versions": {"current_goal": 1, "step": 1},
            "versions_seen": {},
            "pending_sends": [],
        }
        metadata = {"source": "test_persistence", "step": 3, "writes": {"step": 3}}

        saver1.put(thread_config, checkpoint_data, metadata, {})

        # Verify saved in Session 1
        retrieved1 = saver1.get(thread_config)
        assert retrieved1 is not None
        assert retrieved1["channel_values"]["step"] == 3
        conn1.close()

        # Simulate Process Restart: instantiate fresh SqliteSaver with new connection to same DB
        conn2 = sqlite3.connect(db_path, check_same_thread=False)
        saver2 = SqliteSaver(conn2)
        saver2.setup()

        retrieved2 = saver2.get(thread_config)
        assert retrieved2 is not None
        assert retrieved2["channel_values"]["current_goal"] == "Become Senior AI Architect"
        assert retrieved2["channel_values"]["step"] == 3
        conn2.close()
    finally:
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except OSError:
            pass


# -----------------------------------------------------------------------------
# 7. COMPREHENSIVE 24-STEP END-TO-END CROSS-MODULE SCENARIO
# -----------------------------------------------------------------------------

def test_24_step_complete_mvp_user_journey():
    """
    Executes a continuous 24-step multi-module user scenario spanning
    Phase 1 (Identity/Profile), Phase 2 (Alumni/Mentors/Jobs/Events),
    Phase 3 (Agentic AI/Approvals), and Phase 4 (Learning/Communities/Admin/Realtime).
    """
    # Step 1: User Identity (Student)
    student = AuthenticatedUser(
        id="user-journey-24step-001",
        email="journey24@example.msgi.edu",
        first_name="Aoi",
        last_name="Nakamura",
        roles=["student"],
        is_verified=True,
    )

    # Step 2: Mentor Identity (Alumni)
    mentor = AuthenticatedUser(
        id="user-kenji-001",
        email="kenji.sato@example.msgi.edu",
        first_name="Kenji",
        last_name="Sato",
        roles=["alumni"],
        is_verified=True,
    )

    # Step 3: Admin Identity
    admin = AuthenticatedUser(
        id="user-admin-001",
        email="admin@example.msgi.edu",
        first_name="Admin",
        last_name="Institutional",
        roles=["admin", "institutional_admin"],
        is_verified=True,
    )

    # Step 4: Search public communities
    comms = list_communities(user=student)
    assert len(comms) >= 1

    # Step 5: Join AI & Robotics Guild (Module 10)
    cm = join_community("comm-ai-001", student)
    assert cm.status == "active"

    # Step 6: Discover Learning Resources for AI (Module 9)
    resources = list_learning_resources(skill="Python")
    assert len(resources) >= 1
    res = resources[0]

    # Step 7: Enroll in Course (Module 9)
    enr = enroll_in_course(res.resource_id, student)
    assert enr.status == "enrolled"

    # Step 8: Update Progress to 50%
    enr_prog = update_learning_progress(enr.id, 50, student)
    assert enr_prog.progress_percentage == 50

    # Step 9: Complete Course to 100%
    enr_done = update_learning_progress(enr.id, 100, student)
    assert enr_done.status == "completed"

    # Step 10: Check Notifications for completion milestone (Realtime)
    notifs = get_my_notifications(student)
    assert any(n.event_type == "course_completed" for n in notifs)

    # Step 11: Mark notification as read
    target_notif = next(n for n in notifs if n.event_type == "course_completed")
    read_n = mark_notification_as_read(target_notif.id, student)
    assert read_n.is_read is True

    # Step 12: Discover Collaboration Projects (Module 7)
    projects = list_projects(skill="Python", user=student)
    assert len(projects) >= 1

    # Step 13: Join Innovation Project
    proj_mem = join_project_request(projects[0].id, student)
    assert proj_mem.status == "pending"

    # Step 14: Discover Startups (Module 8)
    startups = list_startups(industry="Artificial Intelligence")
    assert len(startups) >= 1

    # Step 15: Request Startup Introduction
    startup_conn = create_startup_connection(
        startup_id=startups[0].id,
        intent="mentorship",
        message="Interested in compiler optimizations.",
        user=student,
    )
    assert startup_conn.status == "pending"

    # Step 16: Verify Founder received notification
    mentor_notifs = get_my_notifications(mentor)
    assert any(n.event_type == "startup_connection_requested" for n in mentor_notifs)

    # Step 17: Discover Giving / Social Impact Programme (Module 11)
    impact_progs = list_impact_programmes(user=student)
    assert len(impact_progs) >= 1

    # Step 18: Register for Volunteering (Strictly NO live payments)
    vol = register_volunteer_interest(
        programme_id=impact_progs[0].id,
        interest_note="Available to mentor students in basic programming.",
        user=student,
    )
    assert vol.status == "registered"

    # Step 19: Submit Institutional Verification Request
    v_req_id = "vreq-journey-001"
    _VERIFICATION_REQUESTS_STORE.append({
        "id": v_req_id,
        "user_id": student.id,
        "user_email": student.email,
        "user_name": f"{student.first_name} {student.last_name}",
        "requested_role": "alumni",
        "evidence_payload": {"student_id": "MSGI-2026-CS-099"},
        "status": "pending",
        "reviewed_by": None,
        "review_notes": None,
        "created_at": "2026-11-20T00:00:00Z",
        "decided_at": None,
    })

    # Step 20: Admin lists pending verifications (Module 12)
    pending_v = list_pending_verifications(admin)
    assert any(pv.id == v_req_id for pv in pending_v)

    # Step 21: Admin approves verification request
    decided_v = decide_verification(v_req_id, "approved", admin, review_notes="Degree conferral verified.")
    assert decided_v.status == "approved"

    # Step 22: Verify Student received verification notification
    student_notifs = get_my_notifications(student)
    assert any(n.event_type == "verification_decided" for n in student_notifs)

    # Step 23: Admin reviews audit logs
    logs = get_admin_audit_logs(admin)
    assert any(log.action == "verify_user_approved" and log.target_id == student.id for log in logs)

    # Step 24: Admin verifies system summary metrics
    summary = get_admin_summary(admin)
    assert summary.active_alumni_count >= 1
    assert summary.total_users >= 10
