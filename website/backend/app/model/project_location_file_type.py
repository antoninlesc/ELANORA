from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .project import Project
    from .project_file_type import ProjectFileType


class ProjectLocationFileType(Base):
    __tablename__ = "PROJECT_LOCATION_FILE_TYPE"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "location_id",
            "project_file_type_id",
            name="uq_project_location_filetype",
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    project_file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT_FILE_TYPE.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    project_file_type: Mapped["ProjectFileType"] = relationship("ProjectFileType")
