from app.schemas.common.base import CustomBaseModel


class FileStatus(CustomBaseModel):
    """Schema for file status information."""

    filename: str
    status: str
    description: str
