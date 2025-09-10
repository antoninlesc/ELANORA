from pydantic import Field

from app.schema.common.base import CustomBaseModel
from app.schema.common.git import FileStatus


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


class UploadSummary(CustomBaseModel):
    """Schema for upload file summary."""

    new_files: list[str] = []
    modified_files: list[str] = []
    deleted_files: list[str] = []


class AdminInfo(CustomBaseModel):
    """Schema for admin workflow information."""

    pending_approval_since: str | None = None
    approval_branch: str | None = None
    original_branch: str | None = None
    next_steps: str | None = None


class BatchFileUploadResponse(CustomBaseModel):
    project_name: str
    branch_name: str | None = None
    uploaded_files: list[UploadedFileInfo]
    failed_files: list[FailedFileInfo]
    total_uploaded: int
    total_failed: int
    existing_files_updated: int
    new_files_added: int

    # Workflow status fields (updated for pending upload workflow)
    status: str  # "pending_admin_approval"
    requires_approval: bool = True
    has_differences: bool = False

    # Legacy fields for backward compatibility
    merge_status: str = "pending_admin_approval"  # Default value
    has_conflicts: bool = False  # No conflicts until admin tests merge
    conflicts: list[FileChanges] = []  # Empty until admin tests merge

    # New workflow fields
    upload_summary: UploadSummary | None = None
    admin_info: AdminInfo | None = None

    # Optional fields
    new_files_in_merge: list[str] | None = []
    modified_files_in_merge: list[str] | None = []
    uploaded_at: str
    message: str | None = None


class ProjectCheckoutResponse(CustomBaseModel):
    """Schema for project branch checkout response."""

    project_name: str
    branch_name: str
    status: str
    message: str | None = None


class ProjectInfo(CustomBaseModel):
    project_id: int
    project_name: str
    project_description: str | None = None


class ProjectListResponse(CustomBaseModel):
    projects: list[ProjectInfo]


class ProjectEditResponse(CustomBaseModel):
    """Schema for project edit response."""

    new_project_name: str
    new_project_description: str | None = None


class ProjectDeleteResponse(CustomBaseModel):
    """Schema for project delete response."""

    project_id: int
    status: str
    message: str | None = None


class ProjectSyncCheckResponse(CustomBaseModel):
    """Schema for project synchronization check response."""

    project_name: str
    in_sync: bool
    files_status: list[FileStatus] = Field(default_factory=list)
    status: str | None = None


class PendingUploadInfo(CustomBaseModel):
    """Schema for individual pending upload information."""

    upload_id: int
    branch_name: str
    original_branch: str | None = None
    upload_type: str
    description: str
    status: str
    uploaded_at: str | None = None
    uploaded_by: str | None = None

    # Real-time merge status (computed when requested)
    merge_status: str | None = None  # "ready_to_merge", "needs_resolution", "error"
    conflicted_files: list[str] = []
    conflicted_files_count: int = 0
    tested_at: str | None = None

    # Raw git details
    git_details: dict | None = None


class UploadSummaryStats(CustomBaseModel):
    """Schema for upload summary statistics."""

    total_pending: int
    ready_count: int = 0
    conflicts_count: int = 0


class PendingUploadsResponse(CustomBaseModel):
    """Schema for pending uploads list response."""

    project_name: str
    pending_uploads: list[PendingUploadInfo]
    total_pending: int
    ready_count: int = 0
    conflicts_count: int = 0


class FileInfo(CustomBaseModel):
    name: str
    size: int
    lastModified: str
    lastUpdatedBy: str
    type: str = "file"


class FileInfoWithMedia(CustomBaseModel):
    """Extended file info that includes database ID and associated media filenames."""
    name: str
    size: int
    lastModified: str
    lastUpdatedBy: str
    type: str = "file"
    elan_id: int | None = None  # Database ID for rename operations
    media_filenames: list[str] = []  # Associated media filenames


class ProjectFilesResponse(CustomBaseModel):
    files: list[FileInfo]


class ProjectFilesWithMediaResponse(CustomBaseModel):
    """Response for project files that includes media information."""

    files: list[FileInfoWithMedia]


class RenameResult(CustomBaseModel):
    """Schema for individual file rename result."""

    old_filename: str
    new_filename: str
    success: bool
    error: str | None = None


class FileRenameResponse(CustomBaseModel):
    """Schema for single file rename response."""

    project_name: str
    old_filename: str
    new_filename: str
    success: bool
    committed: bool
    commit_hash: str | None = None
    renamed_at: str
    message: str | None = None


class BulkRenameResponse(CustomBaseModel):
    """Schema for bulk file rename response."""

    project_name: str
    total_files: int
    successful_renames: int
    failed_renames: int
    results: list[RenameResult]
    committed: bool
    commit_hash: str | None = None
    renamed_at: str
    message: str | None = None
