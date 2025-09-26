from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .elan_file_to_media import ElanFileToMedia


class ElanFileMedia(Base):
    __tablename__ = "ELAN_FILE_MEDIA"

    media_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    media_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=True)
    relative_media_url: Mapped[str] = mapped_column(String(1024), nullable=True)

    # Relationships
    elan_files: Mapped[list["ElanFileToMedia"]] = relationship(
        "ElanFileToMedia", back_populates="media", cascade="all, delete-orphan"
    )
