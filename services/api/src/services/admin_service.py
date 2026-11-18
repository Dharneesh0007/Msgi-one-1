"""
MSGI One — Institutional Administration Domain Service (Module 12)
Manages credential verification queues, role provisioning, and audit logs.
Principles: Silberschatz Security Access Control & Pressman Quality Oversight.
"""

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from src.core.dependencies import AuthenticatedUser
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


def require_admin(user: AuthenticatedUser) -> None:
    if "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_ROLE_REQUIRED", "message": "This operation requires verified institutional administrator privileges."},
        )


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

    # If approved, update user's verification status in synthetic stores
    if decision == "approved":
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
        total_users=active_alumni_count + 12,
        pending_verifications_count=pending_count,
        active_alumni_count=active_alumni_count,
        active_jobs_count=3,
        active_mentors_count=2,
    )


def get_admin_audit_logs(admin: AuthenticatedUser) -> List[AdminAuditLogItem]:
    require_admin(admin)
    sorted_logs = sorted(_ADMIN_AUDIT_LOGS_STORE, key=lambda x: x["created_at"], reverse=True)
    return [AdminAuditLogItem(**l) for l in sorted_logs]
