from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.instance import (
    get_instance_by_name,
    get_first_instance,
    create_instance as crud_create_instance,
    update_instance as crud_update_instance,
)


async def get_instance_info(db: AsyncSession, name: str | None):
    if name:
        return await get_instance_by_name(db, name)
    return await get_first_instance(db)


async def create_instance(db: AsyncSession, data: dict):
    try:
        instance = await crud_create_instance(db, data)
        await db.commit()
        return instance
    except Exception:
        await db.rollback()
        raise


async def update_instance(db: AsyncSession, instance_id: int, data: dict):
    try:
        instance = await crud_update_instance(db, instance_id, data)
        await db.commit()
        return instance
    except Exception:
        await db.rollback()
        raise
