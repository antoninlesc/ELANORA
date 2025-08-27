from app.schema.common.base import CustomBaseModel


class ProjectCreateRequest(CustomBaseModel):
    """Schema for project creation request."""

    project_name: str
    description: str | None = None


class CommitRequest(CustomBaseModel):
    """Schema for commit request."""

    commit_message: str
    user_name: str = "user"


class ProjectCheckoutRequest(CustomBaseModel):
    """Schema for project branch checkout request."""

    branch_name: str


class ProjectEditRequest(CustomBaseModel):
    """Schema for project edit request."""

    new_project_name: str
    new_project_description: str | None = None


class ProjectDeleteRequest(CustomBaseModel):
    """Schema for project delete request."""

    project_id: int
    confirm: bool = False
