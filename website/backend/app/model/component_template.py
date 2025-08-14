from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ComponentTemplate(Base):
    __tablename__ = "COMPONENT_TEMPLATE"
    __table_args__ = (
        UniqueConstraint(
            "file_type_id", "name", "regex", "description", name="uq_component_template"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("FILE_TYPE.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    regex: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    file_type = relationship("FileType")
    accepted_values = relationship(
        "AcceptedValue",
        secondary="COMPONENT_ACCEPTED_VALUE",
        backref="component_templates",
    )
