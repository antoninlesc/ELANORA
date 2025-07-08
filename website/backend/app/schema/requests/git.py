from typing import Optional
from ..common.base import CustomBaseModel


class ProjectCreateRequest(CustomBaseModel):
    """Schema for project creation request."""

    project_name: str


class CommitRequest(CustomBaseModel):
    """Schema for commit request."""

    commit_message: str
    user_name: str = "user"
