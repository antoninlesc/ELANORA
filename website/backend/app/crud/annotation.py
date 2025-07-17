"""Annotation CRUD operations - Pure database access layer."""

from decimal import Decimal

from sqlalchemy import and_, delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.centralized_logging import get_logger
from app.core.centralized_logging import get_logger
from app.model.annotation import Annotation
from app.model.annotation_value import AnnotationValue
from app.utils.database import DatabaseUtils

logger = get_logger()


async def delete_unused_annotation_values(db: AsyncSession) -> int:
    """Delete annotation values not referenced by any annotation."""
    try:
        subquery = select(Annotation.value_id)
        count = await DatabaseUtils.bulk_delete(
            db, AnnotationValue, ~AnnotationValue.value_id.in_(subquery)
        )
        logger.info(f"Deleted {count} unused AnnotationValue rows")
        return count
    except Exception:
        await db.rollback()
        raise


async def get_annotation_by_id(
    db: AsyncSession, annotation_id: str, elan_id: int
) -> Annotation | None:
    """Retrieve an annotation by ID."""
    filters = {"annotation_id": annotation_id, "elan_id": elan_id}
    return await DatabaseUtils.get_one_by_filter(db, Annotation, filters)


async def get_annotations_by_tier(db: AsyncSession, tier_id: int) -> list[Annotation]:
    """Get all annotations for a specific tier."""
    filters = {"tier_id": tier_id}
    order_by = [Annotation.start_time]
    return await DatabaseUtils.get_by_filter(db, Annotation, filters, order_by=order_by)


async def get_annotations_with_value_by_tier(db: AsyncSession, tier_id: int):
    """Get all annotations with their values for a specific tier.

    Args:
        db: Database session.
        tier_id: The tier ID to filter by.

    Returns:
        List of annotations with their values for the tier, ordered by start time.

    """
    result = await db.execute(
        select(Annotation)
        .options(selectinload(Annotation.annotation_value))
        .filter(Annotation.tier_id == tier_id)
        .order_by(Annotation.start_time)
    )
    annotations = result.scalars().all()
    return annotations


async def get_annotations_by_time_range(
    db: AsyncSession, tier_id: int, start_time: Decimal, end_time: Decimal
) -> list[Annotation]:
    """Get annotations within a time range for a specific tier."""
    result = await db.execute(
        select(Annotation)
        .filter(
            and_(
                Annotation.tier_id == tier_id,
                Annotation.start_time >= start_time,
                Annotation.end_time <= end_time,
            )
        )
        .order_by(Annotation.start_time)
    )
    return list(result.scalars().all())


async def create_annotation_in_db(
    db: AsyncSession,
    annotation_id: str,
    elan_id: int,
    value_id: int,
    start_time: Decimal,
    end_time: Decimal,
    tier_id: int,
) -> Annotation:
    """Create a new annotation in the database."""
    annotation = Annotation(
        annotation_id=annotation_id,
        elan_id=elan_id,
        value_id=value_id,
        start_time=start_time,
        end_time=end_time,
        tier_id=tier_id,
    )
    return await DatabaseUtils.create_and_commit(db, annotation)


async def check_annotation_exists(
    db: AsyncSession, annotation_id: str, elan_id: int
) -> bool:
    filters = {"annotation_id": annotation_id, "elan_id": elan_id}
    return await DatabaseUtils.exists(
        db, Annotation, "annotation_id", annotation_id
    ) and await DatabaseUtils.exists(db, Annotation, "elan_id", elan_id)


async def delete_annotations_by_tier(db: AsyncSession, tier_id: int) -> int:
    """Delete all annotations for a tier."""
    try:
        count = await DatabaseUtils.bulk_delete(
            db, Annotation, Annotation.tier_id == tier_id
        )
        await delete_unused_annotation_values(db)
        return count
    except Exception:
        await db.rollback()
        raise


async def bulk_create_annotations(
    db: AsyncSession, tiers_data: list[dict], elan_id: int, value_map: dict[str, int]
) -> None:
    """Bulk create annotations for multiple tiers."""
    all_annotations = []
    for tier_data in tiers_data:
        tier_id = tier_data["tier_id"]
        for ann in tier_data["annotations"]:
            all_annotations.append(
                {
                    "annotation_id": ann["annotation_id"],
                    "elan_id": elan_id,
                    "value_id": value_map[ann["annotation_value"]],
                    "start_time": ann["start_time"],
                    "end_time": ann["end_time"],
                    "tier_id": tier_id,
                }
            )
    if all_annotations:
        await DatabaseUtils.bulk_insert(db, Annotation, all_annotations)
