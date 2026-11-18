"""
MSGI One — Institutional Administration API Router (Module 12)
Endpoints:
  GET  /api/v1/admin/verifications
  POST /api/v1/admin/verifications/{id}/decision
  GET  /api/v1/admin/summary
  GET  /api/v1/admin/audit-logs
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, status
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.extended import VerificationDecisionRequest
from src.services.admin_service import (
    list_pending_verifications,
    decide_verification,
    get_admin_summary,
    get_admin_audit_logs,
    VerificationRequestItem,
    AdminSummaryResponse,
    AdminAuditLogItem,
)

router = APIRouter(prefix="/admin", tags=["Institutional Administration"])


@router.get(
    "/verifications",
    response_model=StandardEnvelope[List[VerificationRequestItem]],
    summary="List Pending Institutional Verifications",
)
def get_pending_verifications(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[VerificationRequestItem]]:
    items = list_pending_verifications(admin=current_user)
    return StandardEnvelope[List[VerificationRequestItem]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"pending_count": len(items)},
    )


@router.post(
    "/verifications/{request_id}/decision",
    response_model=StandardEnvelope[VerificationRequestItem],
    summary="Decide Institutional Verification",
)
def review_verification(
    request_id: str = Path(..., description="Verification request ID"),
    request: VerificationDecisionRequest = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[VerificationRequestItem]:
    record = decide_verification(
        request_id=request_id,
        decision=request.decision,
        admin=current_user,
        review_notes=request.review_notes,
    )
    return StandardEnvelope[VerificationRequestItem](
        status="success",
        data=record,
        timestamp=datetime.now(timezone.utc),
        meta={"decision": request.decision},
    )


@router.get(
    "/summary",
    response_model=StandardEnvelope[AdminSummaryResponse],
    summary="Get Institutional Ecosystem Summary",
)
def get_summary(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[AdminSummaryResponse]:
    data = get_admin_summary(admin=current_user)
    return StandardEnvelope[AdminSummaryResponse](
        status="success",
        data=data,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/audit-logs",
    response_model=StandardEnvelope[List[AdminAuditLogItem]],
    summary="Get Immutable Administrative Audit Logs",
)
def get_audit_logs(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[AdminAuditLogItem]]:
    logs = get_admin_audit_logs(admin=current_user)
    return StandardEnvelope[List[AdminAuditLogItem]](
        status="success",
        data=logs,
        timestamp=datetime.now(timezone.utc),
        meta={"total_entries": len(logs)},
    )
