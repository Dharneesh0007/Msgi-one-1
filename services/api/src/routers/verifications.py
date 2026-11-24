"""
MSGI One — Institutional Verification Router (Phase 3 & Phase 4)
Allows alumni, faculty, and recruiters to submit institutional credentials and inspect verification status.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.services.admin_service import (
    VerificationRequestItem,
    get_my_verification_requests,
    submit_verification_request,
)

router = APIRouter(prefix="/verifications", tags=["Institutional Verification"])


class VerificationSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requested_role: str = Field(default="alumni", pattern="^(alumni|faculty|recruiter)$")
    graduation_year: Optional[int] = Field(default=None, ge=1950, le=2035)
    degree: Optional[str] = Field(default=None, max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)
    organization: Optional[str] = Field(default=None, max_length=150)
    diploma_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=1000)


@router.get(
    "/me",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Get My Verification Status & Requests",
)
def get_my_verification_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    requests = get_my_verification_requests(current_user)
    if current_user.is_verified:
        overall = "approved"
    elif any(r.status == "pending" for r in requests):
        overall = "pending"
    elif any(r.status == "rejected" for r in requests):
        overall = "rejected"
    else:
        overall = "unverified"

    return StandardEnvelope(
        status="success",
        data={
            "overall_status": overall,
            "is_verified": current_user.is_verified,
            "roles": current_user.roles,
            "requests": [r.model_dump() for r in requests],
        },
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/me",
    response_model=StandardEnvelope[VerificationRequestItem],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Institutional Verification Request",
)
def submit_my_verification(
    payload: VerificationSubmissionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[VerificationRequestItem]:
    evidence: Dict[str, Any] = {
        k: v
        for k, v in payload.model_dump().items()
        if k != "requested_role" and v is not None
    }
    created = submit_verification_request(
        user=current_user,
        requested_role=payload.requested_role,
        evidence_payload=evidence,
    )
    return StandardEnvelope(
        status="success",
        data=created,
        timestamp=datetime.now(timezone.utc),
    )
