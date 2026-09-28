"""FastAPI dependency injection providers.

This module wires together Database Sessions, Repositories, External Clients, and Services
following the layered architecture:
Controller -> Service -> Repository -> Database
Controller -> Service -> Telegram Client
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db_session
from src.integrations.telegram.client import TelegramClient
from src.repositories.delivery_log_repository import DeliveryLogRepository
from src.repositories.problem_repository import ProblemRepository
from src.repositories.subject_repository import SubjectRepository
from src.repositories.telegram_group_repository import TelegramGroupRepository
from src.services.delivery_service import DeliveryService
from src.services.problem_service import ProblemService
from src.services.subject_service import SubjectService
from src.services.telegram_group_service import TelegramGroupService


# Repository Dependencies
def get_subject_repository(session: AsyncSession = Depends(get_db_session)) -> SubjectRepository:
    return SubjectRepository(session)


def get_problem_repository(session: AsyncSession = Depends(get_db_session)) -> ProblemRepository:
    return ProblemRepository(session)


def get_telegram_group_repository(session: AsyncSession = Depends(get_db_session)) -> TelegramGroupRepository:
    return TelegramGroupRepository(session)


def get_delivery_log_repository(session: AsyncSession = Depends(get_db_session)) -> DeliveryLogRepository:
    return DeliveryLogRepository(session)


# External Client Dependency
def get_telegram_client() -> TelegramClient:
    return TelegramClient()


# Service Dependencies
def get_subject_service(
    repository: SubjectRepository = Depends(get_subject_repository),
) -> SubjectService:
    return SubjectService(repository)


def get_problem_service(
    problem_repository: ProblemRepository = Depends(get_problem_repository),
    subject_repository: SubjectRepository = Depends(get_subject_repository),
) -> ProblemService:
    return ProblemService(problem_repository, subject_repository)


def get_telegram_group_service(
    group_repository: TelegramGroupRepository = Depends(get_telegram_group_repository),
    subject_repository: SubjectRepository = Depends(get_subject_repository),
) -> TelegramGroupService:
    return TelegramGroupService(group_repository, subject_repository)


def get_delivery_service(
    subject_repository: SubjectRepository = Depends(get_subject_repository),
    problem_repository: ProblemRepository = Depends(get_problem_repository),
    group_repository: TelegramGroupRepository = Depends(get_telegram_group_repository),
    delivery_log_repository: DeliveryLogRepository = Depends(get_delivery_log_repository),
    telegram_client: TelegramClient = Depends(get_telegram_client),
) -> DeliveryService:
    return DeliveryService(
        subject_repository=subject_repository,
        problem_repository=problem_repository,
        group_repository=group_repository,
        delivery_log_repository=delivery_log_repository,
        telegram_client=telegram_client,
    )
