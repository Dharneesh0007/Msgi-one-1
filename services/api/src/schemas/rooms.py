"""
MSGI One — Real-Time Audio/Video Meeting Room Pydantic v2 Schemas (Phase 7)
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RoomTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audio_enabled: bool = True
    video_enabled: bool = True


class MeetingParticipantDTO(BaseModel):
    user_id: str
    role: str
    admission_status: str
    audio_enabled: bool
    video_enabled: bool
    screen_sharing: bool
    joined_at: Optional[datetime] = None


class RoomTokenResponse(BaseModel):
    room_id: str
    meeting_id: str
    room_name: str
    livekit_url: Optional[str] = None
    token: str
    role: str
    admission_status: str
    waiting_room_enabled: bool
    recording_enabled: bool = False
    livekit_configured: bool = False
    expires_at: datetime


class RoomStateResponse(BaseModel):
    room_id: str
    meeting_id: str
    room_name: str
    status: str
    host_user_id: str
    waiting_room_enabled: bool
    recording_enabled: bool
    participants: List[MeetingParticipantDTO] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    expires_at: datetime


class ParticipantActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_user_id: str
