"""
MSGI One — Community & Interest Groups Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Abraham Silberschatz (Membership Invariants).
Manages Communities, Slugs, and Community Memberships.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models.extended import Community, CommunityMembership
from src.repositories.base import BaseRepository


class CommunityRepository(BaseRepository[Community]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Community, session)

    async def get_by_slug(self, slug: str) -> Optional[Community]:
        """Retrieve community by its unique slug."""
        stmt = (
            select(Community)
            .options(selectinload(Community.memberships))
            .where(Community.slug == slug)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_discoverable(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Community]:
        """List non-private communities with optional category filtering."""
        stmt = select(Community).where(Community.is_private == False)
        if category:
            stmt = stmt.where(Community.category.ilike(f"%{category}%"))
        stmt = stmt.order_by(Community.member_count.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_membership(self, community_id: str, user_id: str) -> Optional[CommunityMembership]:
        """Retrieve membership record."""
        stmt = select(CommunityMembership).where(
            CommunityMembership.community_id == community_id,
            CommunityMembership.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def join_community(self, community_id: str, user_id: str, role: str = "member") -> CommunityMembership:
        """Add user to community and increment member count."""
        comm = await self.get_by_id(community_id)
        if not comm:
            raise ValueError(f"Community {community_id} not found")

        membership = CommunityMembership(
            community_id=community_id,
            user_id=user_id,
            role=role,
            status="active",
        )
        comm.member_count += 1
        self.session.add(membership)
        await self.session.flush()
        return membership
