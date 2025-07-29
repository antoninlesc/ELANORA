
from app.schema.common.base import CustomBaseModel


class NamingComponentResponse(CustomBaseModel):
    id: int
    name: str
    regex: str
    description: str | None = ""
    order: int
    accepted_values: list[str] | None = None
    file_type_id: int


class NamingStandardResponse(CustomBaseModel):
    id: int
    project_id: int
    name: str
    file_type_id: int
    pattern: str
    description: str | None = ""
    components: list[NamingComponentResponse]
