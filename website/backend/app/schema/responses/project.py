from app.model.user_to_project import ProjectPermission
from app.schema.common.base import CustomBaseModel


class ProjectUserInfo(CustomBaseModel):
    """Information about a user associated with a project."""

    user_id: int
    username: str
    email: str
    permission: ProjectPermission


class ProjectUserListResponse(CustomBaseModel):
    """Response containing list of users for a project."""

    project_name: str
    users: list[ProjectUserInfo]


class ProjectUserAssociationResponse(CustomBaseModel):
    """Response for project-user association operations."""

    project_name: str
    user_id: int
    username: str
    permission: ProjectPermission | None
    message: str


class UserProjectInfo(CustomBaseModel):
    """Information about a project associated with a user."""

    project_id: int
    project_name: str
    description: str | None


class UserProjectListResponse(CustomBaseModel):
    """Response containing list of projects for a user."""

    user_id: int
    username: str
    projects: list[UserProjectInfo]
