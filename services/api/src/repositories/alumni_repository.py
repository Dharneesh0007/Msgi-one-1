"""
MSGI One — Alumni Discovery Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Abraham Silberschatz (Relational Query Filtering).
Performs directory filtering, multi-parameter searches, and privacy masking.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models.user import AlumniProfile, User, AlumniLocation
from src.repositories.base import BaseRepository


class AlumniRepository(BaseRepository[AlumniProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AlumniProfile, session)

    async def search_directory(
        self,
        query: Optional[str] = None,
        department: Optional[str] = None,
        industry: Optional[str] = None,
        country: Optional[str] = None,
        graduation_year: Optional[int] = None,
        verified_only: bool = True,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[AlumniProfile], int]:
        """Execute parameterized alumni search across PostgreSQL."""
        stmt = (
            select(AlumniProfile)
            .join(AlumniProfile.user)
            .options(
                selectinload(AlumniProfile.user),
            )
            .where(User.is_active == True, User.deleted_at.is_(None))
        )

        if verified_only:
            stmt = stmt.where(User.is_verified == True)

        if graduation_year:
            stmt = stmt.where(AlumniProfile.graduation_year == graduation_year)

        if department:
            stmt = stmt.where(AlumniProfile.major.ilike(f"%{department}%"))

        if industry:
            stmt = stmt.where(AlumniProfile.industry.ilike(f"%{industry}%"))

        if query:
            search_clause = or_(
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
                AlumniProfile.headline.ilike(f"%{query}%"),
                AlumniProfile.current_company.ilike(f"%{query}%"),
                AlumniProfile.major.ilike(f"%{query}%"),
            )
            stmt = stmt.where(search_clause)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Paginate
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_user_or_profile_id(self, identifier: str) -> Optional[AlumniProfile]:
        """Retrieve alumni profile by profile ID or user ID."""
        stmt = (
            select(AlumniProfile)
            .join(AlumniProfile.user)
            .options(selectinload(AlumniProfile.user))
            .where(or_(AlumniProfile.id == identifier, AlumniProfile.user_id == identifier))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
