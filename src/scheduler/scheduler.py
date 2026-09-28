"""APScheduler configuration and lifecycle management.

Async Architecture Concepts:
- `AsyncIOScheduler`: Integrates directly into Python's asyncio event loop.
  Unlike standard thread-based background workers, AsyncIOScheduler fires
  async coroutines (`async def`) directly inside the event loop without
  spawning unneeded OS threads or causing race conditions with asyncpg pools.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.core.config import get_settings
from src.scheduler.jobs import daily_problem_dispatch_job

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler(timezone=settings.APP_TIMEZONE)


def setup_scheduler() -> AsyncIOScheduler:
    """Register scheduled cron jobs with APScheduler."""
    cron_trigger = CronTrigger(
        hour=settings.SCHEDULER_CRON_HOUR,
        minute=settings.SCHEDULON_MINUTE if hasattr(settings, "SCHEDULON_MINUTE") else settings.SCHEDULER_CRON_MINUTE,
        timezone=settings.APP_TIMEZONE,
    )

    scheduler.add_job(
        daily_problem_dispatch_job,
        trigger=cron_trigger,
        id="daily_problem_dispatch",
        name="Daily Problem Dispatch",
        replace_existing=True,
    )
    logger.info(
        "Registered daily problem dispatch job for %02d:%02d (%s)",
        settings.SCHEDULER_CRON_HOUR,
        settings.SCHEDULER_CRON_MINUTE,
        settings.APP_TIMEZONE,
    )
    return scheduler


def start_scheduler() -> None:
    """Start the APScheduler instance."""
    setup_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started successfully.")


def shutdown_scheduler() -> None:
    """Gracefully shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")
