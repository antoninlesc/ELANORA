"""Annotation CRUD operations - Pure database access layer."""

from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.centralized_logging import get_logger
from app.model.annotation import Annotation
from app.model.annotation_value import AnnotationValue
from app.utils.database import DatabaseUtils

logger = get_logger()


async def delete_unused_annotation_values(db: AsyncSession) -> int:
    """Delete annotation values not referenced by any annotation."""
    try:
        from sqlalchemy import and_

        subquery = select(Annotation.value_id)
        conditions = [~AnnotationValue.value_id.in_(subquery)]
        count = await DatabaseUtils.delete_by_conditions(
            db, AnnotationValue, conditions=conditions
        )
        logger.info(f"Deleted {count} unused AnnotationValue rows")
        return count
    except Exception:
        await db.rollback()
        raise


async def get_annotation_by_id(
    db: AsyncSession, annotation_id: str, content_id: int
) -> Annotation | None:
    """Retrieve an annotation by ID."""
    filters = {"annotation_id": annotation_id, "content_id": content_id}
    results = await DatabaseUtils.get_by_filter(db, Annotation, filters, limit=1)
    return results[0] if results else None


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
    conditions = [Annotation.tier_id == tier_id]
    order_by = [Annotation.start_time]
    options = [selectinload(Annotation.annotation_value)]

    return await DatabaseUtils.get_by_conditions(
        db, Annotation, conditions=conditions, order_by=order_by, options=options
    )


async def get_annotations_by_time_range(
    db: AsyncSession, tier_id: int, start_time: Decimal, end_time: Decimal
) -> list[Annotation]:
    """Get annotations within a time range for a specific tier."""
    from sqlalchemy import and_

    conditions = [
        Annotation.tier_id == tier_id,
        Annotation.start_time >= start_time,
        Annotation.end_time <= end_time,
    ]
    order_by = [Annotation.start_time]

    return await DatabaseUtils.get_by_conditions(
        db, Annotation, conditions=conditions, order_by=order_by
    )


async def get_annotations_by_tier_and_content(
    db: AsyncSession, tier_id: int, content_id: int
) -> list[Annotation]:
    """Get all annotations for a specific tier and content."""
    from sqlalchemy import and_

    conditions = [
        and_(Annotation.tier_id == tier_id, Annotation.content_id == content_id)
    ]
    order_by = [Annotation.start_time]
    options = [selectinload(Annotation.annotation_value)]

    return await DatabaseUtils.get_by_conditions(
        db, Annotation, conditions=conditions, order_by=order_by, options=options
    )


async def create_annotation_in_db(
    db: AsyncSession,
    annotation_id: str,
    content_id: int,
    value_id: int,
    start_time: Decimal,
    end_time: Decimal,
    tier_id: int,
) -> Annotation:
    """Create a new annotation in the database."""
    annotation = Annotation(
        annotation_id=annotation_id,
        content_id=content_id,
        value_id=value_id,
        start_time=start_time,
        end_time=end_time,
        tier_id=tier_id,
    )
    return await DatabaseUtils.create(db, annotation)


async def check_annotation_exists(
    db: AsyncSession, annotation_id: str, content_id: int
) -> bool:
    filters = {"annotation_id": annotation_id, "content_id": content_id}
    return await DatabaseUtils.exists(
        db, Annotation, "annotation_id", annotation_id
    ) and await DatabaseUtils.exists(db, Annotation, "content_id", content_id)


async def delete_annotations_by_tier(db: AsyncSession, tier_id: int) -> int:
    """Delete all annotations for a tier."""
    try:
        from sqlalchemy import and_

        conditions = [Annotation.tier_id == tier_id]
        count = await DatabaseUtils.delete_by_conditions(
            db, Annotation, conditions=conditions
        )
        await delete_unused_annotation_values(db)
        return count
    except Exception:
        await db.rollback()
        raise


async def bulk_create_annotations(
    db: AsyncSession, tiers_data: list[dict], content_id: int, value_map: dict[str, int]
) -> None:
    """Bulk create annotations for multiple tiers, checking for existing annotations first."""
    # Check if annotations already exist for this content_id
    existing_count = await DatabaseUtils.get_by_filter(
        db, Annotation, {"content_id": content_id}, limit=1
    )

    if existing_count:
        logger.info(
            f"Annotations already exist for content_id {content_id}, skipping bulk insert"
        )
        return

    all_annotations = []
    for tier_data in tiers_data:
        tier_id = tier_data["tier_id"]
        for ann in tier_data["annotations"]:
            all_annotations.append(
                {
                    "annotation_id": ann["annotation_id"],
                    "content_id": content_id,
                    "value_id": value_map[ann["annotation_value"]],
                    "start_time": ann["start_time"],
                    "end_time": ann["end_time"],
                    "tier_id": tier_id,
                }
            )
    if all_annotations:
        await DatabaseUtils.bulk_insert(db, Annotation, all_annotations)


async def delete_annotations_by_file(db: AsyncSession, content_id: int) -> int:
    """Delete all annotations for a given content."""
    try:
        from sqlalchemy import and_

        conditions = [Annotation.content_id == content_id]
        count = await DatabaseUtils.delete_by_conditions(
            db, Annotation, conditions=conditions
        )
        await delete_unused_annotation_values(db)
        await db.flush()
        return count
    except Exception as e:
        logger.exception("Failed to delete annotations by file", exc_info=e)
        return 0
