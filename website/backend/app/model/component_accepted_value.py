from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ComponentAcceptedValue(Base):
    __tablename__ = "COMPONENT_ACCEPTED_VALUE"
    component_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("COMPONENT_TEMPLATE.id", ondelete="CASCADE"), primary_key=True
    )
    accepted_value_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ACCEPTED_VALUE.id", ondelete="CASCADE"), primary_key=True
    )
