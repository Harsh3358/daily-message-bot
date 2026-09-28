"""Problem SQLAlchemy database model."""
import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Date, Enum as SQLEnum, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import DifficultyEnum

if TYPE_CHECKING:
    from src.models.subject import Subject
    from src.models.delivery_log import DeliveryLog


class Problem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a daily technical question/problem tied to a specific subject."""

    __tablename__ = "problems"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[DifficultyEnum] = mapped_column(
        SQLEnum(DifficultyEnum, name="difficulty_enum", native_enum=False),
        nullable=False,
        default=DifficultyEnum.MEDIUM,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reference_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="problems")
    delivery_logs: Mapped[List["DeliveryLog"]] = relationship(
        "DeliveryLog",
        back_populates="problem",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("subject_id", "scheduled_date", name="uq_subject_scheduled_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Problem(id={self.id}, subject_id={self.subject_id}, title='{self.title}', "
            f"topic='{self.topic}', difficulty={self.difficulty.value}, date={self.scheduled_date})>"
        )
