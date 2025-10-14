from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .file_content import FileContent


class TimeSlot(Base):
    """TimeSlot model representing ELAN time slot definitions."""

    __tablename__ = "TIME_SLOT"

    time_slot_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("FILE_CONTENT.content_id", ondelete="CASCADE"),
        primary_key=True,
    )
    time_value: Mapped[int] = mapped_column(Integer, nullable=False)  # milliseconds

    # Relationships
    file_content: Mapped["FileContent"] = relationship("FileContent")

    def __repr__(self) -> str:
        """Return a string representation of the TimeSlot."""
        return f"<TimeSlot(time_slot_id='{self.time_slot_id}', content_id={self.content_id}, time_value={self.time_value})>"
