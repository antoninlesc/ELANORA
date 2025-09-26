from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .project import Project
    from .user import User

PROJECT_PROJECTID_FK = "PROJECT.project_id"


class ProjectPermission(str, PyEnum):
    """Enumeration for project permissions."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return None


class UserToProject(Base):
    """Association table linking users to projects with permissions."""

    __tablename__ = "USER_TO_PROJECT"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("USER.user_id"), primary_key=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(PROJECT_PROJECTID_FK), primary_key=True
    )
    permission: Mapped[ProjectPermission] = mapped_column(
        Enum(ProjectPermission), nullable=False, default=ProjectPermission.READ
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    project: Mapped["Project"] = relationship("Project", back_populates="users")
