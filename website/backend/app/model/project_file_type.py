from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .file_type import FileType
    from .project import Project
    from .project_naming_standard import ProjectNamingStandard


class ProjectFileType(Base):
    __tablename__ = "PROJECT_FILE_TYPE"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_filetype_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id"), nullable=False
    )
    file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("FILE_TYPE.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    file_type: Mapped["FileType"] = relationship(
        "FileType", back_populates="project_file_types"
    )
    project: Mapped["Project"] = relationship("Project")
    naming_standards: Mapped[list["ProjectNamingStandard"]] = relationship(
        "ProjectNamingStandard", back_populates="project_file_type"
    )
