from app.schema.common.base import CustomBaseModel


class FileTypeResponse(CustomBaseModel):
    id: int
    name: str
    extension: str
