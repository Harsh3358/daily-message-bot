"""Subject Pydantic v2 schemas."""
import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator
from src.schemas.common import BaseSchema


class SubjectBase(BaseSchema):
    """Base fields for Subject."""

    name: str = Field(..., min_length=2, max_length=100, description="Name of the subject track")
    slug: str = Field(..., min_length=2, max_length=100, description="URL-friendly identifier")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed description")
    is_active: bool = Field(default=True, description="Whether this subject is actively scheduled")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", cleaned):
            raise ValueError("Slug must be lowercase alphanumeric and hyphens only (e.g., 'dsa', 'java-core').")
        return cleaned


class SubjectCreate(SubjectBase):
    """Schema for creating a new Subject."""
    pass


class SubjectUpdate(BaseSchema):
    """Schema for updating an existing Subject."""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", cleaned):
                raise ValueError("Slug must be lowercase alphanumeric and hyphens only.")
            return cleaned
        return v


class SubjectResponse(SubjectBase):
    """Schema for returning Subject details."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
