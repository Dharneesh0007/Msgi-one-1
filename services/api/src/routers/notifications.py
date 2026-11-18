"""
MSGI One — Notifications API Router
Endpoints:
  GET   /api/v1/notifications
  GET   /api/v1/notifications/unread-count
  PATCH /api/v1/notifications/{id}/read
  POST  /api/v1/notifications/read-all
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, Path, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.services.notifications_service import (
    get_my_notifications,
    get_unread_count,
    mark_notification_as_read,
    mark_all_as_read,
    NotificationRecord,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=StandardEnvelope[List[NotificationRecord]],
    summary="List In-App Notifications",
)
def list_notifications(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[NotificationRecord]]:
    items = get_my_notifications(user=current_user)
    return StandardEnvelope[List[NotificationRecord]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"total": len(items)},
    )


@router.get(
    "/unread-count",
    response_model=StandardEnvelope[dict],
    summary="Get Unread Notification Count",
)
def get_unread(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[dict]:
    count = get_unread_count(user=current_user)
    return StandardEnvelope[dict](
        status="success",
        data={"unread_count": count},
        timestamp=datetime.now(timezone.utc),
    )


@router.patch(
    "/{notification_id}/read",
    response_model=StandardEnvelope[NotificationRecord],
    summary="Mark Notification as Read",
)
def mark_read(
    notification_id: str = Path(..., description="Notification ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[NotificationRecord]:
    record = mark_notification_as_read(notification_id=notification_id, user=current_user)
    return StandardEnvelope[NotificationRecord](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/read-all",
    response_model=StandardEnvelope[dict],
    summary="Mark All Notifications as Read",
)
def mark_all_read(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[dict]:
    count = mark_all_as_read(user=current_user)
    return StandardEnvelope[dict](
        status="success",
        data={"marked_read": count},
        timestamp=datetime.now(timezone.utc),
    )
