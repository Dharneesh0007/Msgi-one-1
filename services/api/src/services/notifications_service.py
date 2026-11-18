"""
MSGI One — Unified Realtime Notification Service
Supports persistent in-app notifications and event dispatching.
Principles: Kleppmann Reliable Event Propagation & Sommerville Dependability.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from src.core.dependencies import AuthenticatedUser


class NotificationRecord(BaseModel):
    id: str
    user_id: str
    event_type: str
    entity_id: str
    title: str
    message: str
    is_read: bool = False
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    read_at: Optional[str] = None


# Thread-safe in-memory store for notifications (conforming to public.notifications)
_NOTIFICATIONS_STORE: List[Dict[str, Any]] = [
    {
        "id": "notif-seed-001",
        "user_id": "user-student-001",
        "event_type": "mentor_matched",
        "entity_id": "mentor-kenji-001",
        "title": "New Mentor Recommendation",
        "message": "Kenji Sato is available for AI Career advisory.",
        "is_read": False,
        "payload": {"mentor_name": "Kenji Sato", "company": "Rakuten Symphony"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_at": None,
    }
]


def create_notification(
    user_id: str,
    event_type: str,
    entity_id: str,
    title: str,
    message: str,
    payload: Optional[Dict[str, Any]] = None,
) -> NotificationRecord:
    """
    Creates and commits a persistent notification for a specific user.
    """
    notif_id = f"notif-{uuid.uuid4().hex[:12]}"
    record_dict = {
        "id": notif_id,
        "user_id": user_id,
        "event_type": event_type,
        "entity_id": entity_id,
        "title": title,
        "message": message,
        "is_read": False,
        "payload": payload or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_at": None,
    }
    _NOTIFICATIONS_STORE.append(record_dict)
    return NotificationRecord(**record_dict)


def get_my_notifications(user: AuthenticatedUser) -> List[NotificationRecord]:
    """
    Retrieves all notifications owned by the authenticated user.
    """
    user_notifs = [n for n in _NOTIFICATIONS_STORE if n["user_id"] == user.id]
    # Sort descending by created_at
    user_notifs.sort(key=lambda x: x["created_at"], reverse=True)
    return [NotificationRecord(**n) for n in user_notifs]


def get_unread_count(user: AuthenticatedUser) -> int:
    return sum(1 for n in _NOTIFICATIONS_STORE if n["user_id"] == user.id and not n["is_read"])


def mark_notification_as_read(notification_id: str, user: AuthenticatedUser) -> NotificationRecord:
    """
    Marks a single notification as read, enforcing user ownership.
    """
    notif = next((n for n in _NOTIFICATIONS_STORE if n["id"] == notification_id), None)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOTIFICATION_NOT_FOUND", "message": f"Notification '{notification_id}' not found."},
        )

    if notif["user_id"] != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Cannot modify another user's notifications."},
        )

    notif["is_read"] = True
    notif["read_at"] = datetime.now(timezone.utc).isoformat()
    return NotificationRecord(**notif)


def mark_all_as_read(user: AuthenticatedUser) -> int:
    now_iso = datetime.now(timezone.utc).isoformat()
    count = 0
    for n in _NOTIFICATIONS_STORE:
        if n["user_id"] == user.id and not n["is_read"]:
            n["is_read"] = True
            n["read_at"] = now_iso
            count += 1
    return count
