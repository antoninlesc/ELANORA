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


class ProjectInitFromFolderRequest(CustomBaseModel):
    """Schema for initializing a project from an existing folder."""

    project_name: str
    description: str
    folder_path: str
