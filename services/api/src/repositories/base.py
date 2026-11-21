"""
MSGI One — Generic Asynchronous Base Repository
Principle: Martin Fowler (Repository Pattern) & Abraham Silberschatz (ACID Operations).
Provides typed asynchronous CRUD, pagination, and transactional query execution on top of SQLAlchemy 2.0.
"""

from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async repository encapsulating data access logic for SQLAlchemy 2.0 models."""

    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: Any) -> Optional[ModelT]:
        """Fetch a single entity by its primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalars().first()

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> Sequence[ModelT]:
        """List entities matching simple equality filters with pagination."""
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self, **filters: Any) -> int:
        """Count entities matching optional equality filters."""
        query = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelT:
        """Create and stage a new entity instance."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, entity_id: Any, **kwargs: Any) -> Optional[ModelT]:
        """Update existing entity attributes and flush."""
        instance = await self.get_by_id(entity_id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, entity_id: Any) -> bool:
        """Delete an entity by its primary key."""
        instance = await self.get_by_id(entity_id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
