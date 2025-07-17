from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db
from app.service.tier import TierService

router = APIRouter()


@router.get("/{project_name}", response_model=list)
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
    return result
