from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .annotation_value import AnnotationValue
    from .file_content import FileContent
    from .tier import Tier


class Annotation(Base):
    """Annotation model representing individual annotations."""

    __tablename__ = "ANNOTATION"

    annotation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("FILE_CONTENT.content_id", ondelete="CASCADE"),
        primary_key=True,
    )

    value_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ANNOTATION_VALUE.value_id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    end_time: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    tier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("TIER.tier_id"), nullable=False
    )

    # Relationships
    tier: Mapped["Tier"] = relationship("Tier", back_populates="annotations")
    annotation_value: Mapped["AnnotationValue"] = relationship("AnnotationValue")
    file_content: Mapped["FileContent"] = relationship("FileContent")

    def __repr__(self) -> str:
        """Return a string representation of the Annotation."""
        return f"<Annotation(annotation_id='{self.annotation_id}', content_id={self.content_id}, value_id={self.value_id}, start_time={self.start_time}, end_time={self.end_time}, tier_id={self.tier_id})>"
