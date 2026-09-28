"""TelegramGroup Pydantic v2 schemas."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import Field
from src.schemas.common import BaseSchema


class TelegramGroupBase(BaseSchema):
    """Base fields for TelegramGroup."""

    chat_id: int = Field(..., description="Telegram 64-bit chat ID (usually negative for groups)")
    group_title: str = Field(..., min_length=1, max_length=255, description="Display title of the Telegram group")
    is_active: bool = Field(default=True, description="Whether the bot should dispatch messages to this group")


class TelegramGroupCreate(TelegramGroupBase):
    """Schema for registering a new TelegramGroup."""

    subject_id: uuid.UUID = Field(..., description="Subject UUID to subscribe this group to")


class TelegramGroupUpdate(BaseSchema):
    """Schema for updating an existing TelegramGroup."""

    subject_id: Optional[uuid.UUID] = None
    group_title: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class TelegramGroupResponse(TelegramGroupBase):
    """Schema for returning TelegramGroup details."""

    id: uuid.UUID
    subject_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
