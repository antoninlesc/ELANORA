from app.schema.common.base import CustomBaseModel

class NamingComponentRequest(CustomBaseModel):
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

class ImportSelectedStandardsRequest(CustomBaseModel):
    target_project_id: int
    standard_ids: list[int]
