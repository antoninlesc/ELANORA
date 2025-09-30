from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db_dep
from app.schema.requests.tier import (
    CreateSectionRequest,
    DeleteSectionRequest,
    MoveTierGroupRequest,
    RenameSectionRequest,
    CreateTierGroupRequest,
)
from app.schema.responses.tier import SectionsAndGroupsResponse, TierTreeResponse
from app.service.tier import TierGroupService, TierSectionService, TierService

router = APIRouter()


@router.get("/{project_name}", response_model=TierTreeResponse)
async def get_tiers(project_name: str, db: AsyncSession = get_db_dep):
    """Get all tiers for a project, grouped by ELAN file.

    Returns a list of tier trees (one per file).
    """
    result = await TierService.get_project_tiers_grouped_by_file(db, project_name)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Project not found or no tiers available."
        )

    # Unwrap the 'tiers' key if present
    tiers_dict = result["tiers"] if "tiers" in result else result

    # Now serialize
    serialized = {k: [n.model_dump() for n in v] for k, v in tiers_dict.items()}
    return {"tiers": serialized}


@router.get("/{project_id}/sections", response_model=SectionsAndGroupsResponse)
async def get_sections_and_groups(
    project_id: int, include_staged: bool = False, db: AsyncSession = get_db_dep
):
    return await TierSectionService.get_sections_and_groups(
        db, project_id, include_staged
    )


@router.post("/sections/create")
async def create_section(request: CreateSectionRequest, db: AsyncSession = get_db_dep):
    return await TierSectionService.create_section(
        db, request.project_id, request.name, request.is_staged, request.session_id
    )


@router.post("/sections/rename")
async def rename_section(request: RenameSectionRequest, db: AsyncSession = get_db_dep):
    return await TierSectionService.rename_section(
        db, request.section_id, request.new_name, request.is_staged
    )


@router.post("/sections/delete")
async def delete_section(request: DeleteSectionRequest, db: AsyncSession = get_db_dep):
    return await TierSectionService.delete_section(
        db, request.section_id, request.is_staged
    )


@router.post("/tier_group/move")
async def move_tier_group(request: MoveTierGroupRequest, db: AsyncSession = get_db_dep):
    return await TierGroupService.assign_group_to_section(
        db,
        request.tier_group_id,
        request.section_id,
        request.project_id,
        request.tier_id,
        request.tier_name,
        request.is_staged,
    )


@router.post("/tier_group/create")
async def create_tier_group(
    request: CreateTierGroupRequest, db: AsyncSession = get_db_dep
):
    return await TierGroupService.create_group(
        db,
        request.section_id,
        request.project_id,
        request.tier_id,
        request.tier_name,
        request.is_staged,
    )
