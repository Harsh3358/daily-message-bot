"""Enumerations used by database models and domain logic."""
import enum


class DifficultyEnum(str, enum.Enum):
    """Problem difficulty levels."""

    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class DeliveryStatusEnum(str, enum.Enum):
    """Status of a problem delivery attempt to a Telegram group."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
