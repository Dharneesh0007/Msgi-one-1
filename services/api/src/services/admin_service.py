"""
MSGI One — Institutional Administration Domain Service (Module 12)
Manages credential verification queues, role provisioning, moderation reports,
announcements, operational health, and immutable audit logs.
Principles: Silberschatz Security Access Control & Pressman Quality Oversight.
"""

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from src.core.dependencies import AuthenticatedUser
from src.core.permissions import PermissionChecker, VALID_ROLES
from src.services.notifications_service import create_notification
from src.services.alumni_service import _SYNTHETIC_ALUMNI_STORE


# Path to seed CSVs
_SEED_DIR = Path(__file__).resolve().parents[4] / "supabase" / "seed" / "csv"
if not _SEED_DIR.exists():
    for p in Path(__file__).resolve().parents:
        if (p / "supabase" / "seed" / "csv").exists():
            _SEED_DIR = p / "supabase" / "seed" / "csv"
            break


class VerificationRequestItem(BaseModel):
    id: str
    user_id: str
    user_email: str
    user_name: str
    requested_role: str
    evidence_payload: Dict[str, Any]
    status: str  # 'pending', 'approved', 'rejected'
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: str
    decided_at: Optional[str] = None


class AdminAuditLogItem(BaseModel):
    id: str
    admin_id: str
    admin_email: str
    action: str
    target_type: str
    target_id: str
    details: Dict[str, Any]
    created_at: str


class AdminSummaryResponse(BaseModel):
    total_users: int
    pending_verifications_count: int
    active_alumni_count: int
    active_jobs_count: int
    active_mentors_count: int


class AdminUserRoleRecord(BaseModel):
    user_id: str
    email: str
    full_name: str
    roles: List[str]
    is_verified: bool


class ModerationReportItem(BaseModel):
    id: str
    reporter_id: str
    reported_user_id: str
    category: str
    description: str
    status: str
    reviewed_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None


class AnnouncementItem(BaseModel):
    id: str
    title: str
    body: str
    audience_role: str
    created_by: str
    created_at: str


def _load_all_verification_requests() -> List[Dict[str, Any]]:
    csv_file = _SEED_DIR / "verification_requests.csv"
    if not csv_file.exists():
        return [
            {
                "id": "vreq-001",
                "user_id": "user-candidate-001",
                "user_email": "candidate.alumni@example.msgi.edu",
                "user_name": "Daiki Shimizu",
                "requested_role": "alumni",
                "evidence_payload": {
                    "graduation_year": 2023,
                    "degree": "B.Tech Computer Science",
                    "student_id_verified": True,
                    "diploma_url": "https://credentials.example.msgi.edu/verify/daiki-2023",
                },
                "status": "pending",
                "reviewed_by": None,
                "review_notes": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "decided_at": None,
            }
        ]
    results = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            evidence = {}
            try:
                evidence = json.loads(row.get("evidence_payload", "{}"))
            except Exception:
                pass
            results.append({
                "id": row["request_id"],
                "user_id": row["user_id"],
                "user_email": row["user_email"],
                "user_name": row["user_name"],
                "requested_role": row["requested_role"],
                "evidence_payload": evidence,
                "status": row["status"],
                "reviewed_by": None,
                "review_notes": None,
                "created_at": row["created_at"],
                "decided_at": None,
            })
    return results


# In-memory stores conforming to public.verification_requests and public.admin_audit_logs
_VERIFICATION_REQUESTS_STORE: List[Dict[str, Any]] = _load_all_verification_requests()

_ADMIN_AUDIT_LOGS_STORE: List[Dict[str, Any]] = [
    {
        "id": "audit-001",
        "admin_id": "user-admin-001",
        "admin_email": "admin@example.msgi.edu",
        "action": "system_bootstrap",
        "target_type": "system",
        "target_id": "msgi-one-core",
        "details": {"note": "Initial operational state established."},
        "created_at": "2026-09-01T00:00:00Z",
    }
]

