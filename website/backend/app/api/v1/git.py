from dependency.elan_validation import validate_elan_file
from dependency.user import get_admin_dep
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from model.user import User
from schema.requests.git import (
    CommitRequest,
    ProjectCreateRequest,
)
from schema.responses.git import (
    CommitResponse,
    FileUploadResponse,
    GitStatusResponse,
    ProjectCreateResponse,
    ProjectStatusResponse,
)
from service.git import GitService

router = APIRouter()
git_service = GitService()


# Create a dependency instance at module level
validate_elan_file_dep = Depends(validate_elan_file)


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
    project_data: ProjectCreateRequest, user: User = get_admin_dep
) -> ProjectCreateResponse:
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
        result = git_service.create_project(project_data.project_name)
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


@router.post("/projects/{project_name}/upload", response_model=FileUploadResponse)
async def upload_elan_file(
    project_name: str,
    user_name: str = "user",
    file: UploadFile = validate_elan_file_dep,
) -> FileUploadResponse:
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
        result = await git_service.add_elan_file(project_name, file, user_name)
        return FileUploadResponse(**result)
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
    project_name: str, branch_name: str, resolution_strategy: str = "accept_incoming"
):
    """Resolve conflicts and merge a branch."""
    try:
        result = git_service.resolve_conflicts(
            project_name, branch_name, resolution_strategy
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
