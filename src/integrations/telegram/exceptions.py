"""Telegram API custom exceptions."""
from typing import Optional


class TelegramAPIException(Exception):
    """Base exception for Telegram API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[int] = None,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.description = description


class TelegramForbiddenException(TelegramAPIException):
    """Raised when bot is blocked, kicked, or lacks permission (HTTP 403)."""
    pass


class TelegramRateLimitException(TelegramAPIException):
    """Raised when Telegram rate limit is exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str,
        retry_after: int = 5,
        status_code: int = 429,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, description=description)
        self.retry_after = retry_after


class TelegramBadRequestException(TelegramAPIException):
    """Raised when the request format or payload is invalid (HTTP 400)."""
    pass
