"""Subject SQLAlchemy database model."""
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.models.problem import Problem
    from src.models.telegram_group import TelegramGroup


class Subject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a study track/subject (e.g., Java, DSA, DBMS)."""

    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    problems: Mapped[List["Problem"]] = relationship(
        "Problem",
        back_populates="subject",
        cascade="all, delete-orphan",
        order_by="Problem.scheduled_date",
    )
    telegram_groups: Mapped[List["TelegramGroup"]] = relationship(
        "TelegramGroup",
        back_populates="subject",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, name='{self.name}', slug='{self.slug}', is_active={self.is_active})>"
