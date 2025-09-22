from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TierSection(Base):
    __tablename__ = "TIER_SECTION"

    tier_section_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id"), nullable=False
    )
    section_name: Mapped[str] = mapped_column(String, nullable=False)
    is_staged: Mapped[bool] = mapped_column(Boolean, default=False)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    tier_groups = relationship(
        "TierGroup", back_populates="section", passive_deletes=True
    )
