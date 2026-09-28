"""Scheduler jobs executing business workflows.

Async Architecture Concepts:
- Background jobs run independently of HTTP request scopes. Therefore, the job
  creates its own scoped `AsyncSession` using `async_session_factory()`.
- The job directly calls `DeliveryService.execute_daily_delivery()`, upholding
  the architectural rule:
  Scheduler -> Service -> Repository / Telegram Client.
"""
import logging
from datetime import date
from src.core.database import async_session_factory
from src.integrations.telegram.client import TelegramClient
from src.repositories.delivery_log_repository import DeliveryLogRepository
from src.repositories.problem_repository import ProblemRepository
from src.repositories.subject_repository import SubjectRepository
from src.repositories.telegram_group_repository import TelegramGroupRepository
from src.services.delivery_service import DeliveryService

logger = logging.getLogger(__name__)


async def daily_problem_dispatch_job() -> None:
    """Automated morning job executing daily problem delivery across all active subjects."""
    logger.info("Executing scheduled morning daily problem dispatch job.")
    telegram_client = TelegramClient()

    try:
        async with async_session_factory() as session:
            subject_repo = SubjectRepository(session)
            problem_repo = ProblemRepository(session)
            group_repo = TelegramGroupRepository(session)
            log_repo = DeliveryLogRepository(session)

            service = DeliveryService(
                subject_repository=subject_repo,
                problem_repository=problem_repo,
                group_repository=group_repo,
                delivery_log_repository=log_repo,
                telegram_client=telegram_client,
            )

            summary = await service.execute_daily_delivery(target_date=date.today())
            logger.info(
                "Scheduled daily dispatch finished. Processed: %d, Success: %d, Failed: %d, Skipped: %d",
                summary.total_processed,
                summary.successful_count,
                summary.failed_count,
                summary.skipped_count,
            )
    except Exception as exc:
        logger.error("Unhandled exception in scheduled daily problem dispatch job: %s", exc, exc_info=True)
    finally:
        await telegram_client.close()
