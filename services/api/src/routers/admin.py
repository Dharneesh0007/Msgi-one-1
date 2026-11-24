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
from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, ConfigDict, Field
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.extended import VerificationDecisionRequest
from src.services.admin_service import (
    _ADMIN_AUDIT_LOGS_STORE,
    require_admin,
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


# ==============================================================================
# ADMIN AI PROVIDER CONTROL CENTRE (Encrypted Vault, Health & Usage Ledger)
# ==============================================================================

def _append_ai_audit(
    actor: AuthenticatedUser,
    action: str,
    target_type: str,
    target_id: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    import uuid as _uuid_mod
    _ADMIN_AUDIT_LOGS_STORE.append({
        "id": f"audit-{_uuid_mod.uuid4().hex[:10]}",
        "admin_id": actor.id,
        "admin_email": actor.email,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

class AdminAIProviderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    config_id: Optional[str] = Field(None, max_length=64)
    provider: str = Field(..., pattern="^(gemini|openai|anthropic|deepseek)$")
    display_name: str = Field(..., min_length=2, max_length=120)
    model_id: str = Field(..., min_length=2, max_length=120)
    api_key: str = Field(..., min_length=6, max_length=512)
    is_enabled: bool = True
    is_primary: bool = False
    fallback_priority: int = Field(default=100, ge=1, le=1000)
    daily_budget_usd: Optional[float] = Field(default=25.0, ge=0.0, le=10000.0)
    monthly_budget_usd: Optional[float] = Field(default=300.0, ge=0.0, le=100000.0)
    requests_per_minute_limit: Optional[int] = Field(default=60, ge=1, le=10000)


class AdminAIKeyRotateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: str = Field(..., min_length=6, max_length=512)


@router.get(
    "/ai/providers",
    response_model=StandardEnvelope[List[Dict[str, Any]]],
    summary="List Configured AI Providers (Masked Keys Only)",
)
def list_ai_providers_admin(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[Dict[str, Any]]]:
    require_admin(current_user)
    from src.ai.vault import list_provider_configs
    items = [cfg.to_safe_dict() for cfg in list_provider_configs(include_disabled=True)]
    return StandardEnvelope[List[Dict[str, Any]]](
        status="success",
        data=items,
        timestamp=datetime.now(timezone.utc),
        meta={"count": len(items)},
    )


@router.post(
    "/ai/providers",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Create or Update Encrypted AI Provider Config",
)
def upsert_ai_provider_admin(
    payload: AdminAIProviderCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    require_admin(current_user)
    from src.ai.vault import upsert_provider_config

    rec = upsert_provider_config(
        config_id=payload.config_id,
        provider=payload.provider,
        display_name=payload.display_name,
        model_id=payload.model_id,
        api_key=payload.api_key,
        configured_by=current_user.id,
        is_enabled=payload.is_enabled,
        is_primary=payload.is_primary,
        fallback_priority=payload.fallback_priority,
        daily_budget_usd=payload.daily_budget_usd,
        monthly_budget_usd=payload.monthly_budget_usd,
        requests_per_minute_limit=payload.requests_per_minute_limit,
    )
    _append_ai_audit(
        actor=current_user,
        action="ai_provider.upsert",
        target_type="ai_provider_config",
        target_id=rec.id,
        details={"provider": rec.provider, "model_id": rec.model_id, "key_hint": rec.key_hint},
    )
    return StandardEnvelope[Dict[str, Any]](
        status="success",
        data=rec.to_safe_dict(),
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/ai/providers/{config_id}/rotate-key",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Rotate Encrypted AI Provider API Key",
)
def rotate_ai_provider_key_admin(
    config_id: str = Path(..., description="AI provider config ID"),
    payload: AdminAIKeyRotateRequest = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    require_admin(current_user)
    from src.ai.vault import rotate_provider_key

    try:
        rec = rotate_provider_key(
            config_id=config_id,
            new_api_key=payload.api_key,
            configured_by=current_user.id,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "AI_PROVIDER_NOT_FOUND", "message": f"Provider config '{config_id}' not found."},
        )
    _append_ai_audit(
        actor=current_user,
        action="ai_provider.rotate_key",
        target_type="ai_provider_config",
        target_id=rec.id,
        details={"key_version": rec.key_version, "key_hint": rec.key_hint},
    )
    return StandardEnvelope[Dict[str, Any]](
        status="success",
        data=rec.to_safe_dict(),
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/ai/providers/{config_id}/verify",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Run Safe Connectivity Verification on AI Provider",
)
async def verify_ai_provider_admin(
    config_id: str = Path(..., description="AI provider config ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    require_admin(current_user)
    from src.ai.vault import get_provider_config
    from src.ai.multi_provider import verify_vault_provider

    cfg = get_provider_config(config_id)
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "AI_PROVIDER_NOT_FOUND", "message": f"Provider config '{config_id}' not found."},
        )
    health = await verify_vault_provider(cfg)
    _append_ai_audit(
        actor=current_user,
        action="ai_provider.verify",
        target_type="ai_provider_config",
        target_id=config_id,
        details={"healthy": health.healthy, "status": health.status},
    )
    return StandardEnvelope[Dict[str, Any]](
        status="success",
        data=health.model_dump(),
        timestamp=datetime.now(timezone.utc),
    )


@router.delete(
    "/ai/providers/{config_id}",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Revoke and Delete AI Provider Configuration",
)
def delete_ai_provider_admin(
    config_id: str = Path(..., description="AI provider config ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    require_admin(current_user)
    from src.ai.vault import delete_provider_config

    deleted = delete_provider_config(config_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "AI_PROVIDER_NOT_FOUND", "message": f"Provider config '{config_id}' not found."},
        )
    _append_ai_audit(
        actor=current_user,
        action="ai_provider.delete",
        target_type="ai_provider_config",
        target_id=config_id,
    )
    return StandardEnvelope[Dict[str, Any]](
        status="success",
        data={"deleted": True, "config_id": config_id},
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ai/usage",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Get AI Usage Ledger, Token & Cost Telemetry",
)
def get_ai_usage_admin(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    require_admin(current_user)
    from src.ai.multi_provider import get_usage_summary

    summary = get_usage_summary()
    return StandardEnvelope[Dict[str, Any]](
        status="success",
        data=summary,
        timestamp=datetime.now(timezone.utc),
    )
