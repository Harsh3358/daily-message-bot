"""DeliveryLog repository for database queries on DeliveryLog entity."""
import uuid
from datetime import date, datetime, timezone
from typing import Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.delivery_log import DeliveryLog
from src.models.enums import DeliveryStatusEnum
from src.repositories.base import BaseRepository


class DeliveryLogRepository(BaseRepository[DeliveryLog]):
    """Repository handling database operations for DeliveryLog."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DeliveryLog, session)

    async def exists_successful_delivery(
        self,
        problem_id: uuid.UUID,
        telegram_group_id: uuid.UUID,
        delivery_date: date,
    ) -> bool:
        """Check if a successful delivery already exists for problem + group + date."""
        stmt = select(func.count()).select_from(DeliveryLog).where(
            DeliveryLog.problem_id == problem_id,
            DeliveryLog.telegram_group_id == telegram_group_id,
            DeliveryLog.delivery_date == delivery_date,
            DeliveryLog.status == DeliveryStatusEnum.SUCCESS,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def record_delivery_attempt(
        self,
        problem_id: uuid.UUID,
        telegram_group_id: uuid.UUID,
        delivery_date: date,
        status: DeliveryStatusEnum,
        telegram_message_id: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> DeliveryLog:
        """Persist a delivery attempt record."""
        log = DeliveryLog(
            problem_id=problem_id,
            telegram_group_id=telegram_group_id,
            delivery_date=delivery_date,
            status=status,
            telegram_message_id=telegram_message_id,
            error_message=error_message,
            sent_at=datetime.now(timezone.utc) if status == DeliveryStatusEnum.SUCCESS else None,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def list_paginated(
        self,
        problem_id: Optional[uuid.UUID] = None,
        telegram_group_id: Optional[uuid.UUID] = None,
        delivery_date: Optional[date] = None,
        status: Optional[DeliveryStatusEnum] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[DeliveryLog], int]:
        """Fetch filtered delivery logs with total count for pagination."""
        query = select(DeliveryLog)
        count_query = select(func.count()).select_from(DeliveryLog)

        if problem_id is not None:
            query = query.where(DeliveryLog.problem_id == problem_id)
            count_query = count_query.where(DeliveryLog.problem_id == problem_id)

        if telegram_group_id is not None:
            query = query.where(DeliveryLog.telegram_group_id == telegram_group_id)
            count_query = count_query.where(DeliveryLog.telegram_group_id == telegram_group_id)

        if delivery_date is not None:
            query = query.where(DeliveryLog.delivery_date == delivery_date)
            count_query = count_query.where(DeliveryLog.delivery_date == delivery_date)

        if status is not None:
            query = query.where(DeliveryLog.status == status)
            count_query = count_query.where(DeliveryLog.status == status)

        query = query.order_by(DeliveryLog.created_at.desc()).offset(skip).limit(limit)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        items_result = await self.session.execute(query)
        items = items_result.scalars().all()

        return items, total
