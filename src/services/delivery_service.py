"""Delivery service orchestrating problem dispatching and enforcing idempotency.

Workflow:
1. Find active subjects.
2. Find the problem scheduled for the target date for each subject.
3. Find active Telegram groups mapped to the subject.
4. Check Idempotency: Has this problem already been successfully delivered
   to this group on this date?
   - The uniqueness rule: (problem + telegram_group + delivery_date).
   - If a SUCCESS record already exists, skip to prevent duplicates.
   - A Telegram group CAN receive other problems on the same date.
5. Dispatch via TelegramClient.
6. Record delivery result (SUCCESS, FAILED, or SKIPPED) in PostgreSQL.
7. If bot was kicked (HTTP 403), auto-deactivate the group.
"""
import asyncio
import logging
import uuid
from datetime import date
from typing import List, Optional
from src.core.exceptions import EntityNotFoundException
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.exceptions import TelegramForbiddenException
from src.integrations.telegram.formatter import format_problem_message
from src.models.enums import DeliveryStatusEnum
from src.repositories.delivery_log_repository import DeliveryLogRepository
from src.repositories.problem_repository import ProblemRepository
from src.repositories.subject_repository import SubjectRepository
from src.repositories.telegram_group_repository import TelegramGroupRepository
from src.schemas.delivery_log import DeliveryGroupResult, DeliverySummaryResponse

logger = logging.getLogger(__name__)


class DeliveryService:
    """Service handling the end-to-end daily problem delivery process."""

    def __init__(
        self,
        subject_repository: SubjectRepository,
        problem_repository: ProblemRepository,
        group_repository: TelegramGroupRepository,
        delivery_log_repository: DeliveryLogRepository,
        telegram_client: TelegramClient,
    ) -> None:
        self.subject_repo = subject_repository
        self.problem_repo = problem_repository
        self.group_repo = group_repository
        self.log_repo = delivery_log_repository
        self.telegram_client = telegram_client

    async def execute_daily_delivery(
        self,
        target_date: Optional[date] = None,
        subject_id: Optional[uuid.UUID] = None,
        force_retry: bool = False,
    ) -> DeliverySummaryResponse:
        """Execute the daily problem delivery workflow."""
        run_date = target_date or date.today()
        logger.info("Starting daily problem delivery for date: %s", run_date)

        # 1. Fetch active subjects
        if subject_id:
            subject = await self.subject_repo.get_by_id(subject_id)
            if not subject:
                raise EntityNotFoundException("Subject", str(subject_id))
            subjects = [subject] if subject.is_active else []
        else:
            subjects = list(await self.subject_repo.get_active_subjects())

        total_processed = 0
        successful_count = 0
        failed_count = 0
        skipped_count = 0
        results: List[DeliveryGroupResult] = []

        for subject in subjects:
            # 2. Find today's active problem for this subject
            problem = await self.problem_repo.get_active_problem_for_subject(
                subject_id=subject.id,
                scheduled_date=run_date,
            )

            if not problem:
                logger.info("No active problem scheduled for subject '%s' on %s. Skipping.", subject.name, run_date)
                continue

            # 3. Find active groups mapped to this subject
            groups = await self.group_repo.get_active_groups_for_subject(subject.id)
            if not groups:
                logger.info("No active groups found for subject '%s'.", subject.name)
                continue

            formatted_text = format_problem_message(problem, subject)

            # 4. Dispatch to each group
            for group in groups:
                total_processed += 1

                # Idempotency Check: (problem + group + date)
                already_delivered = await self.log_repo.exists_successful_delivery(
                    problem_id=problem.id,
                    telegram_group_id=group.id,
                    delivery_date=run_date,
                )

                if already_delivered and not force_retry:
                    logger.info(
                        "Problem '%s' already delivered to group '%s' on %s. Skipping.",
                        problem.title,
                        group.group_title,
                        run_date,
                    )
                    skipped_count += 1
                    results.append(
                        DeliveryGroupResult(
                            group_id=group.id,
                            chat_id=group.chat_id,
                            group_title=group.group_title,
                            status=DeliveryStatusEnum.SKIPPED,
                        )
                    )
                    continue

                # 5. Send message via Telegram client
                try:
                    message_id = await self.telegram_client.send_message(
                        chat_id=group.chat_id,
                        text=formatted_text,
                    )

                    # 6. Record successful delivery
                    await self.log_repo.record_delivery_attempt(
                        problem_id=problem.id,
                        telegram_group_id=group.id,
                        delivery_date=run_date,
                        status=DeliveryStatusEnum.SUCCESS,
                        telegram_message_id=message_id,
                    )
                    successful_count += 1
                    results.append(
                        DeliveryGroupResult(
                            group_id=group.id,
                            chat_id=group.chat_id,
                            group_title=group.group_title,
                            status=DeliveryStatusEnum.SUCCESS,
                            message_id=message_id,
                        )
                    )
                    logger.info("Successfully delivered problem to group '%s'", group.group_title)

                except TelegramForbiddenException as exc:
                    # Bot was kicked or blocked - auto-deactivate group
                    logger.warning("Bot was kicked from group '%s'. Deactivating group.", group.group_title)
                    await self.group_repo.deactivate_group(group.id)
                    await self.log_repo.record_delivery_attempt(
                        problem_id=problem.id,
                        telegram_group_id=group.id,
                        delivery_date=run_date,
                        status=DeliveryStatusEnum.FAILED,
                        error_message=f"Group deactivated: {exc.message}",
                    )
                    failed_count += 1
                    results.append(
                        DeliveryGroupResult(
                            group_id=group.id,
                            chat_id=group.chat_id,
                            group_title=group.group_title,
                            status=DeliveryStatusEnum.FAILED,
                            error=exc.message,
                        )
                    )

                except Exception as exc:
                    logger.error("Failed to deliver problem to group '%s': %s", group.group_title, exc)
                    await self.log_repo.record_delivery_attempt(
                        problem_id=problem.id,
                        telegram_group_id=group.id,
                        delivery_date=run_date,
                        status=DeliveryStatusEnum.FAILED,
                        error_message=str(exc),
                    )
                    failed_count += 1
                    results.append(
                        DeliveryGroupResult(
                            group_id=group.id,
                            chat_id=group.chat_id,
                            group_title=group.group_title,
                            status=DeliveryStatusEnum.FAILED,
                            error=str(exc),
                        )
                    )

                # Gentle pacing between requests to respect Telegram rate limits
                await asyncio.sleep(0.05)

        summary = DeliverySummaryResponse(
            delivery_date=run_date,
            total_processed=total_processed,
            successful_count=successful_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            details=results,
        )
        logger.info(
            "Delivery run complete: Total=%d, Success=%d, Failed=%d, Skipped=%d",
            total_processed,
            successful_count,
            failed_count,
            skipped_count,
        )
        return summary
