"""
MSGI One — Learning Academy Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Abraham Silberschatz (Courseware & Enrollment Integrity).
Manages Learning Resources, Course Enrollments, and Student Skills.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.ai import LearningResource, StudentSkill
from src.db.models.extended import CourseEnrollment
from src.repositories.base import BaseRepository


class LearningRepository(BaseRepository[LearningResource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(LearningResource, session)

    async def list_by_skill_and_difficulty(
        self,
        target_skill: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[LearningResource]:
        """List courseware filtered by skill and difficulty."""
        stmt = select(LearningResource)
        if target_skill:
            stmt = stmt.where(LearningResource.target_skill.ilike(f"%{target_skill}%"))
        if difficulty:
            stmt = stmt.where(LearningResource.difficulty == difficulty)

        stmt = stmt.order_by(LearningResource.rating.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_enrollments(self, user_id: str) -> List[CourseEnrollment]:
        """Get all course enrollments for a user."""
        stmt = (
            select(CourseEnrollment)
            .where(CourseEnrollment.user_id == user_id)
            .order_by(CourseEnrollment.enrolled_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_enrollment(self, user_id: str, resource_id: str) -> Optional[CourseEnrollment]:
        """Fetch enrollment record."""
        stmt = select(CourseEnrollment).where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.resource_id == resource_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def enroll(self, user_id: str, resource_id: str) -> CourseEnrollment:
        """Enroll user in courseware."""
        enrollment = CourseEnrollment(
            user_id=user_id,
            resource_id=resource_id,
            status="enrolled",
            progress_percentage=0,
        )
        self.session.add(enrollment)
        await self.session.flush()
        return enrollment
