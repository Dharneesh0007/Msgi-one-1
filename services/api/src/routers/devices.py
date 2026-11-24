"""
MSGI One — Push Notification Device Token Registry Router (Phase 9)
Endpoints:
  POST   /api/v1/devices/push-token
  GET    /api/v1/devices/push-tokens
  DELETE /api/v1/devices/push-token/{token}
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, ConfigDict, Field

from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope

router = APIRouter(prefix="/devices", tags=["Push Devices"])


class PushTokenRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expo_push_token: str = Field(..., min_length=10, max_length=300)
    platform: str = Field(default="android", pattern="^(android|ios|web)$")
    device_name: Optional[str] = Field(None, max_length=120)


class PushTokenRecord(BaseModel):
    token: str
    user_id: str
    platform: str
    device_name: Optional[str] = None
    registered_at: str
    is_active: bool = True


_PUSH_TOKENS_STORE: Dict[str, PushTokenRecord] = {}


@router.post(
    "/push-token",
    response_model=StandardEnvelope[PushTokenRecord],
    summary="Register Expo Push Token for Authenticated User",
)
def register_push_token(
    payload: PushTokenRegisterRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[PushTokenRecord]:
    rec = PushTokenRecord(
        token=payload.expo_push_token.strip(),
        user_id=current_user.id,
        platform=payload.platform,
        device_name=payload.device_name,
        registered_at=datetime.now(timezone.utc).isoformat(),
        is_active=True,
    )
    _PUSH_TOKENS_STORE[f"{current_user.id}:{rec.token}"] = rec
    return StandardEnvelope[PushTokenRecord](
        status="success",
        data=rec,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/push-tokens",
    response_model=StandardEnvelope[List[PushTokenRecord]],
    summary="List Registered Devices for Current User",
)
def list_my_push_tokens(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[PushTokenRecord]]:
    mine = [r for r in _PUSH_TOKENS_STORE.values() if r.user_id == current_user.id and r.is_active]
    return StandardEnvelope[List[PushTokenRecord]](
        status="success",
        data=mine,
        timestamp=datetime.now(timezone.utc),
    )


@router.delete(
    "/push-token/{token}",
    response_model=StandardEnvelope[dict],
    summary="Revoke Expo Push Token on Logout",
)
def revoke_push_token(
    token: str = Path(..., description="Expo push token"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[dict]:
    key = f"{current_user.id}:{token}"
    existed = _PUSH_TOKENS_STORE.pop(key, None) is not None
    return StandardEnvelope[dict](
        status="success",
        data={"revoked": existed, "token": token},
        timestamp=datetime.now(timezone.utc),
    )
