from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .project import Project
    from .project_file_type import ProjectFileType
    from .standard_component import StandardComponent


class ProjectNamingStandard(Base):
    __tablename__ = "PROJECT_NAMING_STANDARD"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "project_file_type_id",
            "name",
            name="uq_project_filetype_standard",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    project_file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT_FILE_TYPE.id"), nullable=False
    )
    pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    project_file_type: Mapped["ProjectFileType"] = relationship(
        "ProjectFileType", back_populates="naming_standards"
    )
    standard_components: Mapped[list["StandardComponent"]] = relationship(
        "StandardComponent",
        back_populates="naming_standard",
        cascade="all, delete-orphan",
    )
