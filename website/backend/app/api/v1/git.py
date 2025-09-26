from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.elan_file import get_elan_file_name_by_id
from app.dependency.database import get_db_dep
from app.dependency.elan_validation import validate_multiple_elan_files
from app.dependency.user import get_admin_dep, get_user_dep
from app.model.user import User
from app.schema.requests.git import (
    BulkRenameRequest,
)
from app.schema.responses.git import (
    BulkRenameResponse,
    FileRenameResponse,
    GitStatusResponse,
    ProjectSyncCheckResponse,
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
        # Get the old filename from database for conflict response
        old_filename = await get_elan_file_name_by_id(db, elan_id) or ""

        # Return conflict info with 409 status code
        return FileRenameResponse(
            project_name=project_name,
            old_filename=old_filename,
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
