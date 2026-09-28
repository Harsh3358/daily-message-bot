"""Subject service containing business logic for subject tracks."""
import uuid
from typing import Optional
from src.core.exceptions import DuplicateEntityException, EntityNotFoundException
from src.models.subject import Subject
from src.repositories.subject_repository import SubjectRepository
from src.schemas.common import PaginatedResponse
from src.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate


class SubjectService:
    """Service handling business rules for Subjects."""

    def __init__(self, repository: SubjectRepository) -> None:
        self.repository = repository

    async def create_subject(self, data: SubjectCreate) -> SubjectResponse:
        """Create a new subject track after ensuring uniqueness of name and slug."""
        # Check duplicate name
        existing_name = await self.repository.get_by_name(data.name)
        if existing_name:
            raise DuplicateEntityException("Subject", "name", data.name)

        # Check duplicate slug
        existing_slug = await self.repository.get_by_slug(data.slug)
        if existing_slug:
            raise DuplicateEntityException("Subject", "slug", data.slug)

        subject = Subject(
            name=data.name,
            slug=data.slug,
            description=data.description,
            is_active=data.is_active,
        )
        created = await self.repository.create(subject)
        return SubjectResponse.model_validate(created)

    async def get_subject_by_id(self, id_: uuid.UUID) -> SubjectResponse:
        """Retrieve subject by ID or raise EntityNotFoundException."""
        subject = await self.repository.get_by_id(id_)
        if not subject:
            raise EntityNotFoundException("Subject", str(id_))
        return SubjectResponse.model_validate(subject)

    async def get_subject_by_slug(self, slug: str) -> SubjectResponse:
        """Retrieve subject by slug or raise EntityNotFoundException."""
        subject = await self.repository.get_by_slug(slug)
        if not subject:
            raise EntityNotFoundException("Subject", slug)
        return SubjectResponse.model_validate(subject)

    async def list_subjects(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[SubjectResponse]:
        """Retrieve paginated subjects."""
        skip = (page - 1) * page_size
        items, total = await self.repository.list_paginated(
            is_active=is_active,
            skip=skip,
            limit=page_size,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse[SubjectResponse](
            items=[SubjectResponse.model_validate(s) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_subject(self, id_: uuid.UUID, data: SubjectUpdate) -> SubjectResponse:
        """Update an existing subject."""
        subject = await self.repository.get_by_id(id_)
        if not subject:
            raise EntityNotFoundException("Subject", str(id_))

        update_dict = data.model_dump(exclude_unset=True)

        # Validate name uniqueness if changed
        if "name" in update_dict and update_dict["name"] != subject.name:
            existing = await self.repository.get_by_name(update_dict["name"])
            if existing:
                raise DuplicateEntityException("Subject", "name", update_dict["name"])

        # Validate slug uniqueness if changed
        if "slug" in update_dict and update_dict["slug"] != subject.slug:
            existing = await self.repository.get_by_slug(update_dict["slug"])
            if existing:
                raise DuplicateEntityException("Subject", "slug", update_dict["slug"])

        updated = await self.repository.update(subject, update_dict)
        return SubjectResponse.model_validate(updated)

    async def delete_subject(self, id_: uuid.UUID) -> None:
        """Delete an existing subject."""
        subject = await self.repository.get_by_id(id_)
        if not subject:
            raise EntityNotFoundException("Subject", str(id_))
        await self.repository.delete(subject)
