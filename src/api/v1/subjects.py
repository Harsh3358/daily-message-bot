"""Subject endpoints (Controller)."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from src.api.dependencies import get_subject_service
from src.schemas.common import PaginatedResponse
from src.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from src.services.subject_service import SubjectService

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subject track",
)
async def create_subject(
    payload: SubjectCreate,
    service: SubjectService = Depends(get_subject_service),
) -> SubjectResponse:
    """Create a new technical subject track (e.g., Java, DSA, DBMS)."""
    return await service.create_subject(payload)


@router.get(
    "",
    response_model=PaginatedResponse[SubjectResponse],
    summary="List all subjects with pagination",
)
async def list_subjects(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: SubjectService = Depends(get_subject_service),
) -> PaginatedResponse[SubjectResponse]:
    """Retrieve subjects with optional filtering."""
    return await service.list_subjects(is_active=is_active, page=page, page_size=page_size)


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Get subject by ID",
)
async def get_subject(
    subject_id: uuid.UUID,
    service: SubjectService = Depends(get_subject_service),
) -> SubjectResponse:
    """Fetch details of a single subject."""
    return await service.get_subject_by_id(subject_id)


@router.patch(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Update subject",
)
async def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    service: SubjectService = Depends(get_subject_service),
) -> SubjectResponse:
    """Partially update a subject."""
    return await service.update_subject(subject_id, payload)


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete subject",
)
async def delete_subject(
    subject_id: uuid.UUID,
    service: SubjectService = Depends(get_subject_service),
) -> None:
    """Delete a subject and cascade delete associated problems."""
    await service.delete_subject(subject_id)
