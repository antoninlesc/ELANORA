from sqlalchemy import Integer, String, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class ProjectNamingStandard(Base):
    __tablename__ = "PROJECT_NAMING_STANDARD"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "file_type_id", name="uq_project_filetype_standard"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("FILE_TYPE.id"), nullable=False
    )
    pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    file_type = relationship("FileType")
    components = relationship(
        "NamingComponent", back_populates="standard", cascade="all, delete-orphan"
    )
