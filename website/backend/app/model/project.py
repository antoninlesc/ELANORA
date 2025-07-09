from typing import TYPE_CHECKING

from db.database import Base
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .conflict import Conflict
    from .instance import Instance
    from .invitation import Invitation


class Project(Base):
    """Project model representing annotation projects."""

    __tablename__ = "PROJECT"

    project_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    project_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    instance_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("INSTANCE.instance_id"), nullable=False
    )

    # Relationships - use string references
    instance: Mapped["Instance"] = relationship("Instance", back_populates="projects")
    conflicts: Mapped[list["Conflict"]] = relationship(
        "Conflict", back_populates="project"
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", back_populates="project"
    )

    def __repr__(self) -> str:
        """Return a string representation of the Project."""
        return f"<Project(project_id={self.project_id}, project_name='{self.project_name}')>"
