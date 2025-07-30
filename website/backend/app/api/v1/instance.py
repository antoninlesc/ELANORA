from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db_dep
from app.service import instance as instance_service
from app.schema.responses.instance import InstanceResponse

router = APIRouter()


@router.get("/info", response_model=InstanceResponse)
async def get_instance_info(
    db: AsyncSession = get_db_dep,
    name: str = Query(None, description="Instance name (optional)"),
):
    instance = await instance_service.get_instance_info(db, name)
    if not instance:
        return {}
    return instance
