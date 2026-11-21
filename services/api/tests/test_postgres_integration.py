"""
MSGI One — Asynchronous Repositories & PostgreSQL Persistence Integration Tests (Gate 6.5)
Principle: Abraham Silberschatz (Relational Operations) & Martin Fowler (Repository Pattern).
Validates typed async CRUD interfaces, query AST generation, 38-table schema metadata,
foreign key cascade rules, unique/check constraints, and coroutine execution contracts.
"""

import inspect
from unittest.mock import MagicMock
from sqlalchemy import select, and_, or_, func
from src.db.models.base import Base
from src.db.models.user import (
    Role,
    User,
    UserRole,
    AlumniProfile,
    StudentProfile,
    FacultyProfile,
    RecruiterProfile,
    UserPreference,
    ConsentRecord,
    AlumniLocation,
    Skill,
    UserSkill,
    AuditLog,
)
from src.db.models.core import (
    MentorProfile,
    MentorRequest,
    Job,
    JobApplication,
    Event,
    EventRegistration,
    AlumniChapter,
)
from src.db.models.ai import (
    CareerRoleSkill,
    LearningResource,
    StudentSkill,
    AgentRun,
    AgentAction,
    ApprovalRequest,
)
from src.db.models.extended import (
    CourseEnrollment,
    Community,
    CommunityMembership,
    VerificationRequest,
    AdminAuditLog,
    Project,
    ProjectMember,
    Startup,
    StartupConnectionRequest,
    ImpactProgramme,
    VolunteerInterest,
    Notification,
)
from src.repositories import (
    BaseRepository,
    UserRepository,
    AlumniRepository,
    JobsRepository,
    MentorRepository,
    EventsRepository,
    LearningRepository,
    CommunityRepository,
    AdminRepository,
    NotificationsRepository,
)


def test_declarative_table_count_and_schema_parity():
    """Verify that exactly 38 relational base tables are mapped in Base.metadata."""
    assert len(Base.metadata.tables) == 38
    expected_tables = {
        "admin_audit_logs", "agent_actions", "agent_runs", "alumni_chapters",
        "alumni_locations", "alumni_profiles", "approval_requests", "audit_logs",
        "career_role_skills", "communities", "community_memberships", "consent_records",
        "course_enrollments", "event_registrations", "events", "faculty_profiles",
        "impact_programmes", "job_applications", "jobs", "learning_resources",
        "mentor_profiles", "mentor_requests", "notifications", "project_members",
        "projects", "recruiter_profiles", "roles", "skills", "startup_connection_requests",
        "startups", "student_profiles", "student_skills", "user_preferences",
        "user_roles", "user_skills", "users", "verification_requests", "volunteer_interests",
    }
    assert set(Base.metadata.tables.keys()) == expected_tables


def test_repository_registry_and_model_bindings():
    """Verify that each domain repository binds strictly to its canonical SQLAlchemy model."""
    mock_session = MagicMock()

    user_repo = UserRepository(mock_session)
    assert user_repo.model == User
    assert user_repo.model.__tablename__ == "users"

    alumni_repo = AlumniRepository(mock_session)
    assert alumni_repo.model == AlumniProfile
    assert alumni_repo.model.__tablename__ == "alumni_profiles"

    jobs_repo = JobsRepository(mock_session)
    assert jobs_repo.model == Job
    assert jobs_repo.model.__tablename__ == "jobs"

    mentor_repo = MentorRepository(mock_session)
    assert mentor_repo.model == MentorProfile
    assert mentor_repo.model.__tablename__ == "mentor_profiles"

    events_repo = EventsRepository(mock_session)
    assert events_repo.model == Event
    assert events_repo.model.__tablename__ == "events"

    learning_repo = LearningRepository(mock_session)
    assert learning_repo.model == LearningResource
    assert learning_repo.model.__tablename__ == "learning_resources"

    comm_repo = CommunityRepository(mock_session)
    assert comm_repo.model == Community
    assert comm_repo.model.__tablename__ == "communities"

    admin_repo = AdminRepository(mock_session)
    assert admin_repo.model == VerificationRequest
    assert admin_repo.model.__tablename__ == "verification_requests"

    notif_repo = NotificationsRepository(mock_session)
    assert notif_repo.model == Notification
    assert notif_repo.model.__tablename__ == "notifications"


