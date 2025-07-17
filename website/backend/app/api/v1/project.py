"""Project API endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.project import get_project_by_id
from app.dependency.database import get_db_dep
from app.dependency.user import get_user_dep
from app.model.user import User
from app.schema.responses.project import ProjectResponse
from app.service.git import list_projects_by_instance

router = APIRouter()


@router.get("/list", response_model=list[ProjectResponse])
async def get_projects(
    user: User = get_user_dep,
    db: AsyncSession = get_db_dep,
) -> list[ProjectResponse]:
    """Get all projects (authenticated users only)."""
    try:
        projects = await list_projects_by_instance(db, user.user_id)
        return [ProjectResponse.model_validate(project) for project in projects]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {e!s}",
        )


@router.get("/details/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    user: User = get_user_dep,
    db: AsyncSession = get_db_dep,
) -> ProjectResponse:
    """Get a specific project by ID (authenticated users only)."""
    try:
        project = await get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        return ProjectResponse.model_validate(project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project: {e!s}",
        )
