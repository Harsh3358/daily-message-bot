"""Tests for delivery workflow, multi-group dispatch, and idempotency guarantees."""
import uuid
from datetime import date
from unittest.mock import AsyncMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.exceptions import TelegramForbiddenException
from src.models.enums import DeliveryStatusEnum, DifficultyEnum
from src.models.problem import Problem
from src.models.subject import Subject
from src.models.telegram_group import TelegramGroup
from src.repositories.delivery_log_repository import DeliveryLogRepository
from src.repositories.problem_repository import ProblemRepository
from src.repositories.subject_repository import SubjectRepository
from src.repositories.telegram_group_repository import TelegramGroupRepository
from src.services.delivery_service import DeliveryService


@pytest.mark.asyncio
async def test_delivery_idempotency_same_problem_skipped(db_session: AsyncSession):
    """Verify that dispatching the same problem to the same group on the same date is skipped."""
    subject_repo = SubjectRepository(db_session)
    problem_repo = ProblemRepository(db_session)
    group_repo = TelegramGroupRepository(db_session)
    log_repo = DeliveryLogRepository(db_session)

    # 1. Setup Data
    subject = await subject_repo.create(
        Subject(name="Java", slug="java", is_active=True)
    )
    group = await group_repo.create(
        TelegramGroup(subject_id=subject.id, chat_id=-1001234567890, group_title="Java Study Group", is_active=True)
    )
    run_date = date(2026, 9, 23)
    problem_a = await problem_repo.create(
        Problem(
            subject_id=subject.id,
            title="JVM Memory Model",
            topic="Memory Management",
            difficulty=DifficultyEnum.MEDIUM,
            content="Explain Stack vs Heap.",
            scheduled_date=run_date,
            is_active=True,
        )
    )

    mock_telegram = AsyncMock(spec=TelegramClient)
    mock_telegram.send_message.return_value = 99991

    service = DeliveryService(
        subject_repository=subject_repo,
        problem_repository=problem_repo,
        group_repository=group_repo,
        delivery_log_repository=log_repo,
        telegram_client=mock_telegram,
    )

    # First dispatch -> SUCCESS
    summary1 = await service.execute_daily_delivery(target_date=run_date)
    assert summary1.total_processed == 1
    assert summary1.successful_count == 1
    assert summary1.skipped_count == 0
    assert mock_telegram.send_message.call_count == 1

    # Second dispatch -> SKIPPED (Idempotent!)
    summary2 = await service.execute_daily_delivery(target_date=run_date)
    assert summary2.total_processed == 1
    assert summary2.successful_count == 0
    assert summary2.skipped_count == 1
    # Ensure send_message was NOT called again
    assert mock_telegram.send_message.call_count == 1


@pytest.mark.asyncio
async def test_group_can_receive_different_problems_on_same_day(db_session: AsyncSession):
    """Verify that a group is NOT restricted to only one problem per day if another problem is sent."""
    subject_repo = SubjectRepository(db_session)
    problem_repo = ProblemRepository(db_session)
    group_repo = TelegramGroupRepository(db_session)
    log_repo = DeliveryLogRepository(db_session)

    subject_a = await subject_repo.create(Subject(name="DSA", slug="dsa", is_active=True))
    group = await group_repo.create(
        TelegramGroup(subject_id=subject_a.id, chat_id=-1009876543210, group_title="General Tech", is_active=True)
    )
    run_date = date(2026, 9, 23)

    problem_1 = await problem_repo.create(
        Problem(
            subject_id=subject_a.id,
            title="Binary Search",
            topic="Algorithms",
            difficulty=DifficultyEnum.EASY,
            content="Search in sorted array.",
            scheduled_date=run_date,
            is_active=True,
        )
    )

    mock_telegram = AsyncMock(spec=TelegramClient)
    mock_telegram.send_message.return_value = 10001

    service = DeliveryService(
        subject_repository=subject_repo,
        problem_repository=problem_repo,
        group_repository=group_repo,
        delivery_log_repository=log_repo,
        telegram_client=mock_telegram,
    )

    # Deliver Problem 1
    res1 = await service.execute_daily_delivery(target_date=run_date)
    assert res1.successful_count == 1

    # Create another problem (e.g. for another track or updated problem)
    subject_b = await subject_repo.create(Subject(name="DBMS", slug="dbms", is_active=True))
    # Switch group mapping to subject_b or add another group for subject_b
    group_b = await group_repo.create(
        TelegramGroup(subject_id=subject_b.id, chat_id=-1009876543211, group_title="DBMS Group", is_active=True)
    )
    problem_2 = await problem_repo.create(
        Problem(
            subject_id=subject_b.id,
            title="B+ Trees",
            topic="Storage",
            difficulty=DifficultyEnum.HARD,
            content="Explain node split.",
            scheduled_date=run_date,
            is_active=True,
        )
    )

    res2 = await service.execute_daily_delivery(target_date=run_date)
    # Problem 1 is skipped, Problem 2 is delivered successfully
    assert res2.skipped_count == 1
    assert res2.successful_count == 1


@pytest.mark.asyncio
async def test_bot_kicked_403_deactivates_group(db_session: AsyncSession):
    """Verify that when Telegram API raises 403 Forbidden, the group is auto-deactivated."""
    subject_repo = SubjectRepository(db_session)
    problem_repo = ProblemRepository(db_session)
    group_repo = TelegramGroupRepository(db_session)
    log_repo = DeliveryLogRepository(db_session)

    subject = await subject_repo.create(Subject(name="OS", slug="os", is_active=True))
    group = await group_repo.create(
        TelegramGroup(subject_id=subject.id, chat_id=-1005555555555, group_title="Kicked Group", is_active=True)
    )
    run_date = date(2026, 9, 23)
    await problem_repo.create(
        Problem(
            subject_id=subject.id,
            title="Deadlocks",
            topic="Synchronization",
            difficulty=DifficultyEnum.HARD,
            content="Coffman conditions.",
            scheduled_date=run_date,
            is_active=True,
        )
    )

    mock_telegram = AsyncMock(spec=TelegramClient)
    mock_telegram.send_message.side_effect = TelegramForbiddenException("Forbidden: bot was kicked from group", status_code=403)

    service = DeliveryService(
        subject_repository=subject_repo,
        problem_repository=problem_repo,
        group_repository=group_repo,
        delivery_log_repository=log_repo,
        telegram_client=mock_telegram,
    )

    summary = await service.execute_daily_delivery(target_date=run_date)
    assert summary.failed_count == 1

    # Verify group was deactivated in database
    refreshed_group = await group_repo.get_by_id(group.id)
    assert refreshed_group is not None
    assert refreshed_group.is_active is False
