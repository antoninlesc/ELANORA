from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TierGroup(Base):
    __tablename__ = "TIER_GROUP"

    tier_group_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("TIER_SECTION.tier_section_id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id"), nullable=False
    )
    tier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("TIER.tier_id", ondelete="CASCADE"), nullable=False
    )
    tier_name: Mapped[str] = mapped_column(String, nullable=False)
    is_staged: Mapped[bool] = mapped_column(Boolean, default=False)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    section = relationship("TierSection", back_populates="tier_groups")
    tier = relationship("Tier")
