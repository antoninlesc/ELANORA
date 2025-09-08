from app.schema.common.base import CustomBaseModel


class FileTypeResponse(CustomBaseModel):
    id: int
    name: str
    extension: str | None = None
    file_type_id: int | None = None
    exists_in_target: bool = False
