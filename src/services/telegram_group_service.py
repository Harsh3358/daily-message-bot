"""TelegramGroup service containing business logic for registered groups."""
import uuid
from typing import Optional
from src.core.exceptions import DuplicateEntityException, EntityNotFoundException
from src.models.telegram_group import TelegramGroup
from src.repositories.subject_repository import SubjectRepository
from src.repositories.telegram_group_repository import TelegramGroupRepository
from src.schemas.common import PaginatedResponse
from src.schemas.telegram_group import (
    TelegramGroupCreate,
    TelegramGroupResponse,
    TelegramGroupUpdate,
)


class TelegramGroupService:
    """Service handling business rules for Telegram groups."""

    def __init__(
        self,
        group_repository: TelegramGroupRepository,
        subject_repository: SubjectRepository,
    ) -> None:
        self.group_repository = group_repository
        self.subject_repository = subject_repository

    async def register_group(self, data: TelegramGroupCreate) -> TelegramGroupResponse:
        """Register a new Telegram group mapped to a subject track."""
        # Ensure subject exists
        subject = await self.subject_repository.get_by_id(data.subject_id)
        if not subject:
            raise EntityNotFoundException("Subject", str(data.subject_id))

        # Check unique chat_id
        existing = await self.group_repository.get_by_chat_id(data.chat_id)
        if existing:
            raise DuplicateEntityException("TelegramGroup", "chat_id", data.chat_id)

        group = TelegramGroup(
            subject_id=data.subject_id,
            chat_id=data.chat_id,
            group_title=data.group_title,
            is_active=data.is_active,
        )
        created = await self.group_repository.create(group)
        return TelegramGroupResponse.model_validate(created)

    async def get_group_by_id(self, id_: uuid.UUID) -> TelegramGroupResponse:
        """Retrieve group by ID or raise EntityNotFoundException."""
        group = await self.group_repository.get_by_id(id_)
        if not group:
            raise EntityNotFoundException("TelegramGroup", str(id_))
        return TelegramGroupResponse.model_validate(group)

    async def list_groups(
        self,
        subject_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[TelegramGroupResponse]:
        """Retrieve paginated groups with optional filters."""
        skip = (page - 1) * page_size
        items, total = await self.group_repository.list_paginated(
            subject_id=subject_id,
            is_active=is_active,
            skip=skip,
            limit=page_size,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse[TelegramGroupResponse](
            items=[TelegramGroupResponse.model_validate(g) for g in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_group(self, id_: uuid.UUID, data: TelegramGroupUpdate) -> TelegramGroupResponse:
        """Update an existing Telegram group."""
        group = await self.group_repository.get_by_id(id_)
        if not group:
            raise EntityNotFoundException("TelegramGroup", str(id_))

        update_dict = data.model_dump(exclude_unset=True)

        # Validate subject if changed
        if "subject_id" in update_dict and update_dict["subject_id"] != group.subject_id:
            subject = await self.subject_repository.get_by_id(update_dict["subject_id"])
            if not subject:
                raise EntityNotFoundException("Subject", str(update_dict["subject_id"]))

        updated = await self.group_repository.update(group, update_dict)
        return TelegramGroupResponse.model_validate(updated)

    async def delete_group(self, id_: uuid.UUID) -> None:
        """Delete an existing Telegram group."""
        group = await self.group_repository.get_by_id(id_)
        if not group:
            raise EntityNotFoundException("TelegramGroup", str(id_))
        await self.group_repository.delete(group)
