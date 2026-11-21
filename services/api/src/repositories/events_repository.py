"""
MSGI One — Events & Reunions Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Abraham Silberschatz (Capacity & Temporal Constraints).
Manages Events, Ticket Codes, and Event Registrations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models.core import Event, EventRegistration
from src.repositories.base import BaseRepository


class EventsRepository(BaseRepository[Event]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Event, session)

    async def list_upcoming_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Event]:
        """List published upcoming events."""
        now = datetime.now(timezone.utc)
        stmt = select(Event).where(
            Event.is_published == True,
            Event.end_time > now,
        )
        if event_type:
            stmt = stmt.where(Event.event_type == event_type)

        stmt = stmt.order_by(Event.start_time.asc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_registration(self, event_id: str, user_id: str) -> Optional[EventRegistration]:
        """Find existing user registration for an event."""
        stmt = select(EventRegistration).where(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def register_user(self, event_id: str, user_id: str) -> EventRegistration:
        """Register a user for an event and increment registration count."""
        event = await self.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        reg = EventRegistration(
            event_id=event_id,
            user_id=user_id,
            status="confirmed",
        )
        event.current_registrations += 1
        self.session.add(reg)
        await self.session.flush()
        return reg
