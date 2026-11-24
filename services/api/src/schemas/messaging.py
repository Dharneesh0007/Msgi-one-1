"""
MSGI One — Real-Time Messaging & Safety Pydantic v2 Schemas (Phase 6)
Conforms to API_CONTRACT_V2.md and Kurose & Ross / Kleppmann reliability contracts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_ATTACHMENT_MIMES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
PROHIBITED_EXTENSIONS = {".exe", ".sh", ".bat", ".cmd", ".ps1", ".js", ".msi", ".apk", ".vbs"}
MAX_ATTACHMENT_BYTES = 26_214_400  # 25 MB


class AttachmentUploadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_name: str = Field(..., min_length=1, max_length=255)
    mime_type: str = Field(..., min_length=3, max_length=128)
    size_bytes: int = Field(..., gt=0, le=MAX_ATTACHMENT_BYTES)
    sha256_checksum: str = Field(..., min_length=64, max_length=64)
    storage_path: str = Field(..., min_length=3, max_length=500)

    @field_validator("file_name")
    @classmethod
    def _check_filename(cls, v: str) -> str:
        lower = v.strip().lower()
        for ext in PROHIBITED_EXTENSIONS:
            if lower.endswith(ext):
                raise ValueError(f"Prohibited executable/script extension '{ext}' rejected for security.")
        return v.strip()

    @field_validator("mime_type")
    @classmethod
    def _check_mime(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ALLOWED_ATTACHMENT_MIMES:
            raise ValueError(f"Unsupported attachment MIME type '{cleaned}'.")
        return cleaned


class MessageAttachmentResponse(BaseModel):
    id: str
    message_id: str
    file_name: str
    mime_type: str
    size_bytes: int
    sha256_checksum: str
    storage_path: str
    scan_status: str
    created_at: datetime


class ConversationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient_id: str = Field(..., min_length=1, max_length=128)


class ConversationResponse(BaseModel):
    id: str
    peer_id: str
    peer_name: str
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    last_seq: int
    unread_count: int
    peer_online: bool = False
    created_at: datetime


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(..., min_length=1, max_length=4000)
    message_type: str = Field(default="text", pattern="^(text|attachment|system|meeting_invite)$")
    client_idempotency_key: Optional[str] = Field(default=None, max_length=128)
    reply_to_message_id: Optional[str] = None
    attachments: List[AttachmentUploadInput] = Field(default_factory=list, max_length=5)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    seq: int
    body: str
    message_type: str
    status: str
    client_idempotency_key: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    attachments: List[MessageAttachmentResponse] = Field(default_factory=list)
    created_at: datetime


class ReadReceiptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    last_read_seq: int = Field(..., ge=1)


class UserBlockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blocked_user_id: str = Field(..., min_length=1, max_length=128)
    reason: Optional[str] = Field(default=None, max_length=255)


class UserReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reported_user_id: str = Field(..., min_length=1, max_length=128)
    message_id: Optional[str] = None
    category: str = Field(..., pattern="^(spam|harassment|impersonation|inappropriate|other)$")
    description: str = Field(..., min_length=5, max_length=2000)


class WSEventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    event_type: str
    schema_version: str = "1.0"
    conversation_id: Optional[str] = None
    sender_id: Optional[str] = None
    client_idempotency_key: Optional[str] = None
    server_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)
