from sqlalchemy.ext.asyncio import AsyncSession

from app.model.instance import Instance
from app.utils.database import DatabaseUtils


async def get_instance_count(db: AsyncSession) -> int:
    from sqlalchemy import func

    result = await DatabaseUtils.get_aggregated_data(
        db, Instance, {"count": func.count(Instance.instance_id)}
    )
    return result[0]["count"] if result else 0


async def create_instance(db: AsyncSession, data: dict):
    instance = Instance(**data)
    return await DatabaseUtils.create(db, instance)


async def get_instance_by_name(db: AsyncSession, name: str):
    result = await DatabaseUtils.get_by_filter(
        db, Instance, {"instance_name": name}, limit=1
    )
    return result[0] if result else None


async def get_first_instance(db: AsyncSession):
    result = await DatabaseUtils.get_all(db, Instance)
    return result[0] if result else None


async def update_instance(db: AsyncSession, instance_id: int, data: dict):
    await DatabaseUtils.update_by_filter(
        db, Instance, {"instance_id": instance_id}, data
    )
    return await DatabaseUtils.get_by_id(db, Instance, "instance_id", instance_id)
