from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .accepted_value import AcceptedValue
    from .component_template import ComponentTemplate


class ComponentAcceptedValue(Base):
    __tablename__ = "COMPONENT_ACCEPTED_VALUE"
    component_template_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("COMPONENT_TEMPLATE.id", ondelete="CASCADE"),
        primary_key=True,
    )
    accepted_value_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ACCEPTED_VALUE.id", ondelete="CASCADE"), primary_key=True
    )

    # Relationships
    component_template: Mapped["ComponentTemplate"] = relationship("ComponentTemplate")
    accepted_value: Mapped["AcceptedValue"] = relationship("AcceptedValue")
