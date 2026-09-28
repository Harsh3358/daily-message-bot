"""Subject repository for database queries on Subject entity."""
from typing import Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.subject import Subject
from src.repositories.base import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    """Repository handling database operations for Subject."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Subject, session)

    async def get_by_name(self, name: str) -> Optional[Subject]:
        """Fetch subject by exact name."""
        stmt = select(Subject).where(Subject.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_slug(self, slug: str) -> Optional[Subject]:
        """Fetch subject by unique slug."""
        stmt = select(Subject).where(Subject.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_subjects(self) -> Sequence[Subject]:
        """Fetch all currently active subjects."""
        stmt = select(Subject).where(Subject.is_active.is_(True)).order_by(Subject.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_paginated(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[Subject], int]:
        """Fetch filtered subjects with total count for pagination."""
        query = select(Subject)
        count_query = select(func.count()).select_from(Subject)

        if is_active is not None:
            query = query.where(Subject.is_active == is_active)
            count_query = count_query.where(Subject.is_active == is_active)

        query = query.order_by(Subject.name).offset(skip).limit(limit)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        items_result = await self.session.execute(query)
        items = items_result.scalars().all()

        return items, total
