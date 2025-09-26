from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .project import Project
    from .project_file_type import ProjectFileType
    from .project_naming_standard import ProjectNamingStandard


class EffectiveNamingStandard(Base):
    __tablename__ = "EFFECTIVE_NAMING_STANDARD"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "project_file_type_id",
            "location_id",
            name="uq_project_filetype_location",
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id", ondelete="CASCADE"), nullable=False
    )
    project_file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT_FILE_TYPE.id", ondelete="CASCADE"), nullable=False
    )
    naming_standard_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("PROJECT_NAMING_STANDARD.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    project_file_type: Mapped["ProjectFileType"] = relationship("ProjectFileType")
    naming_standard: Mapped["ProjectNamingStandard"] = relationship(
        "ProjectNamingStandard"
    )
