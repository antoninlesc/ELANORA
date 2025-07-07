from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .comment import Comment
    from .conflict import Conflict
    from .elan_file import ElanFile
    from .invitation import Invitation


class User(Base):
    """User model representing registered users in the system."""

    __tablename__ = "USER"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    elan_files: Mapped[list["ElanFile"]] = relationship(
        "ElanFile", back_populates="user"
    )
    sent_invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", foreign_keys="Invitation.sender", back_populates="sender_user"
    )
    received_invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", foreign_keys="Invitation.receiver", back_populates="receiver_user"
    )
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")
    resolved_conflicts: Mapped[list["Conflict"]] = relationship(
        "Conflict", foreign_keys="Conflict.resolved_by", back_populates="resolver"
    )

    def __repr__(self) -> str:
        """Return a string representation of the User."""
        return f"<User(user_id={self.user_id}, username='{self.username}')>"
