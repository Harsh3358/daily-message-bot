"""Common reusable Pydantic schemas."""
from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with standard Pydantic v2 configuration."""

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class StatusMessageResponse(BaseModel):
    """Standard message response."""

    message: str
    success: bool = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated wrapper response."""

    items: List[T]
    total: int = Field(..., ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    total_pages: int = Field(..., ge=0)
