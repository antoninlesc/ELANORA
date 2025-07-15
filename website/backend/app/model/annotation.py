from decimal import Decimal
from typing import TYPE_CHECKING

from app.db.database import Base
from sqlalchemy import ForeignKey, Numeric, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .tier import Tier
    from .annotation_value import AnnotationValue
    from .elan_file import ElanFile


class Annotation(Base):
    """Annotation model representing individual annotations."""

    __tablename__ = "ANNOTATION"

    annotation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    elan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ELAN_FILE.elan_id"), primary_key=True
    )

    value_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ANNOTATION_VALUE.value_id"), nullable=False
    )
    start_time: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    end_time: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    tier_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("TIER.tier_id"), nullable=False
    )

    # Relationships
    tier: Mapped["Tier"] = relationship("Tier", back_populates="annotations")
    annotation_value: Mapped["AnnotationValue"] = relationship("AnnotationValue")
    elan_file: Mapped["ElanFile"] = relationship("ElanFile")

    def __repr__(self) -> str:
        """Return a string representation of the Annotation."""
        return f"<Annotation(annotation_id='{self.annotation_id}', value_id={self.value_id}, start_time={self.start_time}, end_time={self.end_time})>"
