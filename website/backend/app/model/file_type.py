from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .component_template import ComponentTemplate
    from .project_file_type import ProjectFileType


class FileType(Base):
    __tablename__ = "FILE_TYPE"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extension: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    # Relationships
    project_file_types: Mapped[list["ProjectFileType"]] = relationship(
        "ProjectFileType", back_populates="file_type"
    )
    component_templates: Mapped[list["ComponentTemplate"]] = relationship(
        "ComponentTemplate", back_populates="file_type"
    )
