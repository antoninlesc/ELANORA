"""TimeSlot CRUD operations using DatabaseUtils."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.time_slot import TimeSlot
from app.utils.database import DatabaseUtils

logger = get_logger()


async def get_time_slots_by_content_id(
    db: AsyncSession, content_id: int
) -> list[TimeSlot]:
    """Get all time slots for a specific file content."""
    filters = {"content_id": content_id}
    order_by = [TimeSlot.time_value]
    return await DatabaseUtils.get_by_filter(db, TimeSlot, filters, order_by=order_by)


async def get_time_slots_as_dict(db: AsyncSession, content_id: int) -> dict[str, int]:
    """Get time slots as dictionary mapping time_slot_id -> time_value."""
    time_slots = await get_time_slots_by_content_id(db, content_id)
    return {ts.time_slot_id: ts.time_value for ts in time_slots}


async def get_time_slot_by_id_and_content(
    db: AsyncSession, time_slot_id: str, content_id: int
) -> TimeSlot | None:
    """Get a specific time slot by ID and content."""
    filters = {"time_slot_id": time_slot_id, "content_id": content_id}
    return await DatabaseUtils.get_one_or_none(db, TimeSlot, filters=filters)


async def create_time_slot(
    db: AsyncSession, time_slot_id: str, content_id: int, time_value: int
) -> TimeSlot:
    """Create a new time slot."""
    time_slot = TimeSlot(
        time_slot_id=time_slot_id, content_id=content_id, time_value=time_value
    )
    return await DatabaseUtils.create(db, time_slot)


async def bulk_create_time_slots(db: AsyncSession, time_slots_data: list[dict]) -> None:
    """Bulk create time slots for performance."""
    await DatabaseUtils.bulk_insert(
        db, TimeSlot, time_slots_data, ignore_duplicates=True
    )


async def delete_time_slots_by_content_id(db: AsyncSession, content_id: int) -> int:
    """Delete all time slots for a specific content."""
    return await DatabaseUtils.delete_by_filter(db, TimeSlot, content_id=content_id)


async def get_highest_time_slot_number(db: AsyncSession, content_id: int) -> int:
    """Get the highest time slot number for generating new IDs."""
    time_slots = await get_time_slots_by_content_id(db, content_id)
    if not time_slots:
        return 0

    # Extract numeric part from time slot IDs (ts1, ts2, etc.)
    max_number = 0
    for ts in time_slots:
        if ts.time_slot_id.startswith("ts") and ts.time_slot_id[2:].isdigit():
            number = int(ts.time_slot_id[2:])
            max_number = max(max_number, number)

    return max_number


async def upsert_time_slot(
    db: AsyncSession, time_slot_id: str, content_id: int, time_value: int
) -> tuple[TimeSlot, bool]:
    """Get or create time slot using upsert."""
    return await DatabaseUtils.upsert(
        db,
        TimeSlot,
        defaults={"time_value": time_value},
        time_slot_id=time_slot_id,
        content_id=content_id,
    )
