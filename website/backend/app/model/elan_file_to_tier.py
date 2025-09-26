from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ElanFileToTier(Base):
    """Association table linking ELAN files to tiers."""

    __tablename__ = "ELAN_FILE_TO_TIER"

    tier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("TIER.tier_id"), primary_key=True
    )
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("FILE_CONTENT.content_id"), primary_key=True
    )
