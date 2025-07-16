from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AnnotationValue(Base):
    __tablename__ = "ANNOTATION_VALUE"

    value_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    annotation_value: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