_ADMIN_USERS_DIRECTORY: Dict[str, Dict[str, Any]] = {
    "user-student-001": {
        "user_id": "user-student-001",
        "email": "alex.rivera@example.msgi.edu",
        "full_name": "Alex Rivera",
        "roles": ["student"],
        "is_verified": True,
    },
    "user-kenji-001": {
        "user_id": "user-kenji-001",
        "email": "kenji.sato@example.msgi.edu",
        "full_name": "Kenji Sato",
        "roles": ["alumni"],
        "is_verified": True,
    },
    "user-admin-001": {
        "user_id": "user-admin-001",
        "email": "sarah.jenkins@example.msgi.edu",
        "full_name": "Sarah Jenkins",
        "roles": ["admin"],
        "is_verified": True,
    },
}

_MODERATION_REPORTS_STORE: List[Dict[str, Any]] = []

_ANNOUNCEMENTS_STORE: List[Dict[str, Any]] = [
    {
        "id": "ann-001",
        "title": "Welcome to MSGI One Ecosystem V2",
        "body": "Verified alumni mentorship, career pathways, and institutional events are open for the 2026 academic term.",
        "audience_role": "all",
        "created_by": "user-admin-001",
        "created_at": "2026-11-01T09:00:00Z",
    }
]


def require_admin(user: AuthenticatedUser) -> None:
    if "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_ROLE_REQUIRED", "message": "This operation requires verified institutional administrator privileges."},
        )


def submit_verification_request(
    user: AuthenticatedUser,
    requested_role: str,
    evidence_payload: Dict[str, Any],
) -> VerificationRequestItem:
    if requested_role not in ("alumni", "faculty", "recruiter"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_VERIFICATION_ROLE", "message": "Verification requests support 'alumni', 'faculty', or 'recruiter'."},
        )

    existing_pending = next(
        (r for r in _VERIFICATION_REQUESTS_STORE if r["user_id"] == user.id and r["status"] == "pending"),
        None,
    )
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "VERIFICATION_ALREADY_PENDING", "message": "You already have a pending institutional verification request."},
        )

    if requested_role == "alumni":
        grad_year = evidence_payload.get("graduation_year")
        if not grad_year or not isinstance(grad_year, int) or grad_year < 1950 or grad_year > 2035:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "INVALID_GRADUATION_YEAR", "message": "A valid graduation_year (1950-2035) is required for alumni verification."},
            )
        if not evidence_payload.get("degree") or not evidence_payload.get("department"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "INCOMPLETE_ALUMNI_EVIDENCE", "message": "Both degree and department are required for alumni verification."},
            )

    req_id = f"vreq-{uuid.uuid4().hex[:10]}"
    full_name = f"{user.first_name or 'Institutional'} {user.last_name or 'Member'}".strip()
    record = {
        "id": req_id,
        "user_id": user.id,
        "user_email": user.email,
        "user_name": full_name,
        "requested_role": requested_role,
        "evidence_payload": evidence_payload,
        "status": "pending",
        "reviewed_by": None,
        "review_notes": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decided_at": None,
    }
    _VERIFICATION_REQUESTS_STORE.append(record)
    _ADMIN_USERS_DIRECTORY.setdefault(
        user.id,
        {
            "user_id": user.id,
            "email": user.email,
            "full_name": full_name,
            "roles": list(user.roles),
            "is_verified": user.is_verified,
        },
    )
    return VerificationRequestItem(**record)


def get_my_verification_requests(user: AuthenticatedUser) -> List[VerificationRequestItem]:
    items = [VerificationRequestItem(**r) for r in _VERIFICATION_REQUESTS_STORE if r["user_id"] == user.id]
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items


def list_pending_verifications(admin: AuthenticatedUser) -> List[VerificationRequestItem]:
    require_admin(admin)
    pending = [r for r in _VERIFICATION_REQUESTS_STORE if r["status"] == "pending"]
    return [VerificationRequestItem(**r) for r in pending]


