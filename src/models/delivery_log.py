"""DeliveryLog SQLAlchemy database model."""
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import DeliveryStatusEnum

if TYPE_CHECKING:
    from src.models.problem import Problem
    from src.models.telegram_group import TelegramGroup


class DeliveryLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit record tracking every problem delivery attempt to a Telegram group."""

    __tablename__ = "delivery_logs"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("telegram_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[DeliveryStatusEnum] = mapped_column(
        SQLEnum(DeliveryStatusEnum, name="delivery_status_enum", native_enum=False),
        nullable=False,
        default=DeliveryStatusEnum.PENDING,
        index=True,
    )
    telegram_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    problem: Mapped["Problem"] = relationship("Problem", back_populates="delivery_logs")
    telegram_group: Mapped["TelegramGroup"] = relationship(
        "TelegramGroup",
        back_populates="delivery_logs",
    )

    __table_args__ = (
        # Partial unique index ensuring that a specific problem cannot be delivered
        # to the same Telegram group more than once successfully on the same date.
        Index(
            "uq_successful_problem_delivery",
            "problem_id",
            "telegram_group_id",
            "delivery_date",
            unique=True,
            postgresql_where=(status == DeliveryStatusEnum.SUCCESS),
        ),
        # General composite index for fast pre-flight query checks
        Index(
            "ix_delivery_lookup",
            "problem_id",
            "telegram_group_id",
            "delivery_date",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DeliveryLog(id={self.id}, problem_id={self.problem_id}, "
            f"group_id={self.telegram_group_id}, date={self.delivery_date}, status={self.status.value})>"
        )
