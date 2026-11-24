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

    async def search_semantic(
        self,
        query_vector: List[float],
        limit: int = 10,
        distance_threshold: float = 0.8,
        department: Optional[str] = None,
        industry: Optional[str] = None,
        country: Optional[str] = None,
        verified_only: bool = True,
        current_user_id: Optional[str] = None,
    ) -> List[Tuple[AlumniProfile, float]]:
        """
        Execute cosine distance semantic search (<=>) on alumni_profiles.embedding.
        Enforces authorized query scoping (visibility, active status, verification).
        Returns list of tuples: (AlumniProfile, similarity_score).
        """
        distance_expr = AlumniProfile.embedding.cosine_distance(query_vector).label("distance")
        stmt = (
            select(AlumniProfile, distance_expr)
            .join(AlumniProfile.user)
            .options(selectinload(AlumniProfile.user))
            .where(
                AlumniProfile.embedding.isnot(None),
                User.is_active == True,
                User.deleted_at.is_(None),
            )
        )

        # Authorized visibility scoping: institutional users see public & institutional
        if current_user_id:
            stmt = stmt.where(
                or_(
                    AlumniProfile.user_id == current_user_id,
                    AlumniProfile.visibility.in_(["public", "institutional"]),
                )
            )
        else:
            stmt = stmt.where(AlumniProfile.visibility.in_(["public", "institutional"]))

        if verified_only:
            stmt = stmt.where(User.is_verified == True)

        if department:
            stmt = stmt.where(AlumniProfile.major.ilike(f"%{department}%"))

        if industry:
            stmt = stmt.where(AlumniProfile.industry.ilike(f"%{industry}%"))

        stmt = (
            stmt.where(distance_expr <= distance_threshold)
            .order_by(distance_expr.asc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        rows = result.all()
        return [(row[0], round(1.0 - float(row[1]), 4)) for row in rows]

    async def update_embedding(self, profile_id: str, embedding: List[float]) -> bool:
        """Persist 1536-dim embedding vector for an alumni profile."""
        profile = await self.get_by_user_or_profile_id(profile_id)
        if not profile:
            return False
        profile.embedding = embedding
        await self.session.flush()
        return True

