from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from sqlalchemy import Integer, String, ForeignKey


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
    elan_file_name: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    section = relationship("TierSection", back_populates="tier_groups")
