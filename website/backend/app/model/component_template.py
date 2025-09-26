from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .accepted_value import AcceptedValue
    from .file_type import FileType
    from .standard_component import StandardComponent


class ComponentTemplate(Base):
    __tablename__ = "COMPONENT_TEMPLATE"
    __table_args__ = (
        UniqueConstraint(
            "file_type_id",
            "name",
            "regex",
            "description",
            name="uq_component_template",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("FILE_TYPE.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    regex: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    file_type: Mapped["FileType"] = relationship(
        "FileType", back_populates="component_templates"
    )
    accepted_values: Mapped[list["AcceptedValue"]] = relationship(
        "AcceptedValue",
        secondary="COMPONENT_ACCEPTED_VALUE",
        back_populates="component_templates",
    )
    standard_components: Mapped[list["StandardComponent"]] = relationship(
        "StandardComponent", back_populates="component_template"
    )
