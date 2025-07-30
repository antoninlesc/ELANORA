"""Tier CRUD operations - Pure database access layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.annotation import Annotation
from app.model.association import ElanFileToTier
from app.model.tier import Tier
from app.utils.database import DatabaseUtils

logger = get_logger()


async def delete_tiers_for_elan_file(db: AsyncSession, elan_id: int):
    logger.info(f"Bulk deleting tiers and annotations for elan_id={elan_id}")
    try:
        tier_ids = [
            row[0]
            for row in await db.execute(
                select(ElanFileToTier.tier_id).where(ElanFileToTier.elan_id == elan_id)
            )
        ]
        logger.info(f"tier_ids to delete for elan_id={elan_id}: {tier_ids}")
        if tier_ids:
            await DatabaseUtils.bulk_delete(
                db, Annotation, Annotation.tier_id.in_(tier_ids)
            )
            await DatabaseUtils.bulk_delete(
                db,
                ElanFileToTier,
                (ElanFileToTier.elan_id == elan_id)
                & ElanFileToTier.tier_id.in_(tier_ids),
            )
            orphaned_tiers = [
                row[0]
                for row in await db.execute(
                    select(Tier.tier_id).where(
                        Tier.tier_id.in_(tier_ids),
                        ~Tier.tier_id.in_(select(ElanFileToTier.tier_id)),
                    )
                )
            ]
            if orphaned_tiers:
                await DatabaseUtils.bulk_delete(
                    db, Tier, Tier.tier_id.in_(orphaned_tiers)
                )
        logger.info(f"Bulk deleted tiers and annotations for elan_id={elan_id}")
    except Exception as e:
        logger.error(f"Failed to bulk delete tiers for elan_id={elan_id}: {e}")


async def get_tier_by_id(db: AsyncSession, tier_id: int) -> Tier | None:
    """Retrieve a tier by ID."""
    return await DatabaseUtils.get_by_id(db, Tier, "tier_id", tier_id)


async def get_all_tiers(db: AsyncSession) -> list[Tier]:
    """Get all tiers."""
    return await DatabaseUtils.get_all(db, Tier)


async def get_child_tiers(db: AsyncSession, parent_tier_id: int) -> list[Tier]:
    """Get all child tiers of a parent tier."""
    filters = {"parent_tier_id": parent_tier_id}
    return await DatabaseUtils.get_by_filter(db, Tier, filters)


async def get_root_tiers(db: AsyncSession) -> list[Tier]:
    """Get all root tiers (no parent)."""
    filters = {"parent_tier_id": None}
    return await DatabaseUtils.get_by_filter(db, Tier, filters)


async def get_tier_id_by_name(db: AsyncSession, tier_name: str) -> int | None:
    filters = {"tier_name": tier_name}
    tier = await DatabaseUtils.get_one_by_filter(db, Tier, filters)
    return tier.tier_id if tier else None


async def get_tier_by_name(db: AsyncSession, tier_name: str) -> Tier | None:
    filters = {"tier_name": tier_name}
    return await DatabaseUtils.get_one_by_filter(db, Tier, filters)


async def create_tier_in_db(
    db: AsyncSession,
    tier_name: str,
    parent_tier_id: int | None = None,
) -> Tier:
    """Create a new tier in the database."""
    tier = Tier(
        tier_name=tier_name,
        parent_tier_id=parent_tier_id,
    )
    return await DatabaseUtils.create_and_commit(db, tier)


async def get_tiers_by_elan_id(db: AsyncSession, elan_id: int) -> list[Tier]:
    """Get all tiers for a given ELAN file using tier_id association."""
    result = await db.execute(
        select(Tier)
        .join(ElanFileToTier, Tier.tier_id == ElanFileToTier.tier_id)
        .filter(ElanFileToTier.elan_id == elan_id)
    )
    return list(result.scalars().all())


async def check_tier_exists(db: AsyncSession, tier_id: int) -> bool:
    """Check if a tier exists by tier_id."""
    return await DatabaseUtils.exists(db, Tier, "tier_id", tier_id)


async def update_parent_tier(
    db: AsyncSession, tier_id: int, parent_tier_id: int
) -> None:
    """Update the parent_tier_id for a tier."""
    filters = {"tier_id": tier_id}
    update_fields = {"parent_tier_id": parent_tier_id}
    await DatabaseUtils.update_by_filter(db, Tier, filters, update_fields)


async def get_all_tier_names_with_annotations(db: AsyncSession) -> list[str]:
    """Get all unique tier names that have annotations."""
    result = await db.execute(select(Tier.tier_name).join(Annotation).distinct())
    return [row[0] for row in result]


async def get_tiers_with_annotations(db: AsyncSession) -> list[Tier]:
    """Get all tiers that have at least one annotation."""
    result = await db.execute(select(Tier).join(Annotation).distinct())
    return list(result.scalars().all())


async def get_tier_statistics(db: AsyncSession) -> list[tuple[str, int]]:
    """Get statistics about tiers across all files."""
    result = await db.execute(
        select(
            Tier.tier_name,
            func.count(Annotation.annotation_id).label("annotation_count"),
        )
        .join(Annotation)
        .group_by(Tier.tier_name)
        .order_by(func.count(Annotation.annotation_id).desc())
    )
    return [tuple(row) for row in result]


async def get_tiers_by_ids(db, tier_ids: list[int]) -> list[Tier]:
    """Get all tiers for a list of tier_ids."""
    if not tier_ids:
        return []
    return await DatabaseUtils.get_by_filter(db, Tier, {"tier_id": tier_ids})
