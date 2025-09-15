from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db_dep
from app.dependency.elan_validation import validate_multiple_elan_files
from app.dependency.user import get_admin_dep, get_user_dep
from app.model.user import User
from app.schema.requests.git import (
    BulkRenameRequest,
    CommitRequest,
    ProjectCheckoutRequest,
    ProjectCreateRequest,
    ProjectEditRequest,
    DownloadFilesRequest,
)
from app.schema.responses.git import (
    BatchFileUploadResponse,
    BulkRenameResponse,
    CommitResponse,
    FileRenameResponse,
    GitStatusResponse,
    ProjectCheckoutResponse,
    ProjectCreateResponse,
    ProjectEditResponse,
    ProjectListResponse,
    ProjectSyncCheckResponse,
    PendingUploadsResponse,
)
from app.service.git import GitService, RenameConflictError

router = APIRouter()

git_service = GitService()

# Create a dependency instance at module level
validate_elan_files_dep = Depends(validate_multiple_elan_files)


@router.get("/check", response_model=GitStatusResponse)
async def check_git(user: User = get_admin_dep) -> GitStatusResponse:
    """Check if Git is available on the system.

    Args:
        user: Authenticated admin user.

    Returns:
        GitStatusResponse: Git availability status, version, and any errors.

    Raises:
        HTTPException: 500 if Git check fails.

    """
    try:
        result = git_service.check_git_availability()
        return GitStatusResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/create", response_model=ProjectCreateResponse)
