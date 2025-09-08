from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.effective_naming_standard import EFFECTIVE_NAMING_STANDARDS
from app.dependency.database import get_db_dep
from app.dependency.user import get_admin_dep
from app.service.effective_naming_standard import (
    assign_effective_standard,
    unassign_effective_standard,
    fetch_effective_standards,
)
from app.schema.requests.effective_naming_standard import (
    AssignEffectiveNamingStandardRequest,
)
from app.schema.responses.effective_naming_standard import (
    EffectiveNamingStandardResponse,
    UnassignEffectiveNamingStandardResponse,
    GetEffectiveStandardsResponse,
)

router = APIRouter()


@router.get("/effective-naming-standards")
async def get_effective_naming_standards():
    return {"effective_naming_standards": EFFECTIVE_NAMING_STANDARDS}


@router.post(
    "/project/{project_id}/filetype/{project_file_type_id}/assign",
    response_model=EffectiveNamingStandardResponse,
)
async def assign_standard(
    project_id: int,
    project_file_type_id: int,
    payload: AssignEffectiveNamingStandardRequest,
    db: AsyncSession = get_db_dep,
    admin_user=get_admin_dep,
):
    result = await assign_effective_standard(
        db, project_id, project_file_type_id, payload.naming_standard_id
    )
    return {"success": True, "effective_standard": result}


@router.delete(
    "/project/{project_id}/filetype/{project_file_type_id}/unassign",
    response_model=UnassignEffectiveNamingStandardResponse,
)
async def unassign_standard(
    project_id: int,
    project_file_type_id: int,
    db: AsyncSession = get_db_dep,
    admin_user=get_admin_dep,
):
    await unassign_effective_standard(db, project_id, project_file_type_id)
    return {"success": True}


@router.get(
    "/project/{project_id}/effective-standards",
    response_model=GetEffectiveStandardsResponse,
)
async def get_effective_standards(project_id: int, db: AsyncSession = get_db_dep):
    standards = await fetch_effective_standards(db, project_id)
    return {"effective_standards": standards}
