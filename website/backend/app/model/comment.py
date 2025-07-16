from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

from .enums import CommentTargetType

if TYPE_CHECKING:
    from .user import User


class Comment(Base):
    """Comment model representing user comments on various entities."""

    __tablename__ = "COMMENT"

    comment_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[CommentTargetType] = mapped_column(
        SQLEnum(CommentTargetType), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("USER.user_id"), nullable=False
    )
    parent_comment_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("COMMENT.comment_id"), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="comments")
    parent_comment: Mapped[Optional["Comment"]] = relationship(
        "Comment", remote_side="Comment.comment_id", back_populates="replies"
    )
    replies: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="parent_comment"
    )

    def __repr__(self) -> str:
        """Return a string representation of the Comment."""
        return f"<Comment(comment_id='{self.comment_id}', target_type='{self.target_type}')>"
