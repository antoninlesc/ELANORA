from app.schema.common.base import CustomBaseModel


class FileStatus(CustomBaseModel):
    """Schema for file status information."""

    filename: str
    status: str
    description: str
    old_filename: str | None = None
    new_filename: str | None = None
