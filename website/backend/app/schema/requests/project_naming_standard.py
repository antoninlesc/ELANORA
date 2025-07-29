from app.schema.common.base import CustomBaseModel


class NamingComponentRequest(CustomBaseModel):
    id: int | None = None
    name: str
    regex: str
    description: str | None = ""
    order: int
    accepted_values: list[str] | None = None
    project_file_type_id: int


class CreateNamingStandardRequest(CustomBaseModel):
    project_id: int
    name: str
    project_file_type_id: int
    pattern: str
    description: str | None = ""
    components: list[NamingComponentRequest]


class UpdateNamingStandardRequest(CustomBaseModel):
    name: str | None = None
    pattern: str | None = None
    description: str | None = None
    project_file_type_id: int | None = None
    components: list[NamingComponentRequest]
