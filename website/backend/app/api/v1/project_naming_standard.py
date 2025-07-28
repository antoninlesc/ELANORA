from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db_dep
from app.service.project_naming_standard import ProjectNamingStandardService
from app.schema.requests.project_naming_standard import CreateNamingStandardRequest
from app.schema.responses.project_naming_standard import NamingStandardResponse

router = APIRouter()


@router.get("/project/{project_id}")
async def get_standards_for_project(project_id: int, db: AsyncSession = get_db_dep):
    return await ProjectNamingStandardService.get_standards_for_project(db, project_id)


@router.get("/{standard_id}")
async def get_standard_with_components(standard_id: int, db: AsyncSession = get_db_dep):
    result = await ProjectNamingStandardService.get_standard_with_components(
        db, standard_id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Standard not found")
    return result


@router.post("/create", response_model=NamingStandardResponse)
async def create_standard_with_components(
    req: CreateNamingStandardRequest,
    db: AsyncSession = get_db_dep,
):
    components = [c.model_dump() for c in req.components]
    return await ProjectNamingStandardService.create_standard_with_components(
        db,
        req.project_id,
        req.name,
        req.file_type_id,
        req.pattern,
        req.description,
        components,
    )


@router.put("/{standard_id}/update")
async def update_standard_and_components(
    standard_id: int,
    update_fields: dict,
    components: list[dict],
    db: AsyncSession = get_db_dep,
):
    return await ProjectNamingStandardService.update_standard_and_components(
        db, standard_id, update_fields, components
    )


@router.delete("/{standard_id}")
async def delete_standard(standard_id: int, db: AsyncSession = get_db_dep):
    return await ProjectNamingStandardService.delete_standard(db, standard_id)


@router.get("/project/{project_id}/component-names")
async def get_component_names(project_id: int, db: AsyncSession = get_db_dep):
    return await ProjectNamingStandardService.get_unique_component_names_by_project(
        db, project_id
    )
