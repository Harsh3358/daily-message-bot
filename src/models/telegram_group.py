"""TelegramGroup SQLAlchemy database model."""
import uuid
from typing import TYPE_CHECKING, List
from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.models.subject import Subject
    from src.models.delivery_log import DeliveryLog


class TelegramGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a registered Telegram group or supergroup mapped to a subject."""

    __tablename__ = "telegram_groups"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Telegram chat IDs are 64-bit signed integers (e.g., -100xxxxxxxxxx)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    group_title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="telegram_groups")
    delivery_logs: Mapped[List["DeliveryLog"]] = relationship(
        "DeliveryLog",
        back_populates="telegram_group",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<TelegramGroup(id={self.id}, chat_id={self.chat_id}, "
            f"title='{self.group_title}', subject_id={self.subject_id}, is_active={self.is_active})>"
        )
