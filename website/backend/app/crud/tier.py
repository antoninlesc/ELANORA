"""Tier CRUD operations - Pure database access layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.annotation import Annotation
from app.model.elan_file_to_tier import ElanFileToTier
from app.model.tier import Tier
from app.utils.database import DatabaseUtils

logger = get_logger()


async def delete_tiers_for_elan_file(db: AsyncSession, elan_id: int):
    logger.info(f"Bulk deleting tiers and annotations for elan_id={elan_id}")
    try:
        # Get content_id from elan_id
        from app.crud.elan_file import get_elan_file_by_id

        elan_file = await get_elan_file_by_id(db, elan_id)
        if not elan_file:
            return

        tier_ids = [
            row[0]
            for row in await db.execute(
                select(ElanFileToTier.tier_id).where(
                    ElanFileToTier.content_id == elan_file.content_id
                )
            )
        ]
        logger.info(f"tier_ids to delete for elan_id={elan_id}: {tier_ids}")
        if tier_ids:
            from sqlalchemy import and_

            conditions = [Annotation.tier_id.in_(tier_ids)]
            await DatabaseUtils.delete_by_conditions(
                db, Annotation, conditions=conditions
            )
            conditions = [
                (ElanFileToTier.content_id == elan_file.content_id)
                & ElanFileToTier.tier_id.in_(tier_ids)
            ]
            await DatabaseUtils.delete_by_conditions(
                db, ElanFileToTier, conditions=conditions
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
                conditions = [Tier.tier_id.in_(orphaned_tiers)]
                await DatabaseUtils.delete_by_conditions(
                    db, Tier, conditions=conditions
                )
        logger.info(f"Bulk deleted tiers and annotations for elan_id={elan_id}")
    except Exception as e:
        logger.error(f"Failed to bulk delete tiers for elan_id={elan_id}: {e}")


async def get_tier_by_id(db: AsyncSession, tier_id: int) -> Tier | None:
    """Retrieve a tier by ID."""
    return await DatabaseUtils.get_by_id(db, Tier, "tier_id", tier_id)


async def get_all_tiers(db: AsyncSession, include_staged: bool = False) -> list[Tier]:
    """Get all tiers."""
    filters = {}
    if not include_staged:
        filters["is_staged"] = False
    return await DatabaseUtils.get_by_filter(db, Tier, filters)


async def get_child_tiers(
    db: AsyncSession, parent_tier_id: int, include_staged: bool = False
) -> list[Tier]:
    """Get all child tiers of a parent tier."""
    filters = {"parent_tier_id": parent_tier_id}
    if not include_staged:
        filters["is_staged"] = False
    return await DatabaseUtils.get_by_filter(db, Tier, filters)


async def get_root_tiers(db: AsyncSession, include_staged: bool = False) -> list[Tier]:
    """Get all root tiers (no parent)."""
    conditions = [Tier.parent_tier_id.is_(None)]
    if not include_staged:
        conditions.append(Tier.is_staged.is_(False))
    return await DatabaseUtils.get_by_conditions(db, Tier, conditions=conditions)


async def get_tier_id_by_name(
    db: AsyncSession, tier_name: str, include_staged: bool = False
) -> int | None:
    conditions = [Tier.tier_name == tier_name]
    if not include_staged:
        conditions.append(Tier.is_staged.is_(False))
    results = await DatabaseUtils.get_by_conditions(
        db, Tier, conditions=conditions, limit=1
    )
    return results[0].tier_id if results else None


async def get_tier_by_name(
    db: AsyncSession, tier_name: str, include_staged: bool = False
) -> Tier | None:
    conditions = [Tier.tier_name == tier_name]
    if not include_staged:
        conditions.append(Tier.is_staged.is_(False))
    results = await DatabaseUtils.get_by_conditions(
        db, Tier, conditions=conditions, limit=1
    )
    return results[0] if results else None


async def create_tier_in_db(
    db: AsyncSession,
    tier_name: str,
    parent_tier_id: int | None = None,
    is_staged: bool = False,
    session_id: str | None = None,
) -> Tier:
    """Create a new tier in the database."""
    tier = Tier(
        tier_name=tier_name,
        parent_tier_id=parent_tier_id,
        is_staged=is_staged,
        session_id=session_id,
    )
    await DatabaseUtils.create(db, tier)
    await db.flush()
    return tier


async def get_tiers_by_elan_id(
    db: AsyncSession, elan_id: int, include_staged: bool = False
) -> list[Tier]:
    """Get all tiers for a given ELAN file using tier_id association."""
    # Get content_id from elan_id using DatabaseUtils
    from app.crud.elan_file import get_elan_file_by_id

    elan_file = await get_elan_file_by_id(db, elan_id)
    if not elan_file:
        return []

    # Use DatabaseUtils with subquery approach for now
    in_filters = {"tier_id": []}
    # Get tier_ids associated with this content_id
    assoc_filters = {"content_id": elan_file.content_id}
    associations = await DatabaseUtils.get_by_filter(db, ElanFileToTier, assoc_filters)
    tier_ids = [assoc.tier_id for assoc in associations]

    if not tier_ids:
        return []

    conditions = [Tier.tier_id.in_(tier_ids)]
    if not include_staged:
        conditions.append(Tier.is_staged.is_(False))
    return await DatabaseUtils.get_by_conditions(db, Tier, conditions=conditions)


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
    await db.flush()


async def get_all_tier_names_with_annotations(db: AsyncSession) -> list[str]:
    """Get all unique tier names that have annotations."""
    # Use distinct query to get tier names that have annotations
    from app.model.annotation import Annotation
    from sqlalchemy import distinct, select

    query = (
        select(distinct(Tier.tier_name))
        .select_from(Tier)
        .join(Annotation, Tier.tier_id == Annotation.tier_id)
    )
    result = await db.execute(query)
    tier_names = [row[0] for row in result.all() if row[0] is not None]
    return [str(name) for name in tier_names]


async def get_tiers_with_annotations_for_content(
    db: AsyncSession, content_id: int, include_staged: bool = False
) -> list[Tier]:
    """Get all tiers that have at least one annotation for a specific content."""
    # Use DatabaseUtils with join to get distinct tiers
    from app.model.annotation import Annotation
    from sqlalchemy import distinct

    # Get distinct tier_ids that have annotations for this content
    subquery = select(distinct(Annotation.tier_id)).where(
        Annotation.content_id == content_id
    )
    conditions = [Tier.tier_id.in_(subquery)]
    if not include_staged:
        conditions.append(Tier.is_staged.is_(False))

    return await DatabaseUtils.get_by_conditions(db, Tier, conditions=conditions)


async def get_tier_statistics(db: AsyncSession) -> list[tuple[str, int]]:
    """Get statistics about tiers across all files."""
    # Use DatabaseUtils aggregate query support
    from sqlalchemy import func
    from app.model.annotation import Annotation

    aggregates = {
        "tier_name": Tier.tier_name,
        "annotation_count": func.count(Annotation.annotation_id),
    }
    group_by = [Tier.tier_name]

    # Join with annotations
    relationships = [("annotations", None)]

    result = await DatabaseUtils.get_aggregated_data(
        db, Tier, aggregates, group_by=group_by
    )

    # Sort by annotation count descending
    result.sort(key=lambda x: x["annotation_count"], reverse=True)
    return [(row["tier_name"], row["annotation_count"]) for row in result]


async def get_tiers_by_ids(
    db, tier_ids: list[int], include_staged: bool = False
) -> list[Tier]:
    """Get all tiers for a list of tier_ids."""
    if not tier_ids:
        return []
    conditions = [Tier.tier_id.in_(tier_ids)]
    if not include_staged:
        conditions.append(Tier.is_staged.is_(False))
    return await DatabaseUtils.get_by_conditions(db, Tier, conditions=conditions)


async def delete_tiers_for_session(db: AsyncSession, session_id: str) -> int:
    """Delete all staged tiers for a given session_id."""
    return await DatabaseUtils.delete_by_filter(
        db, Tier, session_id=session_id, is_staged=True
    )
