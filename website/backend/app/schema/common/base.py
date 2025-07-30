from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    """Base model that forbids extra fields not defined in the schema and supports ORM serialization."""

    class Config:
        """Pydantic configuration to forbid extra fields and enable ORM serialization."""

        extra = "forbid"
        from_attributes = True
