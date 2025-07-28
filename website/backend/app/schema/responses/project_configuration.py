from typing import List
from app.schema.responses.file_type import FileTypeResponse
from app.schema.responses.project_naming_standard import (
    NamingStandardResponse,
    NamingComponentResponse,
)
from app.schema.common.base import CustomBaseModel


class StandardWithComponents(CustomBaseModel):
    standard: NamingStandardResponse
    components: List[NamingComponentResponse]


class ProjectConfigurationResponse(CustomBaseModel):
    file_types: List[FileTypeResponse]
    standards: List[StandardWithComponents]
    component_names: List[str]
