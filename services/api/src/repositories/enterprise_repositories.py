"""
MSGI One — Enterprise Domain Asynchronous Repositories (Phase 2)
Provides clean async SQLAlchemy 2.0 data-access boundaries for:
  - SchedulingRepository (availability, requests, slots, meetings)
  - MessagingRepository (conversations, participants, messages, attachments, blocks, reports)
  - MediaRoomRepository (meeting_rooms, meeting_participants)
  - AIProviderRepository (ai_provider_configs, ai_usage_ledger)
  - PushDeviceRepository (push_device_tokens)
  - OutboxRepository (outbox_events)
  - IdempotencyRepository (idempotency_keys)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
import uuid
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.enterprise import (
    AIProviderConfig,
    AIUsageLedger,
    AlumniAvailability,
    Conversation,
    ConversationParticipant,
    IdempotencyKey,
    Meeting,
    MeetingParticipant,
    MeetingRequest,
    MeetingRoom,
    MeetingSlot,
    Message,
    MessageAttachment,
    OutboxEvent,
    PushDeviceToken,
    UserBlock,
    UserReport,
)
from src.repositories.base import BaseRepository


class SchedulingRepository(BaseRepository[Meeting]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Meeting, session)

    async def get_alumni_availability(self, alumni_id: str) -> Sequence[AlumniAvailability]:
        res = await self.session.execute(
            select(AlumniAvailability)
            .where(and_(AlumniAvailability.alumni_id == alumni_id, AlumniAvailability.is_active.is_(True)))
            .order_by(AlumniAvailability.day_of_week, AlumniAvailability.start_time_local)
        )
        return res.scalars().all()

    async def has_overlapping_meeting(
        self,
        user_id: str,
        start_utc: datetime,
        end_utc: datetime,
        exclude_meeting_id: Optional[str] = None,
    ) -> bool:
        """Application-level overlap check complementing PostgreSQL GIST exclusion constraints."""
        stmt = select(Meeting).where(
            and_(
                or_(Meeting.alumni_id == user_id, Meeting.student_id == user_id),
                Meeting.status.in_(["scheduled", "in_progress"]),
                Meeting.scheduled_start < end_utc,
                Meeting.scheduled_end > start_utc,
            )
        )
        if exclude_meeting_id:
            stmt = stmt.where(Meeting.id != exclude_meeting_id)
        res = await self.session.execute(stmt)
        return res.scalars().first() is not None

    async def get_request_with_slots(self, request_id: str) -> Optional[MeetingRequest]:
        res = await self.session.execute(
            select(MeetingRequest)
            .where(MeetingRequest.id == request_id)
            .options(selectinload(MeetingRequest.slots))
        )
        return res.scalars().first()

    async def list_user_meetings(self, user_id: str) -> Sequence[Meeting]:
        res = await self.session.execute(
            select(Meeting)
            .where(or_(Meeting.student_id == user_id, Meeting.alumni_id == user_id))
            .order_by(Meeting.scheduled_start.asc())
        )
        return res.scalars().all()


class MessagingRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Conversation, session)

    @staticmethod
    def canonical_pair(user_a: str, user_b: str) -> tuple[str, str]:
        return (user_a, user_b) if user_a < user_b else (user_b, user_a)

    async def is_blocked(self, user_a: str, user_b: str) -> bool:
        res = await self.session.execute(
            select(UserBlock).where(
                or_(
                    and_(UserBlock.blocker_id == user_a, UserBlock.blocked_id == user_b),
                    and_(UserBlock.blocker_id == user_b, UserBlock.blocked_id == user_a),
                )
            )
        )
        return res.scalars().first() is not None

    async def get_or_create_conversation(self, user_a: str, user_b: str) -> Conversation:
        p1, p2 = self.canonical_pair(user_a, user_b)
        res = await self.session.execute(
            select(Conversation)
            .where(and_(Conversation.participant_one_id == p1, Conversation.participant_two_id == p2))
            .options(selectinload(Conversation.participants))
        )
        conv = res.scalars().first()
        if conv:
            return conv

        conv = Conversation(id=str(uuid.uuid4()), participant_one_id=p1, participant_two_id=p2, last_seq=0)
        self.session.add(conv)
        await self.session.flush()
        for uid in (p1, p2):
            self.session.add(ConversationParticipant(id=str(uuid.uuid4()), conversation_id=conv.id, user_id=uid))
        await self.session.flush()
        return conv

    async def get_messages_after_seq(
        self, conversation_id: str, after_seq: int = 0, limit: int = 50
    ) -> Sequence[Message]:
        res = await self.session.execute(
            select(Message)
            .where(and_(Message.conversation_id == conversation_id, Message.seq > after_seq))
            .order_by(Message.seq.asc())
            .limit(limit)
        )
        return res.scalars().all()


class MediaRoomRepository(BaseRepository[MeetingRoom]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(MeetingRoom, session)

    async def get_by_meeting_id(self, meeting_id: str) -> Optional[MeetingRoom]:
        res = await self.session.execute(
            select(MeetingRoom)
            .where(MeetingRoom.meeting_id == meeting_id)
            .options(selectinload(MeetingRoom.participants))
        )
        return res.scalars().first()


class AIProviderRepository(BaseRepository[AIProviderConfig]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AIProviderConfig, session)

    async def list_enabled_configs(self) -> Sequence[AIProviderConfig]:
        res = await self.session.execute(
            select(AIProviderConfig)
            .where(AIProviderConfig.is_enabled.is_(True))
            .order_by(AIProviderConfig.is_primary.desc(), AIProviderConfig.fallback_priority.asc())
        )
        return res.scalars().all()

    async def record_usage(self, **kwargs: Any) -> AIUsageLedger:
        entry = AIUsageLedger(id=str(uuid.uuid4()), **kwargs)
        self.session.add(entry)
        await self.session.flush()
        return entry


class PushDeviceRepository(BaseRepository[PushDeviceToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PushDeviceToken, session)

    async def upsert_token(self, user_id: str, token: str, platform: str, device_name: Optional[str] = None) -> PushDeviceToken:
        res = await self.session.execute(select(PushDeviceToken).where(PushDeviceToken.token == token))
        existing = res.scalars().first()
        now = datetime.now(timezone.utc)
        if existing:
            existing.user_id = user_id
            existing.platform = platform
            existing.device_name = device_name
            existing.is_active = True
            existing.last_seen_at = now
            await self.session.flush()
            return existing
        record = PushDeviceToken(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            platform=platform,
            device_name=device_name,
            is_active=True,
            last_seen_at=now,
        )
        self.session.add(record)
        await self.session.flush()
        return record


class OutboxRepository(BaseRepository[OutboxEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(OutboxEvent, session)

    async def enqueue(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: Dict[str, Any],
        actor_id: Optional[str] = None,
    ) -> OutboxEvent:
        evt = OutboxEvent(
            id=str(uuid.uuid4()),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            actor_id=actor_id,
            payload=payload,
            status="pending",
        )
        self.session.add(evt)
        await self.session.flush()
        return evt

    async def fetch_pending(self, limit: int = 50) -> Sequence[OutboxEvent]:
        now = datetime.now(timezone.utc)
        res = await self.session.execute(
            select(OutboxEvent)
            .where(and_(OutboxEvent.status == "pending", OutboxEvent.available_at <= now))
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
        )
        return res.scalars().all()


class IdempotencyRepository(BaseRepository[IdempotencyKey]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(IdempotencyKey, session)

    async def get_existing(self, scope: str, user_id: str, key: str) -> Optional[IdempotencyKey]:
        res = await self.session.execute(
            select(IdempotencyKey).where(
                and_(
                    IdempotencyKey.scope == scope,
                    IdempotencyKey.user_id == user_id,
                    IdempotencyKey.idempotency_key == key,
                )
            )
        )
        return res.scalars().first()
