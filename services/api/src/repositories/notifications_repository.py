"""
MSGI One — Realtime Notifications Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Kleppmann (Append-Only Event Notification Log).
Manages Owner-Isolated Notifications, Read Receipts, and Realtime Delivery Persistence.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.extended import Notification
from src.repositories.base import BaseRepository


class NotificationsRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Notification, session)

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Retrieve notifications isolated to the authenticated user."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: str, user_id: str) -> Optional[Notification]:
        """Mark a notification as read with ownership verification."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        notif = result.scalars().first()
        if not notif:
            return None
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        await self.session.flush()
        return notif

    async def create_notification(
        self,
        user_id: str,
        event_type: str,
        entity_id: str,
        title: str,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create new owner-isolated notification."""
        notif = Notification(
            user_id=user_id,
            event_type=event_type,
            entity_id=entity_id,
            title=title,
            message=message,
            payload=payload or {},
        )
        self.session.add(notif)
        await self.session.flush()
        return notif
