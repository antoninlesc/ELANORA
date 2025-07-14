"""Project API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.dependency.database import get_db_dep
from app.dependency.user import get_user_dep
from app.model.user import User
from app.crud.project import get_all_projects, get_project_by_id
from pydantic import BaseModel

router = APIRouter()


class ProjectResponse(BaseModel):
    """Schema for project data."""

    project_id: int
    project_name: str
    description: str
    instance_id: int
    project_path: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    user: User = get_user_dep,
    db: AsyncSession = get_db_dep,
) -> List[ProjectResponse]:
    """Get all projects (authenticated users only)."""
    try:
        projects = await get_all_projects(db)
        return [ProjectResponse.model_validate(project) for project in projects]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}",
        )


@router.get("/{project_id}", response_model=ProjectResponse)
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
            detail=f"Failed to retrieve project: {str(e)}",
        )