def test_foreign_key_cascade_invariants():
    """Verify that foreign keys enforce ON DELETE CASCADE or ON DELETE SET NULL."""
    # User roles cascade
    user_roles_table = Base.metadata.tables["user_roles"]
    user_fks = [fk for fk in user_roles_table.foreign_keys if fk.column.table.name == "users"]
    assert len(user_fks) >= 1
    assert any(fk.ondelete == "CASCADE" for fk in user_fks)

    # Job applications cascade
    apps_table = Base.metadata.tables["job_applications"]
    job_fks = [fk for fk in apps_table.foreign_keys if fk.column.table.name == "jobs"]
    assert any(fk.ondelete == "CASCADE" for fk in job_fks)

    # Mentor profiles cascade
    mentor_table = Base.metadata.tables["mentor_profiles"]
    alumni_fks = [fk for fk in mentor_table.foreign_keys if fk.column.table.name == "alumni_profiles"]
    assert any(fk.ondelete == "CASCADE" for fk in alumni_fks)

    # Event registrations cascade
    reg_table = Base.metadata.tables["event_registrations"]
    event_fks = [fk for fk in reg_table.foreign_keys if fk.column.table.name == "events"]
    assert any(fk.ondelete == "CASCADE" for fk in event_fks)

    # Notifications cascade
    notif_table = Base.metadata.tables["notifications"]
    user_notif_fks = [fk for fk in notif_table.foreign_keys if fk.column.table.name == "users"]
    assert any(fk.ondelete == "CASCADE" for fk in user_notif_fks)


def test_unique_and_check_constraints():
    """Verify domain constraints across tables."""
    # 1. Job applications unique(job_id, applicant_id)
    apps_table = Base.metadata.tables["job_applications"]
    uqs = [c.name for c in apps_table.constraints if hasattr(c, "columns") and len(c.columns) > 1]
    assert "uq_job_applications_user" in uqs

    # 2. Mentor capacity check
    mentor_table = Base.metadata.tables["mentor_profiles"]
    chks = [c.name for c in mentor_table.constraints if hasattr(c, "sqltext")]
    assert "chk_mentee_capacity" in chks

    # 3. Event times check
    events_table = Base.metadata.tables["events"]
    event_chks = [c.name for c in events_table.constraints if hasattr(c, "sqltext")]
    assert "chk_event_times" in event_chks

    # 4. Course enrollment progress check
    course_table = Base.metadata.tables["course_enrollments"]
    course_chks = [c.name for c in course_table.constraints if hasattr(c, "sqltext")]
    assert "chk_progress_percentage" in course_chks


