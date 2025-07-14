from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .project import Project


class Instance(Base):
    """Instance model representing institutional instances."""

    __tablename__ = "INSTANCE"

    instance_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    instance_name: Mapped[str] = mapped_column(String(100), nullable=False)
    institution_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    default_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en"
    )
    max_file_size_mb: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=100.00
    )
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="instance"
    )

    def __repr__(self) -> str:
        """Return a string representation of the Instance."""
        return f"<Instance(instance_id={self.instance_id}, instance_name='{self.instance_name}')>"
