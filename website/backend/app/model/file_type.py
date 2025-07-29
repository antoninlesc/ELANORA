from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class FileType(Base):
    __tablename__ = "FILE_TYPE"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    extension: Mapped[str] = mapped_column(String(10), nullable=False)