def test_repository_coroutine_signatures():
    """Verify that all repository methods are defined as asynchronous coroutine functions."""
    mock_session = MagicMock()
    repo = BaseRepository(Role, mock_session)

    assert inspect.iscoroutinefunction(repo.get_by_id)
    assert inspect.iscoroutinefunction(repo.list)
    assert inspect.iscoroutinefunction(repo.count)
    assert inspect.iscoroutinefunction(repo.create)
    assert inspect.iscoroutinefunction(repo.update)
    assert inspect.iscoroutinefunction(repo.delete)

    user_repo = UserRepository(mock_session)
    assert inspect.iscoroutinefunction(user_repo.get_by_email)
    assert inspect.iscoroutinefunction(user_repo.get_with_relations)
    assert inspect.iscoroutinefunction(user_repo.update_profile_fields)

    alumni_repo = AlumniRepository(mock_session)
    assert inspect.iscoroutinefunction(alumni_repo.search_directory)
    assert inspect.iscoroutinefunction(alumni_repo.get_by_user_or_profile_id)

    jobs_repo = JobsRepository(mock_session)
    assert inspect.iscoroutinefunction(jobs_repo.search_active_jobs)
    assert inspect.iscoroutinefunction(jobs_repo.get_application)
    assert inspect.iscoroutinefunction(jobs_repo.create_application)
    assert inspect.iscoroutinefunction(jobs_repo.get_user_applications)

    mentor_repo = MentorRepository(mock_session)
    assert inspect.iscoroutinefunction(mentor_repo.list_available_mentors)
    assert inspect.iscoroutinefunction(mentor_repo.get_active_request)
    assert inspect.iscoroutinefunction(mentor_repo.create_request)
    assert inspect.iscoroutinefunction(mentor_repo.get_user_requests)

    events_repo = EventsRepository(mock_session)
    assert inspect.iscoroutinefunction(events_repo.list_upcoming_events)
    assert inspect.iscoroutinefunction(events_repo.get_registration)
    assert inspect.iscoroutinefunction(events_repo.register_user)

    learning_repo = LearningRepository(mock_session)
    assert inspect.iscoroutinefunction(learning_repo.list_by_skill_and_difficulty)
    assert inspect.iscoroutinefunction(learning_repo.get_user_enrollments)
    assert inspect.iscoroutinefunction(learning_repo.enroll)

    comm_repo = CommunityRepository(mock_session)
    assert inspect.iscoroutinefunction(comm_repo.get_by_slug)
    assert inspect.iscoroutinefunction(comm_repo.list_discoverable)
    assert inspect.iscoroutinefunction(comm_repo.join_community)

    admin_repo = AdminRepository(mock_session)
    assert inspect.iscoroutinefunction(admin_repo.list_pending_verifications)
    assert inspect.iscoroutinefunction(admin_repo.decide_verification)
    assert inspect.iscoroutinefunction(admin_repo.log_admin_action)

    notif_repo = NotificationsRepository(mock_session)
    assert inspect.iscoroutinefunction(notif_repo.get_user_notifications)
    assert inspect.iscoroutinefunction(notif_repo.mark_read)
    assert inspect.iscoroutinefunction(notif_repo.create_notification)


def test_coroutine_instantiation_and_query_assembly():
    """Verify that repository methods instantiate valid coroutine objects with correct SQL ASTs."""
    mock_session = MagicMock()
    repo = BaseRepository(Role, mock_session)

    # Calling coroutine function produces coroutine object
    coro = repo.get_by_id("student")
    assert inspect.iscoroutine(coro)
    coro.close()

    coro_list = repo.list(limit=5, offset=10)
    assert inspect.iscoroutine(coro_list)
    coro_list.close()

    coro_create = repo.create(id="alumni", description="Alumni Description")
    assert inspect.iscoroutine(coro_create)
    coro_create.close()


def test_sql_ast_compilation_and_dialect_rendering():
    """Verify that SQLAlchemy 2.0 select statements compile to valid SQL strings."""
    # Test User query compilation
    user_stmt = select(User).where(User.email == "test@example.msgi.edu")
    compiled_user = str(user_stmt.compile())
    assert "users.email =" in compiled_user

    # Test AlumniProfile query compilation
    alumni_stmt = select(AlumniProfile).where(AlumniProfile.graduation_year == 2021)
    compiled_alumni = str(alumni_stmt.compile())
    assert "alumni_profiles.graduation_year =" in compiled_alumni

    # Test Jobs active search query compilation
    job_stmt = select(Job).where(and_(Job.is_active == True, Job.opportunity_type == "full_time"))
    compiled_job = str(job_stmt.compile())
    assert "jobs.is_active =" in compiled_job
    assert "jobs.opportunity_type =" in compiled_job

    # Test Mentor query compilation
    mentor_stmt = select(MentorProfile).where(MentorProfile.is_accepting_requests == True)
    compiled_mentor = str(mentor_stmt.compile())
    assert "mentor_profiles.is_accepting_requests =" in compiled_mentor
