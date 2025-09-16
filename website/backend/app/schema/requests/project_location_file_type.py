from pydantic import BaseModel


class AddFileTypeToLocationRequest(BaseModel):
    project_id: int
    location_id: int
    project_file_type_id: int


class RemoveFileTypeFromLocationRequest(BaseModel):
    project_id: int
    location_id: int
    project_file_type_id: int
