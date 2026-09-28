"""Problem repository for database queries on Problem entity."""
import uuid
from datetime import date
from typing import Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.enums import DifficultyEnum
from src.models.problem import Problem
from src.repositories.base import BaseRepository


class ProblemRepository(BaseRepository[Problem]):
    """Repository handling database operations for Problem."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Problem, session)

    async def get_by_subject_and_date(
        self,
        subject_id: uuid.UUID,
        scheduled_date: date,
    ) -> Optional[Problem]:
        """Fetch problem scheduled for a subject on a specific date."""
        stmt = select(Problem).where(
            Problem.subject_id == subject_id,
            Problem.scheduled_date == scheduled_date,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_problem_for_subject(
        self,
        subject_id: uuid.UUID,
        scheduled_date: date,
    ) -> Optional[Problem]:
        """Fetch active problem for a subject on a given date for delivery."""
        stmt = select(Problem).where(
            Problem.subject_id == subject_id,
            Problem.scheduled_date == scheduled_date,
            Problem.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_paginated(
        self,
        subject_id: Optional[uuid.UUID] = None,
        scheduled_date: Optional[date] = None,
        difficulty: Optional[DifficultyEnum] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[Problem], int]:
        """Fetch filtered problems with total count for pagination."""
        query = select(Problem)
        count_query = select(func.count()).select_from(Problem)

        if subject_id is not None:
            query = query.where(Problem.subject_id == subject_id)
            count_query = count_query.where(Problem.subject_id == subject_id)

        if scheduled_date is not None:
            query = query.where(Problem.scheduled_date == scheduled_date)
            count_query = count_query.where(Problem.scheduled_date == scheduled_date)

        if difficulty is not None:
            query = query.where(Problem.difficulty == difficulty)
            count_query = count_query.where(Problem.difficulty == difficulty)

        if is_active is not None:
            query = query.where(Problem.is_active == is_active)
            count_query = count_query.where(Problem.is_active == is_active)

        query = query.order_by(Problem.scheduled_date.desc(), Problem.created_at.desc()).offset(skip).limit(limit)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        items_result = await self.session.execute(query)
        items = items_result.scalars().all()

        return items, total
