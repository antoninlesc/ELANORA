from sqlalchemy import func
from sqlalchemy import select as sql_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.accepted_value import AcceptedValue
from app.model.component_accepted_value import ComponentAcceptedValue
from app.utils.database import DatabaseUtils

logger = get_logger(__name__)


async def get_or_create_accepted_value(db: AsyncSession, value: str) -> AcceptedValue:
    """Get existing accepted value or create new one."""
    accepted_value, created = await DatabaseUtils.upsert(
        db, AcceptedValue, defaults={}, value=value
    )
    if created:
        await db.flush()
    return accepted_value


async def delete_orphaned_accepted_values(db: AsyncSession):
    try:
        logger.info("Starting orphaned AcceptedValue cleanup...")
        # Count before
        before = (
            await db.execute(sql_select(func.count()).select_from(AcceptedValue))
        ).scalar()
        logger.info(f"AcceptedValue rows before cleanup: {before}")
        # Delete orphans
        subquery = sql_select(ComponentAcceptedValue.accepted_value_id)
        conditions = [~AcceptedValue.id.in_(subquery)]
        result = await DatabaseUtils.delete_by_conditions(
            db, AcceptedValue, conditions=conditions
        )
        # Count after
        after = (
            await db.execute(sql_select(func.count()).select_from(AcceptedValue))
        ).scalar()
        logger.info(f"AcceptedValue rows after cleanup: {after}")
        await db.flush()
        return result
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Error during delete_orphaned_accepted_values: {e}", exc_info=True
        )
        raise
