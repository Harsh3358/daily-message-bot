from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    PROJECT_NAME: str = "DailyProblemBot"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/daily_problem_bot"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = "mock_token"

    # Scheduler Settings
    SCHEDULER_CRON_HOUR: int = 8
    SCHEDULER_CRON_MINUTE: int = 0
    APP_TIMEZONE: str = "Asia/Kolkata"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Ensure the DATABASE_URL always uses the asyncpg driver.

        Railway and other platforms provide URLs in the plain postgresql://
        format. This validator automatically rewrites it to the asyncpg
        dialect so SQLAlchemy async engine works correctly.
        """
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()
