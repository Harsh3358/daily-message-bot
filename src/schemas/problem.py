"""Problem Pydantic v2 schemas."""
import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import Field, HttpUrl, field_validator
from src.models.enums import DifficultyEnum
from src.schemas.common import BaseSchema


class ProblemBase(BaseSchema):
    """Base fields for Problem."""

    title: str = Field(..., min_length=3, max_length=255, description="Title of the daily problem")
    topic: str = Field(..., min_length=2, max_length=100, description="Topic or category within the subject")
    difficulty: DifficultyEnum = Field(default=DifficultyEnum.MEDIUM, description="Difficulty level")
    content: str = Field(..., min_length=10, description="Full problem description and examples")
    scheduled_date: date = Field(..., description="Calendar date this problem should be dispatched")
    reference_url: Optional[str] = Field(None, max_length=500, description="External reference/solution URL")
    is_active: bool = Field(default=True, description="Whether this problem is active for delivery")

    @field_validator("reference_url")
    @classmethod
    def validate_reference_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v_str = str(v).strip()
            if not (v_str.startswith("http://") or v_str.startswith("https://")):
                raise ValueError("Reference URL must start with http:// or https://")
            return v_str
        return None


class ProblemCreate(ProblemBase):
    """Schema for creating a new Problem."""

    subject_id: uuid.UUID = Field(..., description="UUID of the parent Subject")


class ProblemUpdate(BaseSchema):
    """Schema for updating an existing Problem."""

    subject_id: Optional[uuid.UUID] = None
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    topic: Optional[str] = Field(None, min_length=2, max_length=100)
    difficulty: Optional[DifficultyEnum] = None
    content: Optional[str] = Field(None, min_length=10)
    scheduled_date: Optional[date] = None
    reference_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    @field_validator("reference_url")
    @classmethod
    def validate_reference_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v_str = str(v).strip()
            if not (v_str.startswith("http://") or v_str.startswith("https://")):
                raise ValueError("Reference URL must start with http:// or https://")
            return v_str
        return None


class ProblemResponse(ProblemBase):
    """Schema for returning Problem details."""

    id: uuid.UUID
    subject_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
