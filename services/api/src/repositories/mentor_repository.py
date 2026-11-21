"""
MSGI One — MentorMatch Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Abraham Silberschatz (Capacity Invariants).
Manages Mentor Profiles, Mentorship Requests, and Status Lifecycles.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models.core import MentorProfile, MentorRequest
from src.db.models.user import AlumniProfile, User
from src.repositories.base import BaseRepository


class MentorRepository(BaseRepository[MentorProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(MentorProfile, session)

    async def list_available_mentors(
        self,
        topic: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MentorProfile]:
        """Query mentors who are accepting requests and have remaining capacity."""
        stmt = (
            select(MentorProfile)
            .where(
                MentorProfile.is_accepting_requests == True,
                MentorProfile.current_active_mentees < MentorProfile.max_active_mentees,
            )
            .order_by(MentorProfile.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_request(self, mentor_id: str, student_id: str) -> Optional[MentorRequest]:
        """Check for existing pending request to enforce uq_active_mentor_request."""
        stmt = select(MentorRequest).where(
            MentorRequest.mentor_id == mentor_id,
            MentorRequest.student_id == student_id,
            MentorRequest.status == "pending",
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_request(
        self,
        mentor_id: str,
        student_id: str,
        topic: str,
        career_goal: str,
        message: Optional[str] = None,
    ) -> MentorRequest:
        """Create new pending mentorship request."""
        req = MentorRequest(
            mentor_id=mentor_id,
            student_id=student_id,
            topic=topic,
            career_goal=career_goal,
            message=message,
            status="pending",
        )
        self.session.add(req)
        await self.session.flush()
        return req

    async def get_user_requests(self, user_id: str) -> List[MentorRequest]:
        """List all requests involving this user (either as student or mentor)."""
        # Find mentor_profile for this user if exists
        mentor_prof = await self.session.execute(
            select(MentorProfile.id).where(MentorProfile.user_id == user_id)
        )
        mentor_profile_id = mentor_prof.scalars().first()

        conditions = [MentorRequest.student_id == user_id]
        if mentor_profile_id:
            conditions.append(MentorRequest.mentor_id == mentor_profile_id)

        stmt = (
            select(MentorRequest)
            .options(selectinload(MentorRequest.mentor))
            .where(or_(*conditions))
            .order_by(MentorRequest.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
