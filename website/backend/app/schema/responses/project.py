"""Project response schemas."""

from pydantic import BaseModel


class ProjectResponse(BaseModel):
    """Schema for project data."""

    project_id: int
    project_name: str
    description: str
    instance_id: int
    project_path: str

    class Config:
        from_attributes = True