async def create_project(
    project_data: ProjectCreateRequest,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Create a new ELAN project with Git repository.

    Args:
        project_data: Project creation request containing project name.
        user: Authenticated admin user.

    Returns:
        ProjectCreateResponse: Details of the created project including path and Git status.

    Raises:
        HTTPException: 400 if project already exists, 500 if creation fails.

    """
    try:
        result = await git_service.create_project(
            project_data.project_name,
            project_data.description or "",
            db,
            user.user_id,
        )
        return ProjectCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_name}/commit", response_model=CommitResponse)
async def commit_changes(
    project_name: str, commit_data: CommitRequest
) -> CommitResponse:
    """Commit changes to a project.

    Args:
        project_name: Name of the project to commit changes to.
        commit_data: Commit request containing message and user information.

    Returns:
        CommitResponse: Details of the commit including hash and timestamp.

    Raises:
        HTTPException: 404 if project not found, 400 if no changes or invalid data, 500 if commit fails.

    """
    try:
        result = git_service.commit_changes(
            project_name, commit_data.commit_message, commit_data.user_name
        )
        return CommitResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_id}/upload", response_model=BatchFileUploadResponse)
async def upload_elan_files(
    project_id: int,
    user_name: str = Form(...),
    files: list[UploadFile] = validate_elan_files_dep,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
) -> BatchFileUploadResponse:
    """Upload an ELAN file to a project.

    Args:
        project_id: Name of the project to upload file to.
        file: ELAN file (.eaf) to upload. File is validated for format and size.
        user_name: Name of the user uploading the file.

    Returns:
        FileUploadResponse: Details of the uploaded file including filename and timestamp.

    Raises:
        HTTPException: 404 if project not found, 400 if file validation fails, 500 if upload fails.
        HTTPException: 400 if file validation fails.

    Note:
        File validation includes checking for .eaf extension, file size limits,
        valid ELAN XML structure, and filename compliance with the project's naming standard.

    """
    try:
        result = await git_service.add_elan_files(
            project_id, files, db, user.user_id, user_name
        )
        return BatchFileUploadResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects/{project_name}/branches")
async def get_project_branches(project_name: str):
    """Get all branches for a project."""
    try:
        result = git_service.get_branches(project_name)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/projects/{project_name}/checkout", response_model=ProjectCheckoutResponse
)
async def checkout_project_branch(
    project_name: str,
    checkout_data: ProjectCheckoutRequest,
    user: User = get_admin_dep,
):
    """Switch to a different branch in the given project."""
    try:
        result = git_service.checkout_branch(project_name, checkout_data.branch_name)
        return ProjectCheckoutResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """List all project names for the current instance (admin only)."""
    instance_id = 1
    projects = await git_service.list_projects(db, instance_id)
    return ProjectListResponse(projects=projects)


@router.get("/user-projects", response_model=ProjectListResponse)
async def list_user_projects(
    db: AsyncSession = get_db_dep,
    user: User = get_user_dep,
):
    """List project names that the current user has access to."""
    instance_id = 1
    projects = await git_service.list_user_projects(db, user.user_id, instance_id)
    return ProjectListResponse(projects=projects)


@router.post("/projects/init-from-folder-upload", response_model=ProjectCreateResponse)
async def init_project_from_folder_upload(
    project_name: str = Form(...),
    description: str = Form(...),
    files: list[UploadFile] | None = None,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Initialize a project by uploading a folder (only .eaf files and structure are kept)."""
    if files is None:
        files = []
    try:
        result = await git_service.init_project_from_folder_upload(
            project_name, description, files, db, user.user_id
        )
        return ProjectCreateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects/{project_name}/files")
async def get_project_files(
    project_name: str,
    include_media: bool = False,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Get project files, optionally with media information.

    Args:
        project_name: Name of the project
        include_media: Whether to include media filenames for each file
        db: Database session
        user: Authenticated admin user

    Returns:
        ProjectFilesResponse or ProjectFilesWithMediaResponse depending on include_media

    """
    try:
        result = await git_service.list_project_files(project_name, db, include_media)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects/{project_name}/synchronize/check")
async def synchronize_project_check(
    project_name: str,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
    response_model=ProjectSyncCheckResponse,
):
    """Synchronize the project's elan_files folder with the git repo and database."""
    try:
        return git_service.synchronize_project_check(project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/projects/{project_name}")
async def delete_project(
    project_name: str,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Delete a project, its files, and all associated database artifacts."""
    try:
        await git_service.delete_project(project_name, db)
        return {"status": "success", "detail": f"Project '{project_name}' deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/projects/{project_name}/edit",
    response_model=ProjectEditResponse,
)
async def edit_project(
    project_name: str,
    req: ProjectEditRequest,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    try:
        result = await git_service.edit_project(
            project_name, req.new_project_name, req.new_project_description, db
        )
        return ProjectEditResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/projects/{project_name}/synchronize", response_model=ProjectSyncCheckResponse
)
async def synchronize_project(
    project_name: str,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Synchronize the project's elan_files folder with the git repo and update the database.

    Only changed, added, or deleted files are processed.
    """
    try:
        result = await git_service.synchronize_project(project_name, db, user.user_id)
        return ProjectSyncCheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_name}/discard-local-changes")
async def discard_local_changes(
    project_name: str,
    user: User = get_admin_dep,
):
    """Discard all local changes and reset the project folder to match the master branch."""
    try:
        result = git_service.discard_local_changes(project_name)
        return {"status": "success", "detail": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_name}/restore-from-backup")
async def restore_from_backup(
    project_name: str,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Restore the project folder from the most recent backup and update the database."""
    try:
        result = await git_service.restore_project_from_backup(
            project_name, db, user.user_id
        )
        return {"status": "success", "detail": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_name}/decline-backup")
async def decline_backup(
    project_name: str,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Decline restoration of the most recent backup for the project, delete it and erase all related data from the database."""
    try:
        await git_service.decline_project_backup(db, project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/projects/{project_name}/admin/pending-uploads",
    response_model=PendingUploadsResponse,
)
async def get_pending_uploads(
    project_name: str,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Get all uploads pending admin approval."""
    try:
        result = await git_service.get_pending_uploads_with_status(project_name, db)
        return PendingUploadsResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_name}/rename-file", response_model=FileRenameResponse)
async def rename_file(
    project_name: str,
    elan_id: int = Form(...),
    new_filename: str = Form(...),
    db: AsyncSession = get_db_dep,
    user: User = get_user_dep,
) -> FileRenameResponse:
    """Rename a single file in the project."""
    try:
        result = await git_service.rename_file(
            project_name=project_name,
            elan_id=elan_id,
            new_filename=new_filename,
            db=db,
        )
        return result
    except RenameConflictError as e:
        # Return conflict info with 409 status code
        return FileRenameResponse(
            project_name=project_name,
            old_filename="",  # Will be filled by service if needed
            new_filename=new_filename,
            success=False,
            committed=False,
            commit_hash=None,
            renamed_at="",
            message=str(e),
            conflict_elan_id=e.conflict_elan_id,
            message_key=e.message_key,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_name}/rename-files", response_model=BulkRenameResponse)
async def rename_files(
    project_name: str,
    request: BulkRenameRequest,
    db: AsyncSession = get_db_dep,
    user: User = get_user_dep,
) -> BulkRenameResponse:
    """Rename multiple files in the project."""
    try:
        renames = [
            {"elan_id": rename.elan_id, "new_filename": rename.new_filename}
            for rename in request.renames
        ]
        result = await git_service.rename_files(
            project_name=project_name,
            renames=renames,
            db=db,
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_name}/download")
async def download_files(
    project_name: str,
    request: DownloadFilesRequest,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Download selected files as a ZIP archive (admin only)."""
    try:
        result = await git_service.download_files(project_name, request.elan_ids, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
