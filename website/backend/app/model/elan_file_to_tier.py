from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .file_content import FileContent
    from .tier import Tier


class ElanFileToTier(Base):
    """Association table linking ELAN files to tiers."""

    __tablename__ = "ELAN_FILE_TO_TIER"

    tier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("TIER.tier_id"), primary_key=True
    )
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("FILE_CONTENT.content_id"), primary_key=True
    )

    # Relationships
    tier: Mapped["Tier"] = relationship("Tier")
    file_content: Mapped["FileContent"] = relationship("FileContent")
