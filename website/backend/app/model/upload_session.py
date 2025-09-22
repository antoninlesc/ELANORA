from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

if TYPE_CHECKING:
    pass


class UploadSession(Base):
    """UploadSession model for temporary upload sessions during multi-step upload process."""

    __tablename__ = "UPLOAD_SESSION"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="processing")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    def __repr__(self) -> str:
        """Return a string representation of the UploadSession."""
        return f"<UploadSession(session_id='{self.session_id}', project_id='{self.project_id}', status='{self.status}')>"
