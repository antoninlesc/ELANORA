from app.schema.common.base import CustomBaseModel


class ProjectCreateRequest(CustomBaseModel):
    """Schema for project creation request."""

    project_name: str
    description: str


class CommitRequest(CustomBaseModel):
    """Schema for commit request."""

    commit_message: str
    user_name: str = "user"