def decide_verification(
    request_id: str,
    decision: str,  # 'approved' or 'rejected'
    admin: AuthenticatedUser,
    review_notes: Optional[str] = None,
) -> VerificationRequestItem:
    """
    Decides on a pending institutional credential verification.
    Enforces RBAC: Only admin role can review.
    Enforces anti-tampering: Administrators cannot self-verify their own user account.
    """
    require_admin(admin)

    req = next((r for r in _VERIFICATION_REQUESTS_STORE if r["id"] == request_id), None)
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REQUEST_NOT_FOUND", "message": f"Verification request '{request_id}' does not exist."},
        )

    # Anti-self-verification guard
    if req["user_id"] == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_VERIFICATION_FORBIDDEN", "message": "Institutional administrators cannot approve their own verification request."},
        )

    if decision not in ("approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_DECISION", "message": "Decision must be 'approved' or 'rejected'."},
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    req["status"] = decision
    req["reviewed_by"] = admin.id
    req["review_notes"] = review_notes
    req["decided_at"] = now_iso

    # If approved, update user's server-side roles and verification status
    if decision == "approved":
        updated_roles = PermissionChecker.grant_role(req["user_id"], req["requested_role"], mark_verified=True)
        if req["user_id"] in _ADMIN_USERS_DIRECTORY:
            _ADMIN_USERS_DIRECTORY[req["user_id"]]["roles"] = updated_roles
            _ADMIN_USERS_DIRECTORY[req["user_id"]]["is_verified"] = True
        for a in _SYNTHETIC_ALUMNI_STORE:
            if a.get("user_id") == req["user_id"]:
                a["is_verified"] = True

    # Record immutable audit log
    audit_id = f"audit-{uuid.uuid4().hex[:12]}"
    audit_entry = {
        "id": audit_id,
        "admin_id": admin.id,
        "admin_email": admin.email,
        "action": f"verify_user_{decision}",
        "target_type": "user",
        "target_id": req["user_id"],
        "details": {
            "requested_role": req["requested_role"],
            "decision": decision,
            "review_notes": review_notes,
        },
        "created_at": now_iso,
    }
    _ADMIN_AUDIT_LOGS_STORE.append(audit_entry)

    # Dispatch notification to the affected user
    create_notification(
        user_id=req["user_id"],
        event_type="verification_decided",
        entity_id=request_id,
        title="Institutional Verification Decided",
        message=f"Your {req['requested_role'].capitalize()} verification request was {decision}.",
        payload={"decision": decision, "role": req["requested_role"]},
    )

    return VerificationRequestItem(**req)


def get_admin_summary(admin: AuthenticatedUser) -> AdminSummaryResponse:
    require_admin(admin)
    pending_count = sum(1 for r in _VERIFICATION_REQUESTS_STORE if r["status"] == "pending")
    active_alumni_count = len(_SYNTHETIC_ALUMNI_STORE)
    return AdminSummaryResponse(
        total_users=max(len(_ADMIN_USERS_DIRECTORY), active_alumni_count + 12),
        pending_verifications_count=pending_count,
        active_alumni_count=active_alumni_count,
        active_jobs_count=3,
        active_mentors_count=2,
    )


def get_admin_audit_logs(admin: AuthenticatedUser) -> List[AdminAuditLogItem]:
    require_admin(admin)
    sorted_logs = sorted(_ADMIN_AUDIT_LOGS_STORE, key=lambda x: x["created_at"], reverse=True)
    return [AdminAuditLogItem(**l) for l in sorted_logs]


def list_users_for_admin(admin: AuthenticatedUser) -> List[AdminUserRoleRecord]:
    require_admin(admin)
    return [AdminUserRoleRecord(**u) for u in _ADMIN_USERS_DIRECTORY.values()]


