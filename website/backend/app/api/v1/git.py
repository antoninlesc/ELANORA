from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db_dep
from app.dependency.elan_validation import validate_multiple_elan_files
from app.dependency.user import get_admin_dep
from app.model.user import User
from app.schema.requests.git import (
    CommitRequest,
    ProjectCheckoutRequest,
    ProjectCreateRequest,
    ProjectRenameRequest,
)
from app.schema.responses.git import (
    BatchFileUploadResponse,
    CommitResponse,
    GitStatusResponse,
    ProjectCheckoutResponse,
    ProjectCreateResponse,
    ProjectListResponse,
    ProjectRenameResponse,
    ProjectStatusResponse,
)
from app.service.git import GitService

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
            project_data.description,
            db,
            user.user_id,
        )
        return ProjectCreateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects/{project_name}/status", response_model=ProjectStatusResponse)
async def get_project_status(project_name: str) -> ProjectStatusResponse:
    """Get Git status of a project.

    Args:
        project_name: Name of the project to check status for.

    Returns:
        ProjectStatusResponse: Project status including file changes, recent commits, and conflicts.

    Raises:
        HTTPException: 404 if project not found, 500 if status check fails.

    """
    try:
        result = git_service.get_project_status(project_name)
        return ProjectStatusResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
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


@router.post("/projects/{project_name}/upload", response_model=BatchFileUploadResponse)
async def upload_elan_files(
    project_name: str,
    user_name: str = "user",
    files: list[UploadFile] = validate_elan_files_dep,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
) -> BatchFileUploadResponse:
    """Upload an ELAN file to a project.

    Args:
        project_name: Name of the project to upload file to.
        file: ELAN file (.eaf) to upload. File is validated for format and size.
        user_name: Name of the user uploading the file (defaults to "user").

    Returns:
        FileUploadResponse: Details of the uploaded file including filename and timestamp.

    Raises:
        HTTPException: 404 if project not found, 400 if file validation fails, 500 if upload fails.

    Note:
        File validation includes checking for .eaf extension, file size limits,
        and valid ELAN XML structure.

    """
    try:
        result = await git_service.add_elan_files(
            project_name, files, db, user.user_id, user_name
        )
        return BatchFileUploadResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
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


@router.post("/projects/{project_name}/resolve-conflicts")
async def resolve_conflicts(
    project_name: str,
    branch_name: str,
    resolution_strategy: str = "accept_incoming",
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Resolve conflicts and merge a branch."""
    try:
        result = await git_service.resolve_conflicts(
            project_name, branch_name, resolution_strategy, db, user.user_id
        )
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
    """List all project names for the current instance."""
    instance_id = 1
    project_names = await git_service.list_projects(db, instance_id)
    return ProjectListResponse(projects=project_names)


@router.post("/projects/init-from-folder-upload", response_model=ProjectCreateResponse)
async def init_project_from_folder_upload(
    project_name: str = Form(...),
    description: str = Form(...),
    files: list[UploadFile] = File(...),
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Initialize a project by uploading a folder (only .eaf files and structure are kept)."""
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
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """List all .eaf files and folders containing .eaf files in a project as a tree."""
    try:
        result = await git_service.list_project_files(project_name)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_name}/synchronize")
async def synchronize_project(
    project_name: str,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Synchronize the project's elan_files folder with the git repo and database."""
    try:
        result = await git_service.synchronize_project(project_name, db, user.user_id)
        return {"status": "success", "detail": result}
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
    "/projects/{project_name}/rename",
    response_model=ProjectRenameResponse,
)
async def rename_project(
    project_name: str,
    req: ProjectRenameRequest,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Rename a project (folder and DB)."""
    try:
        result = await git_service.rename_project(
            project_name, req.new_project_name, db
        )
        return ProjectRenameResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
