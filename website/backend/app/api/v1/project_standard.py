from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.effective_naming_standard_locations import (
    EFFECTIVE_NAMING_STANDARD_LOCATIONS,
)
from app.dependency.database import get_db_dep
from app.dependency.user import get_admin_dep
from app.schema.requests.effective_naming_standard import (
    AssignEffectiveNamingStandardRequest,
)
from app.schema.requests.project_naming_standard import (
    CreateNamingStandardRequest,
    ImportSelectedStandardsRequest,
)
from app.schema.responses.effective_naming_standard import (
    EffectiveNamingStandardResponse,
    GetEffectiveStandardsResponse,
    UnassignEffectiveNamingStandardResponse,
)
from app.schema.responses.project_location_file_type import (
    AddFileTypeToLocationResponse,
    FileTypeLocationOut,
    GetFileTypesForLocationResponse,
    RemoveFileTypeFromLocationResponse,
)
from app.schema.responses.project_naming_standard import (
    ImportSelectedStandardsResponse,
    NamingStandardResponse,
    ProjectWithStandardsResponse,
)
from app.service.effective_naming_standard import (
    assign_effective_standard,
    fetch_effective_standards,
    unassign_effective_standard,
)
from app.service.project_location_file_type import (
    service_add_file_type_to_location,
    service_get_file_types_for_location,
    service_remove_file_type_from_location,
)
from app.service.project_naming_standard import ProjectNamingStandardService

router = APIRouter()


@router.get(
    "/projects-with-standards", response_model=list[ProjectWithStandardsResponse]
)
async def get_projects_with_standards(db: AsyncSession = get_db_dep):
    return await ProjectNamingStandardService.get_projects_with_standards(db)


@router.post("/import", response_model=ImportSelectedStandardsResponse)
async def import_selected_standards(
    req: ImportSelectedStandardsRequest,
    db: AsyncSession = get_db_dep,
):
    return await ProjectNamingStandardService.import_selected_standards(
        db, req.target_project_id, req.standard_ids
    )


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
        req.project_file_type_id,
        req.pattern,
        req.description,
        components,
    )


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


@router.delete("/{standard_id}")
async def delete_standard(standard_id: int, db: AsyncSession = get_db_dep):
    return await ProjectNamingStandardService.delete_standard(db, standard_id)


@router.get("/project/{project_id}/component-names")
async def get_component_names(project_id: int, db: AsyncSession = get_db_dep):
    return await ProjectNamingStandardService.get_unique_component_names_by_project(
        db, project_id
    )


@router.get("/project/{project_id}/full")
async def get_project_naming_standards_full(
    project_id: int, db: AsyncSession = get_db_dep
):
    return await ProjectNamingStandardService.get_project_naming_standards_full(
        db, project_id
    )


@router.post(
    "/project/{project_id}/location/{location_id}/filetype/{file_type_id}/add",
    response_model=AddFileTypeToLocationResponse,
)
async def add_file_type(
    project_id: int,
    location_id: int,
    file_type_id: int,
    db: AsyncSession = get_db_dep,
):
    instance = await service_add_file_type_to_location(
        db, project_id, location_id, file_type_id
    )
    return {
        "success": True,
        "file_type": FileTypeLocationOut.model_validate(instance, from_attributes=True),
    }


@router.delete(
    "/project/{project_id}/location/{location_id}/filetype/{file_type_id}/remove",
    response_model=RemoveFileTypeFromLocationResponse,
)
async def remove_file_type(
    project_id: int,
    location_id: int,
    file_type_id: int,
    db: AsyncSession = get_db_dep,
):
    count = await service_remove_file_type_from_location(
        db, project_id, location_id, file_type_id
    )
    return {"success": True, "removed": count}


@router.get(
    "/project/{project_id}/location/{location_id}/filetypes",
    response_model=GetFileTypesForLocationResponse,
)
async def get_file_types(
    project_id: int,
    location_id: int,
    db: AsyncSession = get_db_dep,
):
    file_types = await service_get_file_types_for_location(db, project_id, location_id)
    return {
        "file_types": [
            FileTypeLocationOut.model_validate(ft, from_attributes=True)
            for ft in file_types
        ]
    }


@router.get("/locations")
async def get_effective_naming_standard_locations():
    return {"locations": EFFECTIVE_NAMING_STANDARD_LOCATIONS}


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
        db,
        project_id,
        project_file_type_id,
        payload.naming_standard_id,
        payload.location_id,
    )
    return {"success": True, "effective_standard": result}


@router.delete(
    "/project/{project_id}/filetype/{project_file_type_id}/location/{location_id}/unassign",
    response_model=UnassignEffectiveNamingStandardResponse,
)
async def unassign_standard(
    project_id: int,
    project_file_type_id: int,
    location_id: int,
    db: AsyncSession = get_db_dep,
    admin_user=get_admin_dep,
):
    await unassign_effective_standard(db, project_id, project_file_type_id, location_id)
    return {"success": True}


@router.get(
    "/project/{project_id}/location/{location_id}/effective-standards",
    response_model=GetEffectiveStandardsResponse,
)
async def get_effective_standards_for_location(
    project_id: int, location_id: int, db: AsyncSession = get_db_dep
):
    standards = await fetch_effective_standards(db, project_id, location_id)
    return {"effective_standards": standards}
