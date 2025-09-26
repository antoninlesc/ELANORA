"""API endpoints for managing project-user associations (admin only)."""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.association import get_project_users, remove_user_from_project
from app.crud.project import (
    add_user_to_project,
    get_project_by_id,
    update_user_project_permission,
)
from app.crud.user import get_user_by_id
from app.dependency.database import get_db_dep
from app.dependency.elan_validation import validate_multiple_elan_files
from app.dependency.user import get_admin_dep, get_user_dep
from app.model.user import User
from app.schema.requests.git import ProjectCreateRequest
from app.schema.requests.project import (
    AddUserToProjectRequest,
    UpdateUserPermissionRequest,
)
from app.schema.responses.elan_file_media import ProjectFilesWithMediaResponse
from app.schema.responses.git import ProjectCreateResponse, ProjectListResponse
from app.schema.responses.project import (
    ProjectUserAssociationResponse,
    ProjectUserInfo,
    ProjectUserListResponse,
)
from app.service import elan_file_media as elan_media_service
from app.service.git import GitService
from app.service.notification import NotificationService

router = APIRouter()

git_service = GitService()

# Constants to avoid duplication
PROJECT_NOT_FOUND = "Project not found"
USER_NOT_FOUND = "User not found"

# Create a dependency instance at module level
validate_elan_files_dep = Depends(validate_multiple_elan_files)


@router.get("/{project_id}/users", response_model=ProjectUserListResponse)
async def list_project_users(
    project_id: int,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """List all users associated with a specific project (admin only)."""
    try:
        # check if the project exists
        project = await get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=PROJECT_NOT_FOUND)

        # Retrieve associations
        users = await get_project_users(db, project.project_id)

        return ProjectUserListResponse(
            project_name=project.project_name,
            users=[
                ProjectUserInfo(
                    user_id=user_info["user_id"],
                    username=user_info["username"],
                    email=user_info["email"],
                    permission=user_info["permission"],
                )
                for user_info in users
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{project_id}/users", response_model=ProjectUserAssociationResponse)
async def add_user_to_project_admin(
    project_id: int,
    request: AddUserToProjectRequest,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Add a user to a project with specified permissions (admin only)."""
    try:
        # check if the project exists
        project = await get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=PROJECT_NOT_FOUND)

        # check if the user exists
        target_user = await get_user_by_id(db, request.user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        # Add the user to the project
        association = await add_user_to_project(
            db=db,
            user_id=request.user_id,
            project_id=project.project_id,
            permission=request.permission,
        )

        return ProjectUserAssociationResponse(
            project_name=project.project_name,
            user_id=request.user_id,
            username=target_user.username,
            permission=association.permission,
            message=f"User {target_user.username} added to project {project.project_name}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put(
    "/{project_id}/users/{user_id}",
    response_model=ProjectUserAssociationResponse,
)
async def update_user_project_permission_admin(
    project_id: int,
    user_id: int,
    request: UpdateUserPermissionRequest,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Update a user's permission in a project (admin only)."""
    try:
        # check if the project exists
        project = await get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=PROJECT_NOT_FOUND)

        # check if the user exists
        target_user = await get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        # Update the user's permission
        association = await update_user_project_permission(
            db=db,
            user_id=user_id,
            project_id=project.project_id,
            permission=request.permission,
        )

        if not association:
            raise HTTPException(
                status_code=404, detail="User is not associated with this project"
            )

        # Send notification and email about role change
        admin_name = f"{user.first_name} {user.last_name}"
        try:
            _, _ = await NotificationService.send_role_change_notification_and_email(
                db=db,
                user_id=user_id,
                user_email=target_user.email,
                username=target_user.username,
                project_name=project.project_name,
                new_role=str(request.permission.value),
                project_id=project.project_id,
                admin_name=admin_name,
                language="fr",  # You could get this from user preferences or request
            )
        except Exception as e:
            # Log the error but don't fail the permission update
            logging.warning(f"Failed to send role change notification: {e!s}")

        # Commit the changes
        await db.commit()

        return ProjectUserAssociationResponse(
            project_name=project.project_name,
            user_id=user_id,
            username=target_user.username,
            permission=association.permission,
            message=f"User {target_user.username} permission updated to {request.permission} in project {project.project_name}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/{project_id}/users/{user_id}",
    response_model=ProjectUserAssociationResponse,
)
async def remove_user_from_project_admin(
    project_id: int,
    user_id: int,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Remove a user from a project (admin only)."""
    try:
        # Vérifier que le projet existe
        project = await get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=PROJECT_NOT_FOUND)

        # Vérifier que l'utilisateur existe
        target_user = await get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        await remove_user_from_project(db, user_id, project.project_id)

        return ProjectUserAssociationResponse(
            project_name=project.project_name,
            user_id=user_id,
            username=target_user.username,
            permission=None,
            message=f"User {target_user.username} removed from project {project.project_name}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/create", response_model=ProjectCreateResponse)
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


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """List all project names for the current instance (admin only)."""
    instance_id = 1
    projects = await git_service.list_projects(db, instance_id)
    return ProjectListResponse(projects=projects)


@router.post("/init-from-folder-upload", response_model=ProjectCreateResponse)
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


@router.get("/{project_name}/files")
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


@router.get(
    "/{project_id}/files-with-media",
    response_model=ProjectFilesWithMediaResponse,
)
async def get_project_files_with_media(
    project_id: int,
    db: AsyncSession = get_db_dep,
    current_user: User = get_user_dep,
) -> ProjectFilesWithMediaResponse:
    """Get project files with their associated media for rename suggestions."""
    return await elan_media_service.get_project_files_with_media(db, project_id)
