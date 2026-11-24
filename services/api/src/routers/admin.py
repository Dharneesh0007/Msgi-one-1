"""
MSGI One — Institutional Administration API Router (Module 12)
Endpoints:
  GET   /api/v1/admin/verifications
  POST  /api/v1/admin/verifications/{id}/decision
  GET   /api/v1/admin/summary
  GET   /api/v1/admin/audit-logs
  GET   /api/v1/admin/users
  POST  /api/v1/admin/users/{user_id}/roles
  GET   /api/v1/admin/reports
  PATCH /api/v1/admin/reports/{report_id}
  GET   /api/v1/admin/announcements
  POST  /api/v1/admin/announcements
  GET   /api/v1/admin/status
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, ConfigDict, Field
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.extended import VerificationDecisionRequest
from src.services.admin_service import (
    list_pending_verifications,
    decide_verification,
    get_admin_summary,
    get_admin_audit_logs,
    list_users_for_admin,
    update_user_roles_by_admin,
    list_moderation_reports,
    resolve_moderation_report,
    list_announcements,
    create_announcement,
    get_operational_status,
    VerificationRequestItem,
    AdminSummaryResponse,
    AdminAuditLogItem,
    AdminUserRoleRecord,
    ModerationReportItem,
    AnnouncementItem,
)

router = APIRouter(prefix="/admin", tags=["Institutional Administration"])


class AdminRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    roles: List[str] = Field(..., min_length=1)
    is_verified: Optional[bool] = None


class ModerationDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(..., pattern="^(under_review|resolved|dismissed)$")
    resolution_notes: Optional[str] = Field(None, max_length=1000)


class AnnouncementCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(..., min_length=3, max_length=200)
    body: str = Field(..., min_length=10, max_length=3000)
    audience_role: str = Field(default="all", pattern="^(all|student|alumni|faculty|recruiter)$")


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


@router.get(
    "/users",
    response_model=StandardEnvelope[List[AdminUserRoleRecord]],
    summary="List Users & Assigned Roles",
)
def get_admin_users(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[AdminUserRoleRecord]]:
    users = list_users_for_admin(admin=current_user)
    return StandardEnvelope(status="success", data=users, timestamp=datetime.now(timezone.utc))


@router.post(
    "/users/{user_id}/roles",
    response_model=StandardEnvelope[AdminUserRoleRecord],
    summary="Provision or Update User Roles",
)
def set_user_roles(
    user_id: str,
    payload: AdminRoleUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[AdminUserRoleRecord]:
    updated = update_user_roles_by_admin(
        user_id=user_id,
        roles=payload.roles,
        is_verified=payload.is_verified,
        admin=current_user,
    )
    return StandardEnvelope(status="success", data=updated, timestamp=datetime.now(timezone.utc))


@router.get(
    "/reports",
    response_model=StandardEnvelope[List[ModerationReportItem]],
    summary="List User Moderation Reports",
)
def get_reports(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[ModerationReportItem]]:
    reports = list_moderation_reports(admin=current_user)
    return StandardEnvelope(status="success", data=reports, timestamp=datetime.now(timezone.utc))


@router.patch(
    "/reports/{report_id}",
    response_model=StandardEnvelope[ModerationReportItem],
    summary="Resolve or Dismiss Moderation Report",
)
def decide_report(
    report_id: str,
    payload: ModerationDecisionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[ModerationReportItem]:
    report = resolve_moderation_report(
        report_id=report_id,
        new_status=payload.status,
        resolution_notes=payload.resolution_notes,
        admin=current_user,
    )
    return StandardEnvelope(status="success", data=report, timestamp=datetime.now(timezone.utc))


@router.get(
    "/announcements",
    response_model=StandardEnvelope[List[AnnouncementItem]],
    summary="List Institutional Announcements",
)
def get_announcements(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[AnnouncementItem]]:
    items = list_announcements(user=current_user)
    return StandardEnvelope(status="success", data=items, timestamp=datetime.now(timezone.utc))


@router.post(
    "/announcements",
    response_model=StandardEnvelope[AnnouncementItem],
    summary="Publish Institutional Announcement",
)
def publish_announcement(
    payload: AnnouncementCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[AnnouncementItem]:
    item = create_announcement(
        title=payload.title,
        body=payload.body,
        audience_role=payload.audience_role,
        admin=current_user,
    )
    return StandardEnvelope(status="success", data=item, timestamp=datetime.now(timezone.utc))


@router.get(
    "/status",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Get Operational Status Summary",
)
def operational_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    data = get_operational_status(admin=current_user)
    return StandardEnvelope(status="success", data=data, timestamp=datetime.now(timezone.utc))
