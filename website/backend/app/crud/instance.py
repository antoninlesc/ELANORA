from sqlalchemy.ext.asyncio import AsyncSession
from app.model.instance import Instance
from app.utils.database import DatabaseUtils


async def get_instance_count(db: AsyncSession) -> int:
    return await DatabaseUtils.count(db, Instance, None)


async def create_instance(db: AsyncSession, data: dict):
    instance = Instance(**data)
    return await DatabaseUtils.create_and_commit(db, instance)


async def get_instance_by_name(db: AsyncSession, name: str):
    return await DatabaseUtils.get_one_by_filter(db, Instance, {"instance_name": name})


async def get_first_instance(db: AsyncSession):
    result = await DatabaseUtils.get_all(db, Instance)
    return result[0] if result else None


async def update_instance(db: AsyncSession, instance_id: int, data: dict):
    await DatabaseUtils.update_by_filter(
        db, Instance, {"instance_id": instance_id}, data
    )
    return await DatabaseUtils.get_by_id(db, Instance, "instance_id", instance_id)
