from app.db.database import Base
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column


class AnnotationStandard(Base):
    """AnnotationStandard model representing annotation standards."""

    __tablename__ = "ANNOTATION_STANDARD"

    standard_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    standard_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    regex: Mapped[str] = mapped_column(String(500), nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the AnnotationStandard."""
        return f"<AnnotationStandard(standard_id='{self.standard_id}', standard_name='{self.standard_name}')>"
