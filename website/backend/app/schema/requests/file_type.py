from app.schema.common.base import CustomBaseModel


class FileTypeCreateRequest(CustomBaseModel):
    name: str
    extension: str
    project_id: int


class FileTypeUpdateRequest(CustomBaseModel):
    name: str | None = None
    extension: str | None = None


class FileTypeImportSelectedRequest(CustomBaseModel):
    file_type_names: list[str]
