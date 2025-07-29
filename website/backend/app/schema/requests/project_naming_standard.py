
from app.schema.common.base import CustomBaseModel


class NamingComponentRequest(CustomBaseModel):
    name: str
    regex: str
    description: str | None = ""
    order: int
    accepted_values: list[str] | None = None
    file_type_id: int


class CreateNamingStandardRequest(CustomBaseModel):
    project_id: int
    name: str
    file_type_id: int
    pattern: str
    description: str | None = ""
    components: list[NamingComponentRequest]
