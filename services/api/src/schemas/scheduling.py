"""
MSGI One — Scheduling & Meeting Pydantic v2 Schemas (Phase 5)
Conforms to API_CONTRACT_V2.md and Elmasri/Kleppmann transactional integrity.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def validate_iana_timezone(tz_name: str) -> str:
    try:
        ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid IANA timezone: '{tz_name}'") from exc
    return tz_name


class AvailabilityExceptionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    available: bool = False
    reason: Optional[str] = Field(default=None, max_length=200)


class AvailabilityWindowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday .. 6=Sunday")
    start_time_local: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time_local: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    timezone: str = Field(default="UTC", max_length=64)
    slot_duration_minutes: int = Field(default=30)
    buffer_minutes: int = Field(default=10, ge=0, le=60)
    exceptions: List[AvailabilityExceptionInput] = Field(default_factory=list)

    @field_validator("timezone")
    @classmethod
    def _check_tz(cls, v: str) -> str:
        return validate_iana_timezone(v)

    @field_validator("slot_duration_minutes")
    @classmethod
    def _check_duration(cls, v: int) -> int:
        if v not in (15, 30, 45, 60, 90):
            raise ValueError("slot_duration_minutes must be one of 15, 30, 45, 60, 90")
        return v

    @model_validator(mode="after")
    def _check_window_order(self) -> "AvailabilityWindowInput":
        if self.end_time_local <= self.start_time_local:
            raise ValueError("end_time_local must be strictly after start_time_local")
        return self


class AvailabilityUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    windows: List[AvailabilityWindowInput] = Field(..., min_length=1, max_length=21)


class AvailabilityWindowResponse(BaseModel):
    id: str
    alumni_id: str
    day_of_week: int
    start_time_local: str
    end_time_local: str
    timezone: str
    slot_duration_minutes: int
    buffer_minutes: int
    exceptions: List[Dict[str, Any]] = Field(default_factory=list)


class OpenSlotDTO(BaseModel):
    start_utc: datetime
    end_utc: datetime
    alumni_timezone: str
    local_label: str


class ProposedSlotInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_utc: datetime
    end_utc: datetime

    @model_validator(mode="after")
    def _check_utc(self) -> "ProposedSlotInput":
        if self.start_utc.tzinfo is None or self.end_utc.tzinfo is None:
            raise ValueError("Timestamps must be timezone-aware ISO-8601 UTC/offset datetimes")
        if self.end_utc <= self.start_utc:
            raise ValueError("end_utc must be strictly after start_utc")
        return self


class MeetingRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alumni_id: str
    mentor_request_id: Optional[str] = None
    title: str = Field(..., min_length=3, max_length=200)
    purpose: str = Field(..., min_length=5, max_length=2000)
    duration_minutes: int = Field(default=30)
    student_timezone: str = Field(default="UTC", max_length=64)
    proposed_slots: List[ProposedSlotInput] = Field(..., min_length=1, max_length=3)

    @field_validator("student_timezone")
    @classmethod
    def _check_student_tz(cls, v: str) -> str:
        return validate_iana_timezone(v)

    @field_validator("duration_minutes")
    @classmethod
    def _check_dur(cls, v: int) -> int:
        if v not in (15, 30, 45, 60, 90):
            raise ValueError("duration_minutes must be one of 15, 30, 45, 60, 90")
        return v


class MeetingSlotResponse(BaseModel):
    id: str
    meeting_request_id: str
    proposed_by: str
    round_number: int
    start_utc: datetime
    end_utc: datetime
    status: str


class MeetingRequestAccept(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot_id: str


class MeetingRequestDecline(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Optional[str] = Field(default=None, max_length=500)


class MeetingRequestCounterPropose(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposed_slots: List[ProposedSlotInput] = Field(..., min_length=1, max_length=3)
    note: Optional[str] = Field(default=None, max_length=500)


class MeetingRequestConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot_id: str


class MeetingRequestResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    alumni_id: str
    alumni_name: str
    mentor_request_id: Optional[str] = None
    title: str
    purpose: str
    duration_minutes: int
    student_timezone: str
    status: str
    decline_reason: Optional[str] = None
    slots: List[MeetingSlotResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MeetingRescheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_start_utc: datetime
    new_end_utc: datetime
    reason: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _check_dates(self) -> "MeetingRescheduleRequest":
        if self.new_start_utc.tzinfo is None or self.new_end_utc.tzinfo is None:
            raise ValueError("Reschedule timestamps must be timezone-aware")
        if self.new_end_utc <= self.new_start_utc:
            raise ValueError("new_end_utc must be after new_start_utc")
        return self


class MeetingCancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Optional[str] = Field(default=None, max_length=500)


class MeetingFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback: Optional[str] = Field(default=None, max_length=1000)
    alumni_notes: Optional[str] = Field(default=None, max_length=1000)


class MeetingResponse(BaseModel):
    id: str
    meeting_request_id: Optional[str] = None
    student_id: str
    student_name: str
    alumni_id: str
    alumni_name: str
    title: str
    purpose: str
    scheduled_start: datetime
    scheduled_end: datetime
    status: str
    rescheduled_from_meeting_id: Optional[str] = None
    cancellation_reason: Optional[str] = None
    student_rating: Optional[int] = None
    student_feedback: Optional[str] = None
    alumni_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
