"""API endpoints for managing project-user associations (admin only)."""

import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.association import get_project_users, remove_user_from_project
from app.crud.project import (
    add_user_to_project,
    get_project_by_id,
    list_projects_by_instance,
    list_projects_by_user,
    update_user_project_permission,
)
from app.crud.user import get_all_active_users, get_user_by_id
from app.dependency.database import get_db_dep
from app.dependency.user import get_admin_dep
from app.model.user import User
from app.schema.requests.project_association import (
    AddUserToProjectRequest,
    UpdateUserPermissionRequest,
)
from app.schema.responses.project_association import (
    ProjectAssociationResponse,
    ProjectUserListResponse,
    UserProjectListResponse,
)
from app.service.notification import NotificationService

router = APIRouter()

# Constants to avoid duplication
PROJECT_NOT_FOUND = "Project not found"
USER_NOT_FOUND = "User not found"


@router.get("/projects/{project_id}/users", response_model=ProjectUserListResponse)
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
                {
                    "user_id": user_info["user_id"],
                    "username": user_info["username"],
                    "email": user_info["email"],
                    "permission": user_info["permission"],
                }
                for user_info in users
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/users/{user_id}/projects", response_model=UserProjectListResponse)
async def list_user_projects_admin(
    user_id: int,
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """List all projects associated with a specific user (admin only)."""
    try:
        # check if the user exists
        target_user = await get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        # Retrieve the user's projects
        projects = await list_projects_by_user(db, user_id, instance_id=1)

        return UserProjectListResponse(
            user_id=user_id,
            username=target_user.username,
            projects=[
                {
                    "project_id": project.project_id,
                    "project_name": project.project_name,
                    "description": project.description,
                }
                for project in projects
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/{project_id}/users", response_model=ProjectAssociationResponse)
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

        return ProjectAssociationResponse(
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
    "/projects/{project_id}/users/{user_id}",
    response_model=ProjectAssociationResponse,
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

        return ProjectAssociationResponse(
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
    "/projects/{project_id}/users/{user_id}",
    response_model=ProjectAssociationResponse,
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

        return ProjectAssociationResponse(
            project_name=project.project_name,
            user_id=user_id,
            username=target_user.username,
            permission=None,
            message=f"User {target_user.username} removed from project {project.project_name}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/overview", response_model=dict)
async def get_associations_overview(
    db: AsyncSession = get_db_dep,
    user: User = get_admin_dep,
):
    """Get an overview of all project-user associations (admin only)."""
    try:
        # Retrieve all projects
        projects = await list_projects_by_instance(db, instance_id=1)

        # Retrieve all active users
        users = await get_all_active_users(db)

        # Construire l'aperçu
        overview = {
            "total_projects": len(projects),
            "total_users": len(users),
            "projects": [],
        }

        for project in projects:
            project_users = await get_project_users(db, project.project_id)
            overview["projects"].append(
                {
                    "project_id": project.project_id,
                    "project_name": project.project_name,
                    "description": project.description,
                    "user_count": len(project_users),
                    "users": [
                        {
                            "user_id": assoc.user_id,
                            "username": assoc.user.username,
                            "permission": assoc.permission,
                        }
                        for assoc in project_users
                    ],
                }
            )

        return overview

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
