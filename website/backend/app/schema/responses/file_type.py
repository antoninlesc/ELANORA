from app.schema.common.base import CustomBaseModel


class FileTypeResponse(CustomBaseModel):
    id: int
    name: str
    extension: str
    file_type_id: int
    exists_in_target: bool = False
