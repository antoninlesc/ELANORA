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


async def get_instance_by_name(db: AsyncSession, name: str) -> Instance | None:
    """Get instance by name."""
    filters = {"instance_name": name}
    return await DatabaseUtils.get_one_or_none(db, Instance, filters=filters)


async def get_first_instance(db: AsyncSession) -> Instance | None:
    """Get the first instance (for single-instance setups)."""
    from sqlalchemy import select

    stmt = select(Instance).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_instance(
    db: AsyncSession, instance_id: int, data: dict
) -> Instance | None:
    """Update instance and return updated instance."""
    filters = {"instance_id": instance_id}
    updated_count = await DatabaseUtils.update_by_filter(db, Instance, filters, data)
    if updated_count > 0:
        return await DatabaseUtils.get_by_id(db, Instance, "instance_id", instance_id)
    return None
