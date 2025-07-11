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
    branch_name: str
    file_existed: bool
    merge_status: str
    has_conflicts: bool
    conflicts: list[str] | None = None
    status: str
    added_at: str


class UploadedFileInfo(CustomBaseModel):
    filename: str
    size: int | None = None
    existed: bool


class FailedFileInfo(CustomBaseModel):
    filename: str
    error: str


class DiffChange(CustomBaseModel):
    type: str  # "addition", "deletion", "context"
    line_number: int | None = None
    line_number_old: int | None = None
    line_number_new: int | None = None
    content: str


class DiffHunk(CustomBaseModel):
    old_start: int
    new_start: int
    old_count: int
    new_count: int
    context: str
    changes: list[DiffChange]


class FileChanges(CustomBaseModel):
    filename: str
    added_lines: list[DiffChange]
    removed_lines: list[DiffChange]
    modified_sections: list = []
    total_additions: int
    total_deletions: int
    hunks: list[DiffHunk]
    summary: str
    diff_raw: str
    error: str | None = None


class BatchFileUploadResponse(CustomBaseModel):
    project_name: str
    branch_name: str
    uploaded_files: list[UploadedFileInfo]
    failed_files: list[FailedFileInfo]
    total_uploaded: int
    total_failed: int
    existing_files_updated: int
    new_files_added: int
    merge_status: str
    has_conflicts: bool
    conflicts: list[FileChanges] = []
    new_files_in_merge: list[str] | None = []
    modified_files_in_merge: list[str] | None = []
    status: str
    uploaded_at: str
    message: str | None = None


class ProjectStatusResponse(CustomBaseModel):
    """Schema for project status response."""

    project_name: str
    files: list[FileStatus]
    recent_commits: list[str]
    conflicts: list[str]
    status: str
