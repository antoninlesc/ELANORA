from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

from .enums import ConflictSeverity, ConflictStatus, ConflictType

if TYPE_CHECKING:
    from .project import Project
    from .user import User


class Conflict(Base):
    """Conflict model representing detected conflicts in projects."""

    __tablename__ = "CONFLICT"

    conflict_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    conflict_type: Mapped[ConflictType] = mapped_column(
        SQLEnum(ConflictType), nullable=False
    )
    conflict_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[ConflictSeverity] = mapped_column(
        SQLEnum(ConflictSeverity), nullable=False, default=ConflictSeverity.MEDIUM
    )
    status: Mapped[ConflictStatus] = mapped_column(
        SQLEnum(ConflictStatus), nullable=False, default=ConflictStatus.DETECTED
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("USER.user_id"), nullable=True
    )
    branch_name: Mapped[str | None] = mapped_column(
        String(255, ondelete="CASCADE"), nullable=True
    )
    git_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="conflicts")
    resolver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[resolved_by], back_populates="resolved_conflicts"
    )

    def __repr__(self) -> str:
        """Return a string representation of the Conflict."""
        return f"<Conflict(conflict_id='{self.conflict_id}', conflict_type='{self.conflict_type}', status='{self.status}')>"
