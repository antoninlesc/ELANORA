from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .annotation import Annotation
    from .elan_file import ElanFile


class Tier(Base):
    """Tier model representing annotation tiers."""

    __tablename__ = "TIER"

    tier_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_tier_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("TIER.tier_id"), nullable=True
    )
    elan_id: Mapped[int] = mapped_column(
        ForeignKey("ELAN_FILE.elan_id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    parent_tier: Mapped[Optional["Tier"]] = relationship(
        "Tier", remote_side="Tier.tier_id", back_populates="child_tiers"
    )
    child_tiers: Mapped[list["Tier"]] = relationship(
        "Tier", back_populates="parent_tier"
    )
    annotations: Mapped[list["Annotation"]] = relationship(
        "Annotation", back_populates="tier"
    )
    elan_file: Mapped[Optional["ElanFile"]] = relationship(
        "ElanFile", back_populates="tiers"
    )

    def __repr__(self) -> str:
        """Return a string representation of the Tier."""
        return f"<Tier(tier_id='{self.tier_id}', tier_name='{self.tier_name}', elan_id='{self.elan_id}')>"
