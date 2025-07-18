from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db
from app.service.tier import TierService, TierSectionService, TierGroupService
from app.schema.responses.tier import TierTreeResponse, SectionsAndGroupsResponse
from app.schema.requests.tier import (
    CreateSectionRequest,
    RenameSectionRequest,
    DeleteSectionRequest,
)
from app.schema.requests.tier import MoveTierGroupRequest

router = APIRouter()


@router.get("/{project_name}", response_model=TierTreeResponse)
async def get_tiers(project_name: str, db: AsyncSession = Depends(get_db)):
    """
    Get all tiers for a project, grouped by ELAN file.
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
async def get_sections_and_groups(project_id: int, db: AsyncSession = Depends(get_db)):
    return await TierSectionService.get_sections_and_groups(db, project_id)


@router.post("/sections/create")
async def create_section(
    request: CreateSectionRequest, db: AsyncSession = Depends(get_db)
):
    return await TierSectionService.create_section(db, request.project_id, request.name)


@router.post("/sections/rename")
async def rename_section(
    request: RenameSectionRequest, db: AsyncSession = Depends(get_db)
):
    return await TierSectionService.rename_section(
        db, request.section_id, request.new_name
    )


@router.post("/sections/delete")
async def delete_section(
    request: DeleteSectionRequest, db: AsyncSession = Depends(get_db)
):
    return await TierSectionService.delete_section(db, request.section_id)


@router.post("/tier_group/move")
async def move_tier_group(
    request: MoveTierGroupRequest, db: AsyncSession = Depends(get_db)
):
    return await TierGroupService.assign_group_to_section(
        db, request.tier_group_id, request.section_id
    )
