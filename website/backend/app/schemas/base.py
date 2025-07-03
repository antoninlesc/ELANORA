from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    """Base model that forbids extra fields not defined in the schema."""

    class Config:
        """Pydantic configuration to forbid extra fields."""

        extra = "forbid"