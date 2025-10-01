from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .project import Project
    from .tier import Tier
    from .tier_section import TierSection


class TierGroup(Base):
    __tablename__ = "TIER_GROUP"

    tier_group_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    section_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("TIER_SECTION.tier_section_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id"), nullable=False, index=True
    )
    tier_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("TIER.tier_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier_name: Mapped[str] = mapped_column(String, nullable=False)
    is_staged: Mapped[bool] = mapped_column(Boolean, default=False)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    section: Mapped["TierSection"] = relationship(
        "TierSection", back_populates="tier_groups"
    )
    tier: Mapped["Tier"] = relationship("Tier")
    project: Mapped["Project"] = relationship("Project")
