"""Deliveries and dispatch trigger endpoints (Controller)."""
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from src.api.dependencies import get_delivery_log_repository, get_delivery_service
from src.models.enums import DeliveryStatusEnum
from src.repositories.delivery_log_repository import DeliveryLogRepository
from src.schemas.common import PaginatedResponse
from src.schemas.delivery_log import (
    DeliveryLogResponse,
    DeliverySummaryResponse,
    DeliveryTriggerRequest,
)
from src.services.delivery_service import DeliveryService

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


@router.post(
    "/trigger",
    response_model=DeliverySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger daily problem delivery on demand",
)
async def trigger_delivery(
    payload: Optional[DeliveryTriggerRequest] = None,
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliverySummaryResponse:
    """Manually invoke the problem delivery workflow.

    Enforces idempotency:
    Does NOT deliver the same problem to the same group on the same date twice.
    """
    subject_id = payload.subject_id if payload else None
    target_date = payload.scheduled_date if payload else None
    force_retry = payload.force if payload else False

    return await service.execute_daily_delivery(
        target_date=target_date,
        subject_id=subject_id,
        force_retry=force_retry,
    )


@router.get(
    "/logs",
    response_model=PaginatedResponse[DeliveryLogResponse],
    summary="List delivery audit logs with filters",
)
async def list_delivery_logs(
    problem_id: Optional[uuid.UUID] = Query(None, description="Filter by problem ID"),
    telegram_group_id: Optional[uuid.UUID] = Query(None, description="Filter by group ID"),
    delivery_date: Optional[date] = Query(None, description="Filter by delivery date"),
    status: Optional[DeliveryStatusEnum] = Query(None, description="Filter by delivery status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    log_repo: DeliveryLogRepository = Depends(get_delivery_log_repository),
) -> PaginatedResponse[DeliveryLogResponse]:
    """Retrieve audit records of problem delivery attempts."""
    skip = (page - 1) * page_size
    items, total = await log_repo.list_paginated(
        problem_id=problem_id,
        telegram_group_id=telegram_group_id,
        delivery_date=delivery_date,
        status=status,
        skip=skip,
        limit=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse[DeliveryLogResponse](
        items=[DeliveryLogResponse.model_validate(log) for log in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
