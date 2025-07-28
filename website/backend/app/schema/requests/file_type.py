from app.schema.common.base import CustomBaseModel


class FileTypeCreateRequest(CustomBaseModel):
    name: str
    extension: str


class FileTypeUpdateRequest(CustomBaseModel):
    name: str
    extension: str