def update_user_roles_by_admin(
    user_id: str,
    roles: List[str],
    is_verified: Optional[bool],
    admin: AuthenticatedUser,
) -> AdminUserRoleRecord:
    require_admin(admin)
    if not roles or any(r not in VALID_ROLES for r in roles):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ROLE", "message": f"All roles must be within {sorted(VALID_ROLES)}."},
        )
    if user_id == admin.id and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_DEMOTION_FORBIDDEN", "message": "Administrators cannot revoke their own admin role."},
        )

    applied_roles = PermissionChecker.set_user_roles(user_id, roles, is_verified=is_verified)
    entry = _ADMIN_USERS_DIRECTORY.setdefault(
        user_id,
        {
            "user_id": user_id,
            "email": f"{user_id}@example.msgi.edu",
            "full_name": user_id,
            "roles": applied_roles,
            "is_verified": bool(is_verified) if is_verified is not None else False,
        },
    )
    entry["roles"] = applied_roles
    if is_verified is not None:
        entry["is_verified"] = is_verified

    _ADMIN_AUDIT_LOGS_STORE.append({
        "id": f"audit-{uuid.uuid4().hex[:12]}",
        "admin_id": admin.id,
        "admin_email": admin.email,
        "action": "update_user_roles",
        "target_type": "user",
        "target_id": user_id,
        "details": {"roles": applied_roles, "is_verified": entry["is_verified"]},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return AdminUserRoleRecord(**entry)


def list_moderation_reports(admin: AuthenticatedUser) -> List[ModerationReportItem]:
    require_admin(admin)
    return [ModerationReportItem(**r) for r in _MODERATION_REPORTS_STORE]


def resolve_moderation_report(
    report_id: str,
    new_status: str,
    resolution_notes: Optional[str],
    admin: AuthenticatedUser,
) -> ModerationReportItem:
    require_admin(admin)
    if new_status not in ("under_review", "resolved", "dismissed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REPORT_STATUS", "message": "Status must be 'under_review', 'resolved', or 'dismissed'."},
        )
    report = next((r for r in _MODERATION_REPORTS_STORE if r["id"] == report_id), None)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_NOT_FOUND", "message": f"Report '{report_id}' not found."},
        )
    now_iso = datetime.now(timezone.utc).isoformat()
    report["status"] = new_status
    report["reviewed_by"] = admin.id
    report["resolution_notes"] = resolution_notes
    if new_status in ("resolved", "dismissed"):
        report["resolved_at"] = now_iso

    _ADMIN_AUDIT_LOGS_STORE.append({
        "id": f"audit-{uuid.uuid4().hex[:12]}",
        "admin_id": admin.id,
        "admin_email": admin.email,
        "action": f"moderation_report_{new_status}",
        "target_type": "user_report",
        "target_id": report_id,
        "details": {"resolution_notes": resolution_notes},
        "created_at": now_iso,
    })
    return ModerationReportItem(**report)


def list_announcements(user: AuthenticatedUser) -> List[AnnouncementItem]:
    return [
        AnnouncementItem(**a)
        for a in _ANNOUNCEMENTS_STORE
        if a["audience_role"] == "all" or a["audience_role"] in user.roles or "admin" in user.roles
    ]


def create_announcement(title: str, body: str, audience_role: str, admin: AuthenticatedUser) -> AnnouncementItem:
    require_admin(admin)
    ann = {
        "id": f"ann-{uuid.uuid4().hex[:10]}",
        "title": title.strip(),
        "body": body.strip(),
        "audience_role": audience_role,
        "created_by": admin.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _ANNOUNCEMENTS_STORE.insert(0, ann)
    _ADMIN_AUDIT_LOGS_STORE.append({
        "id": f"audit-{uuid.uuid4().hex[:12]}",
        "admin_id": admin.id,
        "admin_email": admin.email,
        "action": "publish_announcement",
        "target_type": "announcement",
        "target_id": ann["id"],
        "details": {"audience_role": audience_role, "title": ann["title"]},
        "created_at": ann["created_at"],
    })
    return AnnouncementItem(**ann)


def get_operational_status(admin: AuthenticatedUser) -> Dict[str, Any]:
    require_admin(admin)
    return {
        "api_status": "healthy",
        "user_skills_rls_enabled": PermissionChecker.is_user_skills_retrieval_enabled(),
        "pending_verifications": sum(1 for r in _VERIFICATION_REQUESTS_STORE if r["status"] == "pending"),
        "open_reports": sum(1 for r in _MODERATION_REPORTS_STORE if r["status"] in ("pending", "under_review")),
        "audit_log_entries": len(_ADMIN_AUDIT_LOGS_STORE),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
