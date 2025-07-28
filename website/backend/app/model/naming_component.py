from sqlalchemy import Integer, String, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.model.component_accepted_value import ComponentAcceptedValue


class NamingComponent(Base):
    __tablename__ = "NAMING_COMPONENT"
    __table_args__ = (
        UniqueConstraint(
            "naming_standard_id", "name", name="uq_standard_component_name"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    naming_standard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT_NAMING_STANDARD.id"), nullable=False
    )
    file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("FILE_TYPE.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    regex: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column("order", Integer, nullable=False)

    standard = relationship("ProjectNamingStandard", back_populates="components")
    file_type = relationship("FileType")
    accepted_values = relationship(
        "ComponentAcceptedValue",
        back_populates="naming_component",
        cascade="all, delete-orphan",
    )
