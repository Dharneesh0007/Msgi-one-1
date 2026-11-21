"""
MSGI One — Institutional Administration Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Abraham Silberschatz (Audit Trail & Verification Lifecycle).
Manages Verification Requests, Administrative Actions, and Audit Logs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.extended import VerificationRequest, AdminAuditLog
from src.repositories.base import BaseRepository


class AdminRepository(BaseRepository[VerificationRequest]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VerificationRequest, session)

    async def list_pending_verifications(
        self,
        requested_role: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[VerificationRequest]:
        """List pending identity verification requests for admin review."""
        stmt = select(VerificationRequest).where(VerificationRequest.status == "pending")
        if requested_role:
            stmt = stmt.where(VerificationRequest.requested_role == requested_role)
        stmt = stmt.order_by(VerificationRequest.created_at.asc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def decide_verification(
        self,
        request_id: str,
        admin_id: str,
        status: str,
        review_notes: Optional[str] = None,
    ) -> Optional[VerificationRequest]:
        """Approve or reject a verification request."""
        req = await self.get_by_id(request_id)
        if not req:
            return None
        req.status = status
        req.reviewed_by = admin_id
        req.review_notes = review_notes
        req.decided_at = datetime.now(timezone.utc)
        await self.session.flush()
        return req

    async def log_admin_action(
        self,
        admin_id: str,
        action: str,
        target_type: str,
        target_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AdminAuditLog:
        """Create immutable administrative audit record."""
        log_entry = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
        )
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry
