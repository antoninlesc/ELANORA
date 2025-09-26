from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .component_template import ComponentTemplate


class AcceptedValue(Base):
    __tablename__ = "ACCEPTED_VALUE"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Relationships
    component_templates: Mapped[list["ComponentTemplate"]] = relationship(
        "ComponentTemplate",
        secondary="COMPONENT_ACCEPTED_VALUE",
        back_populates="accepted_values",
    )
