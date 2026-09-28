"""Problem endpoints (Controller)."""
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from src.api.dependencies import get_problem_service
from src.models.enums import DifficultyEnum
from src.schemas.common import PaginatedResponse
from src.schemas.problem import ProblemCreate, ProblemResponse, ProblemUpdate
from src.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["Problems"])


@router.post(
    "",
    response_model=ProblemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new daily problem",
)
async def create_problem(
    payload: ProblemCreate,
    service: ProblemService = Depends(get_problem_service),
) -> ProblemResponse:
    """Create a new daily problem tied to a subject with topic, difficulty, and scheduled date."""
    return await service.create_problem(payload)


@router.get(
    "",
    response_model=PaginatedResponse[ProblemResponse],
    summary="List problems with filters and pagination",
)
async def list_problems(
    subject_id: Optional[uuid.UUID] = Query(None, description="Filter by subject ID"),
    scheduled_date: Optional[date] = Query(None, description="Filter by scheduled date"),
    difficulty: Optional[DifficultyEnum] = Query(None, description="Filter by difficulty"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ProblemService = Depends(get_problem_service),
) -> PaginatedResponse[ProblemResponse]:
    """Retrieve problems with optional filters."""
    return await service.list_problems(
        subject_id=subject_id,
        scheduled_date=scheduled_date,
        difficulty=difficulty,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{problem_id}",
    response_model=ProblemResponse,
    summary="Get problem by ID",
)
async def get_problem(
    problem_id: uuid.UUID,
    service: ProblemService = Depends(get_problem_service),
) -> ProblemResponse:
    """Fetch details of a single problem."""
    return await service.get_problem_by_id(problem_id)


@router.patch(
    "/{problem_id}",
    response_model=ProblemResponse,
    summary="Update problem",
)
async def update_problem(
    problem_id: uuid.UUID,
    payload: ProblemUpdate,
    service: ProblemService = Depends(get_problem_service),
) -> ProblemResponse:
    """Partially update a problem."""
    return await service.update_problem(problem_id, payload)


@router.delete(
    "/{problem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete problem",
)
async def delete_problem(
    problem_id: uuid.UUID,
    service: ProblemService = Depends(get_problem_service),
) -> None:
    """Delete a problem and associated delivery logs."""
    await service.delete_problem(problem_id)
