from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


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

    naming_standard = relationship(
        "ProjectNamingStandard", back_populates="standard_components"
    )
    component_template = relationship("ComponentTemplate")
