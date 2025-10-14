from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .file_content import FileContent


class FileProperty(Base):
    """FileProperty model representing ELAN file header properties (URN, lastUsedAnnotationId, etc.)."""

    __tablename__ = "FILE_PROPERTY"

    property_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("FILE_CONTENT.content_id", ondelete="CASCADE"),
        nullable=False,
    )
    property_name: Mapped[str] = mapped_column(String(100), nullable=False)
    property_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    file_content: Mapped["FileContent"] = relationship("FileContent")

    def __repr__(self) -> str:
        """Return a string representation of the FileProperty."""
        return f"<FileProperty(property_id={self.property_id}, content_id={self.content_id}, name='{self.property_name}')>"
