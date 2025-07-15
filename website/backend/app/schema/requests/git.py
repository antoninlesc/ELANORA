from app.schema.common.base import CustomBaseModel


class ProjectCreateRequest(CustomBaseModel):
    """Schema for project creation request."""

    project_name: str
    description: str


class CommitRequest(CustomBaseModel):
    """Schema for commit request."""

    commit_message: str
    user_name: str = "user"


class ProjectCheckoutRequest(CustomBaseModel):
    """Schema for project branch checkout request."""

    branch_name: str


class ProjectRenameRequest(CustomBaseModel):
    """Schema for project rename request."""

    new_project_name: str


class ProjectDeleteRequest(CustomBaseModel):
    """Schema for project delete request."""

    project_id: int
    confirm: bool = False
