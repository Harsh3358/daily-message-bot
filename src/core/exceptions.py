"""Custom domain exceptions for the application."""
from typing import Any, Optional


class AppException(Exception):
    """Base exception class for all application-specific errors."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class EntityNotFoundException(AppException):
    """Raised when a requested database entity is not found."""

    def __init__(self, entity_name: str, identifier: Any) -> None:
        message = f"{entity_name} with identifier '{identifier}' was not found."
        super().__init__(message=message, details={"entity": entity_name, "identifier": identifier})


class DuplicateEntityException(AppException):
    """Raised when attempting to create an entity that violates uniqueness."""

    def __init__(self, entity_name: str, field: str, value: Any) -> None:
        message = f"{entity_name} with {field}='{value}' already exists."
        super().__init__(message=message, details={"entity": entity_name, "field": field, "value": value})


class TelegramAPIException(AppException):
    """Raised when communication with Telegram Bot API fails."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None) -> None:
        super().__init__(message=message, details={"status_code": status_code, "response_body": response_body})
        self.status_code = status_code
        self.response_body = response_body
