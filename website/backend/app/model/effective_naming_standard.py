from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class EffectiveNamingStandard(Base):
    __tablename__ = "EFFECTIVE_NAMING_STANDARD"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("PROJECT.project_id", ondelete="CASCADE"), nullable=False)
    project_file_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("PROJECT_FILE_TYPE.id", ondelete="CASCADE"), nullable=False)
    naming_standard_id: Mapped[int] = mapped_column(Integer, ForeignKey("PROJECT_NAMING_STANDARD.id", ondelete="CASCADE"), nullable=False)
