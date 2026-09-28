"""DeliveryLog Pydantic v2 schemas."""
import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import Field
from src.models.enums import DeliveryStatusEnum
from src.schemas.common import BaseSchema


class DeliveryLogResponse(BaseSchema):
    """Schema for delivery audit log record."""

    id: uuid.UUID
    problem_id: uuid.UUID
    telegram_group_id: uuid.UUID
    delivery_date: date
    status: DeliveryStatusEnum
    telegram_message_id: Optional[int] = None
    error_message: Optional[str] = None
    attempt_count: int
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DeliveryTriggerRequest(BaseSchema):
    """Payload to trigger problem delivery on-demand."""

    subject_id: Optional[uuid.UUID] = Field(None, description="Optional subject ID to run specifically for")
    scheduled_date: Optional[date] = Field(None, description="Date to run for (defaults to today)")
    force: bool = Field(False, description="Whether to retry failed deliveries")


class DeliveryGroupResult(BaseSchema):
    """Result of a delivery attempt for a single group."""

    group_id: uuid.UUID
    chat_id: int
    group_title: str
    status: DeliveryStatusEnum
    message_id: Optional[int] = None
    error: Optional[str] = None


class DeliverySummaryResponse(BaseSchema):
    """Summary of a delivery execution run."""

    delivery_date: date
    total_processed: int
    successful_count: int
    failed_count: int
    skipped_count: int
    details: List[DeliveryGroupResult] = Field(default_factory=list)
