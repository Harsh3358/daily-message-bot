"""Generic Async SQLAlchemy 2.x Repository.

Async Concepts Explained:
- `await session.execute(stmt)`: Asynchronously runs the query statement against PostgreSQL
  without blocking the Python event loop.
- `result.scalars().all()`: Extracts the ORM model instances from the cursor result rows.
- `await session.commit()`: Commits the transaction to the database asynchronously.
- `await session.refresh(instance)`: Re-reads attributes from the database after a commit
  so that generated columns (e.g., `id`, `created_at`) are loaded on the instance.
"""
import uuid
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository providing standard CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id_: uuid.UUID) -> Optional[ModelType]:
        """Fetch a single record by its UUID primary key."""
        return await self.session.get(self.model, id_)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Fetch multiple records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Count total records for this model."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, instance: ModelType) -> ModelType:
        """Persist a new model instance."""
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType, update_data: Dict[str, Any]) -> ModelType:
        """Update an existing model instance with a dictionary of values."""
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete a model instance."""
        await self.session.delete(instance)
        await self.session.commit()
