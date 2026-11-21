"""
MSGI One — User & Identity Asynchronous Repository
Principle: Martin Fowler (Repository Pattern) & Kleppmann (Single Source of Truth).
Manages persistence for Users, Roles, UserRoles, and Sub-type Profiles.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models.user import User, UserRole, Role, StudentProfile, AlumniProfile, UserPreference
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        result = await self.session.execute(
            select(User)
            .where(User.email == email.strip().lower())
            .options(
                selectinload(User.user_roles).joinedload(UserRole.role),
                selectinload(User.student_profile),
                selectinload(User.alumni_profile),
                selectinload(User.preferences),
            )
        )
        return result.scalars().first()

    async def get_with_relations(self, user_id: str) -> Optional[User]:
        """Fetch user by ID with eager loading of all profile relations."""
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_roles).joinedload(UserRole.role),
                selectinload(User.student_profile),
                selectinload(User.alumni_profile),
                selectinload(User.preferences),
            )
        )
        return result.scalars().first()

    async def update_profile_fields(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Optional[User]:
        """Update permitted profile attributes."""
        user = await self.get_with_relations(user_id)
        if not user:
            return None
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if avatar_url is not None:
            user.avatar_url = avatar_url
        await self.session.flush()
        return user
