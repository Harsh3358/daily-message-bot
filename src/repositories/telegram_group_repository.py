"""TelegramGroup repository for database queries on TelegramGroup entity."""
import uuid
from typing import Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.telegram_group import TelegramGroup
from src.repositories.base import BaseRepository


class TelegramGroupRepository(BaseRepository[TelegramGroup]):
    """Repository handling database operations for TelegramGroup."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TelegramGroup, session)

    async def get_by_chat_id(self, chat_id: int) -> Optional[TelegramGroup]:
        """Fetch group by Telegram 64-bit chat ID."""
        stmt = select(TelegramGroup).where(TelegramGroup.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_groups_for_subject(self, subject_id: uuid.UUID) -> Sequence[TelegramGroup]:
        """Fetch all active Telegram groups mapped to a specific subject."""
        stmt = (
            select(TelegramGroup)
            .where(
                TelegramGroup.subject_id == subject_id,
                TelegramGroup.is_active.is_(True),
            )
            .order_by(TelegramGroup.group_title)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def deactivate_group(self, group_id: uuid.UUID) -> Optional[TelegramGroup]:
        """Mark a group as inactive (e.g. when bot is kicked from the group)."""
        group = await self.get_by_id(group_id)
        if group:
            group.is_active = False
            await self.session.commit()
            await self.session.refresh(group)
        return group

    async def list_paginated(
        self,
        subject_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[TelegramGroup], int]:
        """Fetch filtered groups with total count for pagination."""
        query = select(TelegramGroup)
        count_query = select(func.count()).select_from(TelegramGroup)

        if subject_id is not None:
            query = query.where(TelegramGroup.subject_id == subject_id)
            count_query = count_query.where(TelegramGroup.subject_id == subject_id)

        if is_active is not None:
            query = query.where(TelegramGroup.is_active == is_active)
            count_query = count_query.where(TelegramGroup.is_active == is_active)

        query = query.order_by(TelegramGroup.group_title).offset(skip).limit(limit)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        items_result = await self.session.execute(query)
        items = items_result.scalars().all()

        return items, total
