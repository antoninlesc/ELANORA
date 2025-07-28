from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class ComponentAcceptedValue(Base):
    __tablename__ = "COMPONENT_ACCEPTED_VALUE"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    naming_component_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("NAMING_COMPONENT.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[str] = mapped_column(String(100), nullable=False)

    naming_component = relationship("NamingComponent", back_populates="accepted_values")
