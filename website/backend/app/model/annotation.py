from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

if TYPE_CHECKING:
    from .tier import Tier


class Annotation(Base):
    """Annotation model representing individual annotations."""

    __tablename__ = "ANNOTATION"

    annotation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    annotation_value: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    end_time: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    tier_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("TIER.tier_id"), nullable=False
    )

    # Relationships
    tier: Mapped["Tier"] = relationship("Tier", back_populates="annotations")

    def __repr__(self) -> str:
        """Return a string representation of the Annotation."""
        return f"<Annotation(annotation_id='{self.annotation_id}', start_time={self.start_time}, end_time={self.end_time})>"
