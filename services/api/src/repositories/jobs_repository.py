"""
MSGI One — CareerBridge Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Abraham Silberschatz (Referential Invariants).
Manages Jobs, Applications, Duplicate Enforcement, and Opportunity Discovery.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models.core import Job, JobApplication
from src.repositories.base import BaseRepository


class JobsRepository(BaseRepository[Job]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Job, session)

    async def search_active_jobs(
        self,
        opportunity_type: Optional[str] = None,
        country: Optional[str] = None,
        workplace_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Job]:
        """Search active, non-expired job opportunities."""
        now = datetime.now(timezone.utc)
        stmt = select(Job).where(
            Job.is_active == True,
            or_(Job.application_deadline.is_(None), Job.application_deadline >= now),
        )

        if opportunity_type:
            stmt = stmt.where(Job.opportunity_type == opportunity_type)
        if country:
            stmt = stmt.where(Job.country.ilike(f"%{country}%"))
        if workplace_type:
            stmt = stmt.where(Job.workplace_type == workplace_type)

        stmt = stmt.order_by(Job.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_application(self, job_id: str, applicant_id: str) -> Optional[JobApplication]:
        """Find existing application to enforce UNIQUE(job_id, applicant_id)."""
        stmt = select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.applicant_id == applicant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_application(
        self,
        job_id: str,
        applicant_id: str,
        resume_url: Optional[str] = None,
        cover_note: Optional[str] = None,
    ) -> JobApplication:
        """Create new job application."""
        app = JobApplication(
            job_id=job_id,
            applicant_id=applicant_id,
            status="submitted",
            resume_url=resume_url,
            cover_note=cover_note,
        )
        self.session.add(app)
        await self.session.flush()
        return app

    async def get_user_applications(self, applicant_id: str) -> List[JobApplication]:
        """List all applications submitted by a user."""
        stmt = (
            select(JobApplication)
            .options(selectinload(JobApplication.job))
            .where(JobApplication.applicant_id == applicant_id)
            .order_by(JobApplication.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
