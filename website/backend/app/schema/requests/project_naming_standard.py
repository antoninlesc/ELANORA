from typing import List, Optional
from app.schema.common.base import CustomBaseModel


class NamingComponentRequest(CustomBaseModel):
    name: str
    regex: str
    description: Optional[str] = ""
    order: int
    accepted_values: Optional[List[str]] = None
    file_type_id: int


class CreateNamingStandardRequest(CustomBaseModel):
    project_id: int
    name: str
    file_type_id: int
    pattern: str
    description: Optional[str] = ""
    components: List[NamingComponentRequest]
