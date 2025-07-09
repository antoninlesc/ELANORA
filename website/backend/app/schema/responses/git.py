from schema.common.base import CustomBaseModel
from schema.common.git import FileStatus


class GitStatusResponse(CustomBaseModel):
    """Schema for Git availability status."""

    git_available: bool
    version: str | None = None
    status: str
    error: str | None = None


class ProjectCreateResponse(CustomBaseModel):
    """Schema for project creation response."""

    project_name: str
    path: str
    status: str
    git_initialized: bool
    created_at: str


class CommitResponse(CustomBaseModel):
    """Schema for commit response."""

    project_name: str
    message: str
    commit_hash: str
    status: str
    committed_at: str


class FileUploadResponse(CustomBaseModel):
    """Schema for file upload response."""

    filename: str
    project_name: str
    status: str
    added_at: str


class ProjectStatusResponse(CustomBaseModel):
    """Schema for project status response."""

    project_name: str
    files: list[FileStatus]
    recent_commits: list[str]
    conflicts: list[str]
    status: str
