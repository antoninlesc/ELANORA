from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .elan_file import ElanFile
    from .elan_file_media import ElanFileMedia

ELAN_FILE_ELANID_FK = "ELAN_FILE.elan_id"


class ElanFileToMedia(Base):
    """Association table linking ELAN files to media."""

    __tablename__ = "ELAN_FILE_TO_MEDIA"

    elan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ELAN_FILE.elan_id", ondelete="CASCADE"), primary_key=True
    )
    media_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ELAN_FILE_MEDIA.media_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    elan_file: Mapped["ElanFile"] = relationship(
        "ElanFile", back_populates="media_links"
    )
    media: Mapped["ElanFileMedia"] = relationship(
        "ElanFileMedia", back_populates="elan_files"
    )
