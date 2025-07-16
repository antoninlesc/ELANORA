from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .user import User
    from .tier import Tier


class ElanFile(Base):
    """ElanFile model representing ELAN annotation files."""

    __tablename__ = "ELAN_FILE"

    elan_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("USER.user_id"), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="elan_files")
    tiers: Mapped[list["Tier"]] = relationship("Tier", back_populates="elan_file")

    def __repr__(self) -> str:
        """Return a string representation of the ElanFile."""
        return f"<ElanFile(elan_id={self.elan_id}, filename='{self.filename}')>"
