from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .component_template import ComponentTemplate
    from .project_naming_standard import ProjectNamingStandard


class StandardComponent(Base):
    __tablename__ = "STANDARD_COMPONENT"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    naming_standard_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("PROJECT_NAMING_STANDARD.id", ondelete="CASCADE"),
        nullable=False,
    )
    component_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("COMPONENT_TEMPLATE.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    naming_standard: Mapped["ProjectNamingStandard"] = relationship(
        "ProjectNamingStandard", back_populates="standard_components"
    )
    component_template: Mapped["ComponentTemplate"] = relationship(
        "ComponentTemplate", back_populates="standard_components"
    )
