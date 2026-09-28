"""Problem service containing business logic for daily problems."""
import uuid
from datetime import date
from typing import Optional
from src.core.exceptions import DuplicateEntityException, EntityNotFoundException
from src.models.enums import DifficultyEnum
from src.models.problem import Problem
from src.repositories.problem_repository import ProblemRepository
from src.repositories.subject_repository import SubjectRepository
from src.schemas.common import PaginatedResponse
from src.schemas.problem import ProblemCreate, ProblemResponse, ProblemUpdate


class ProblemService:
    """Service handling business rules for Problems."""

    def __init__(
        self,
        problem_repository: ProblemRepository,
        subject_repository: SubjectRepository,
    ) -> None:
        self.problem_repository = problem_repository
        self.subject_repository = subject_repository

    async def create_problem(self, data: ProblemCreate) -> ProblemResponse:
        """Create a new problem after validating subject existence and date uniqueness."""
        # Validate that the subject exists
        subject = await self.subject_repository.get_by_id(data.subject_id)
        if not subject:
            raise EntityNotFoundException("Subject", str(data.subject_id))

        # Validate that no problem already exists for this subject on the scheduled date
        existing_problem = await self.problem_repository.get_by_subject_and_date(
            subject_id=data.subject_id,
            scheduled_date=data.scheduled_date,
        )
        if existing_problem:
            raise DuplicateEntityException(
                "Problem",
                "scheduled_date",
                f"{data.scheduled_date} for Subject '{subject.name}'",
            )

        problem = Problem(
            subject_id=data.subject_id,
            title=data.title,
            topic=data.topic,
            difficulty=data.difficulty,
            content=data.content,
            scheduled_date=data.scheduled_date,
            reference_url=data.reference_url,
            is_active=data.is_active,
        )
        created = await self.problem_repository.create(problem)
        return ProblemResponse.model_validate(created)

    async def get_problem_by_id(self, id_: uuid.UUID) -> ProblemResponse:
        """Retrieve a problem by ID or raise EntityNotFoundException."""
        problem = await self.problem_repository.get_by_id(id_)
        if not problem:
            raise EntityNotFoundException("Problem", str(id_))
        return ProblemResponse.model_validate(problem)

    async def list_problems(
        self,
        subject_id: Optional[uuid.UUID] = None,
        scheduled_date: Optional[date] = None,
        difficulty: Optional[DifficultyEnum] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ProblemResponse]:
        """Retrieve paginated problems with optional filters."""
        skip = (page - 1) * page_size
        items, total = await self.problem_repository.list_paginated(
            subject_id=subject_id,
            scheduled_date=scheduled_date,
            difficulty=difficulty,
            is_active=is_active,
            skip=skip,
            limit=page_size,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse[ProblemResponse](
            items=[ProblemResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_problem(self, id_: uuid.UUID, data: ProblemUpdate) -> ProblemResponse:
        """Update an existing problem."""
        problem = await self.problem_repository.get_by_id(id_)
        if not problem:
            raise EntityNotFoundException("Problem", str(id_))

        update_dict = data.model_dump(exclude_unset=True)

        target_subject_id = update_dict.get("subject_id", problem.subject_id)
        target_date = update_dict.get("scheduled_date", problem.scheduled_date)

        # Validate subject if changed
        if "subject_id" in update_dict and update_dict["subject_id"] != problem.subject_id:
            subject = await self.subject_repository.get_by_id(target_subject_id)
            if not subject:
                raise EntityNotFoundException("Subject", str(target_subject_id))

        # Check unique constraint on (subject_id, scheduled_date) if date or subject changed
        if target_subject_id != problem.subject_id or target_date != problem.scheduled_date:
            conflict = await self.problem_repository.get_by_subject_and_date(
                subject_id=target_subject_id,
                scheduled_date=target_date,
            )
            if conflict and conflict.id != problem.id:
                raise DuplicateEntityException(
                    "Problem",
                    "scheduled_date",
                    f"{target_date} for Subject ID '{target_subject_id}'",
                )

        updated = await self.problem_repository.update(problem, update_dict)
        return ProblemResponse.model_validate(updated)

    async def delete_problem(self, id_: uuid.UUID) -> None:
        """Delete an existing problem."""
        problem = await self.problem_repository.get_by_id(id_)
        if not problem:
            raise EntityNotFoundException("Problem", str(id_))
        await self.problem_repository.delete(problem)
