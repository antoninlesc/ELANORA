from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .file_content import FileContent


class LinguisticType(Base):
    """LinguisticType model representing ELAN linguistic type definitions."""

    __tablename__ = "LINGUISTIC_TYPE"

    linguistic_type_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("FILE_CONTENT.content_id", ondelete="CASCADE"),
        primary_key=True,
    )
    time_alignable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    constraints: Mapped[str | None] = mapped_column(String(100), nullable=True)
    controlled_vocabulary_ref: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    graphic_references: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Relationships
    file_content: Mapped["FileContent"] = relationship("FileContent")

    def __repr__(self) -> str:
        """Return a string representation of the LinguisticType."""
        return f"<LinguisticType(linguistic_type_id='{self.linguistic_type_id}', content_id={self.content_id})>"
