
"""TelegramGroup endpoints (Controller)."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from src.api.dependencies import get_telegram_group_service
from src.schemas.common import PaginatedResponse
from src.schemas.telegram_group import (
    TelegramGroupCreate,
    TelegramGroupResponse,
    TelegramGroupUpdate,
)
from src.services.telegram_group_service import TelegramGroupService

router = APIRouter(prefix="/telegram-groups", tags=["Telegram Groups"])


@router.post(
    "",
    response_model=TelegramGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a Telegram group",
)
async def register_group(
    payload: TelegramGroupCreate,
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> TelegramGroupResponse:
    """Register a Telegram group or supergroup and map it to a subject track."""
    return await service.register_group(payload)


@router.get(
    "",
    response_model=PaginatedResponse[TelegramGroupResponse],
    summary="List registered groups with filters",
)
async def list_groups(
    subject_id: Optional[uuid.UUID] = Query(None, description="Filter by subject ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> PaginatedResponse[TelegramGroupResponse]:
    """Retrieve registered Telegram groups with optional filters."""
    return await service.list_groups(
        subject_id=subject_id,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{group_id}",
    response_model=TelegramGroupResponse,
    summary="Get group by ID",
)
async def get_group(
    group_id: uuid.UUID,
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> TelegramGroupResponse:
    """Fetch details of a single registered Telegram group."""
    return await service.get_group_by_id(group_id)


@router.patch(
    "/{group_id}",
    response_model=TelegramGroupResponse,
    summary="Update group",
)
async def update_group(
    group_id: uuid.UUID,
    payload: TelegramGroupUpdate,
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> TelegramGroupResponse:
    """Update group details (title, subject mapping, or active status)."""
    return await service.update_group(group_id, payload)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete group",
)
async def delete_group(
    group_id: uuid.UUID,
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> None:
    """Remove a registered Telegram group."""
    await service.delete_group(group_id)
