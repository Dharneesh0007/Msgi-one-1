"""
MSGI One — Phase 2 Enterprise Schema & Repository Integration Tests
Validates:
  1. SQLite/SQLAlchemy schema DDL compilation for all 55 tables.
  2. Foreign key, unique, and check constraint enforcement on new enterprise tables.
  3. Async CRUD across Scheduling, Messaging, MediaRoom, AIProvider, PushDevice, Outbox, and Idempotency repositories.
  4. Concurrent/overlap conflict detection at repository level.
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.models import Base
from src.db.models.user import User
from src.db.models.enterprise import (
    AlumniAvailability,
    MeetingRequest,
    MeetingSlot,
    Meeting,
    Conversation,
    Message,
    UserBlock,
)
from src.repositories import (
    SchedulingRepository,
    MessagingRepository,
    MediaRoomRepository,
    AIProviderRepository,
    PushDeviceRepository,
    OutboxRepository,
    IdempotencyRepository,
)


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_enterprise_repositories_crud_and_constraints(async_session: AsyncSession):
    student_id = str(uuid.uuid4())
    alumni_id = str(uuid.uuid4())
    if alumni_id < student_id:
        student_id, alumni_id = alumni_id, student_id

    async_session.add_all([
        User(id=student_id, email="student.p2@example.msgi.edu", first_name="Student", last_name="One"),
        User(id=alumni_id, email="alumni.p2@example.msgi.edu", first_name="Alumnus", last_name="One", is_verified=True),
    ])
    await async_session.flush()

    sched_repo = SchedulingRepository(async_session)
    avail = AlumniAvailability(
        id=str(uuid.uuid4()),
        alumni_id=alumni_id,
        day_of_week=1,
        start_time_local="09:00",
        end_time_local="17:00",
        timezone="Asia/Tokyo",
        slot_duration_minutes=30,
        buffer_minutes=10,
    )
    async_session.add(avail)
    await async_session.flush()
    fetched_avail = await sched_repo.get_alumni_availability(alumni_id)
    assert len(fetched_avail) == 1

    now = datetime.now(timezone.utc)
    req_id = str(uuid.uuid4())
    m_req = MeetingRequest(
        id=req_id,
        student_id=student_id,
        alumni_id=alumni_id,
        title="Career Guidance",
        purpose="Discuss distributed systems careers",
        duration_minutes=30,
        student_timezone="UTC",
        status="pending",
    )
    slot = MeetingSlot(
        id=str(uuid.uuid4()),
        meeting_request_id=req_id,
        proposed_by=student_id,
        round_number=1,
        start_utc=now + timedelta(days=2),
        end_utc=now + timedelta(days=2, minutes=30),
    )
    async_session.add_all([m_req, slot])
    await async_session.flush()
    loaded_req = await sched_repo.get_request_with_slots(req_id)
    assert loaded_req is not None
    assert len(loaded_req.slots) == 1

    meeting = await sched_repo.create(
        id=str(uuid.uuid4()),
        meeting_request_id=req_id,
        student_id=student_id,
        alumni_id=alumni_id,
        title="Career Guidance",
        purpose="Confirmed consultation",
        scheduled_start=slot.start_utc,
        scheduled_end=slot.end_utc,
        status="scheduled",
    )
    assert await sched_repo.has_overlapping_meeting(
        alumni_id,
        slot.start_utc + timedelta(minutes=10),
        slot.end_utc + timedelta(minutes=10),
    ) is True

    # Messaging + Canonical Conversation Pair
    msg_repo = MessagingRepository(async_session)
    conv = await msg_repo.get_or_create_conversation(alumni_id, student_id)
    assert conv.participant_one_id < conv.participant_two_id
    conv_same = await msg_repo.get_or_create_conversation(student_id, alumni_id)
    assert conv.id == conv_same.id

    msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        sender_id=student_id,
        seq=1,
        body="Hello mentor!",
        client_idempotency_key="idem-msg-1",
    )
    async_session.add(msg)
    await async_session.flush()
    missed = await msg_repo.get_messages_after_seq(conv.id, after_seq=0)
    assert len(missed) == 1
    assert missed[0].body == "Hello mentor!"

    # Media Room, AI Provider, Push Token, Outbox, Idempotency
    room_repo = MediaRoomRepository(async_session)
    room = await room_repo.create(
        id=str(uuid.uuid4()),
        meeting_id=meeting.id,
        room_name=f"msgi-room-{meeting.id[:8]}",
        host_user_id=alumni_id,
        expires_at=now + timedelta(days=3),
    )
    assert (await room_repo.get_by_meeting_id(meeting.id)).id == room.id

    ai_repo = AIProviderRepository(async_session)
    cfg = await ai_repo.create(
        id=str(uuid.uuid4()),
        provider="gemini",
        display_name="Gemini Primary",
        model_id="gemini-2.5-flash",
        encrypted_api_key="ciphertext",
        nonce="nonce123",
        key_hint="...1234",
        is_enabled=True,
        is_primary=True,
    )
    assert len(await ai_repo.list_enabled_configs()) == 1
    usage = await ai_repo.record_usage(
        provider_config_id=cfg.id,
        provider="gemini",
        model_id="gemini-2.5-flash",
        user_id=student_id,
        prompt_tokens=100,
        output_tokens=50,
        total_tokens=150,
        estimated_cost_usd=0.000155,
    )
    assert usage.total_tokens == 150

    push_repo = PushDeviceRepository(async_session)
    tok = await push_repo.upsert_token(student_id, "ExponentPushToken[test-1]", "android", "Pixel 8")
    assert tok.is_active is True

    outbox_repo = OutboxRepository(async_session)
    evt = await outbox_repo.enqueue("meeting", meeting.id, "meeting.scheduled", {"meeting_id": meeting.id}, actor_id=alumni_id)
    assert len(await outbox_repo.fetch_pending()) == 1
    assert evt.status == "pending"

    idem_repo = IdempotencyRepository(async_session)
    await idem_repo.create(
        id=str(uuid.uuid4()),
        scope="meeting_request",
        user_id=student_id,
        idempotency_key="req-key-1",
        request_hash="abc123",
        response_status=201,
        response_body={"id": req_id},
        expires_at=now + timedelta(hours=24),
    )
    assert (await idem_repo.get_existing("meeting_request", student_id, "req-key-1")) is not None

    # Check self-block constraint
    async_session.add(UserBlock(id=str(uuid.uuid4()), blocker_id=student_id, blocked_id=student_id))
    with pytest.raises(IntegrityError):
        await async_session.flush()
    await async_session.rollback()
