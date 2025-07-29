"""Request schemas for project-user association management."""

from pydantic import BaseModel

from app.model.enums import ProjectPermission


class AddUserToProjectRequest(BaseModel):
    """Request to add a user to a project."""

    user_id: int
    permission: ProjectPermission = ProjectPermission.READ


class RemoveUserFromProjectRequest(BaseModel):
    """Request to remove a user from a project."""

    user_id: int
