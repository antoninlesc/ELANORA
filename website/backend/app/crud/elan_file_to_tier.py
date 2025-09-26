from app.crud.elan_file import get_elan_file_by_id
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.elan_file_to_tier import ElanFileToTier
from app.utils.database import DatabaseUtils

logger = get_logger()


async def add_elan_file_to_tier(db: AsyncSession, elan_id: int, tier_id: int) -> None:
    """Add an ELAN file to tier association if it doesn't already exist."""
    filters = {"elan_id": elan_id, "tier_id": tier_id}
    exists = await DatabaseUtils.get_one_or_none(db, ElanFileToTier, filters)
    if not exists:
        assoc = ElanFileToTier(elan_id=elan_id, tier_id=tier_id)
        await DatabaseUtils.create(db, assoc)


async def remove_elan_file_from_tier(db: AsyncSession, elan_id: int, tier_id: int):
    await DatabaseUtils.delete_by_filter(
        db, ElanFileToTier, elan_id=elan_id, tier_id=tier_id
    )


async def update_elan_file_tier(
    db: AsyncSession, elan_id: int, old_tier_id: int, new_tier_id: int
):
    await DatabaseUtils.update_by_filter(
        db,
        ElanFileToTier,
        {"elan_id": elan_id, "tier_id": old_tier_id},
        {"tier_id": new_tier_id},
    )


async def get_tiers_for_elan_file(db: AsyncSession, elan_id: int) -> list[int]:
    """Get all tier_ids associated with an ELAN file."""
    from app.crud.elan_file import get_elan_file_by_id

    # First get the content_id for this elan_id
    elan_file = await get_elan_file_by_id(db, elan_id)
    if not elan_file:
        return []

    filters = {"content_id": elan_file.content_id}
    associations = await DatabaseUtils.get_by_filter(db, ElanFileToTier, filters)
    return [assoc.tier_id for assoc in associations]


async def sync_elan_file_to_tiers(
    db: AsyncSession, elan_id: int, new_tier_ids: list[int]
) -> None:
    """Synchronize ELAN file associations with tiers.

    Args:
        db: Database session
        elan_id: ID of the ELAN file
        new_tier_ids: List of tier IDs to associate with the file

    """
    # Get content_id from elan_id
    elan_file = await get_elan_file_by_id(db, elan_id)
    if not elan_file:
        return

    current_tier_ids = set(await get_tiers_for_elan_file(db, elan_id))
    new_tier_ids_set = set(new_tier_ids)

    # Add new associations
    for tier_id in new_tier_ids_set - current_tier_ids:
        assoc = ElanFileToTier(content_id=elan_file.content_id, tier_id=tier_id)
        await DatabaseUtils.create(db, assoc)

    # Remove old associations
    for tier_id in current_tier_ids - new_tier_ids_set:
        await DatabaseUtils.delete_by_filter(
            db, ElanFileToTier, content_id=elan_file.content_id, tier_id=tier_id
        )
