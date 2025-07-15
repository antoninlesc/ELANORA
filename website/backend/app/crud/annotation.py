"""Annotation CRUD operations - Pure database access layer."""

from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, delete, select
from sqlalchemy.orm import selectinload


from app.model.annotation import Annotation
from app.model.annotation_value import AnnotationValue
from app.core.centralized_logging import get_logger

logger = get_logger()


async def delete_unused_annotation_values(db: AsyncSession) -> int:
    """Delete annotation values not referenced by any annotation."""
    try:
        subq = select(Annotation.value_id).distinct()
        stmt = delete(AnnotationValue).where(~AnnotationValue.value_id.in_(subq))
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount if hasattr(result, "rowcount") else -1
    except Exception:
        await db.rollback()
        raise


async def get_annotation_by_id(
    db: AsyncSession, annotation_id: str, elan_id: int
) -> Optional[Annotation]:
    """Retrieve an annotation by ID.

    Args:
        db: Database session.
        annotation_id: The annotation ID to retrieve.

    Returns:
        The annotation object if found, otherwise None.

    """
    result = await db.execute(
        select(Annotation).filter(
            Annotation.annotation_id == annotation_id, Annotation.elan_id == elan_id
        )
    )
    return result.scalar_one_or_none()


async def get_annotations_by_tier(db: AsyncSession, tier_id: str) -> list[Annotation]:
    """Get all annotations for a specific tier.

    Args:
        db: Database session.
        tier_id: The tier ID to filter by.

    Returns:
        List of annotations for the tier, ordered by start time.

    """
    result = await db.execute(
        select(Annotation)
        .filter(Annotation.tier_id == tier_id)
        .order_by(Annotation.start_time)
    )
    return list(result.scalars().all())


async def get_annotations_with_value_by_tier(db: AsyncSession, tier_id: str):
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
    db: AsyncSession, tier_id: str, start_time: Decimal, end_time: Decimal
) -> list[Annotation]:
    """Get annotations within a time range for a specific tier.

    Args:
        db: Database session.
        tier_id: The tier ID to filter by.
        start_time: Start of time range.
        end_time: End of time range.

    Returns:
        List of annotations within the time range.

    """
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
    tier_id: str,
) -> Annotation:
    """Create a new annotation in the database.

    Args:
        db: Database session.
        annotation_id: Unique identifier for the annotation.
        value_id: The ID of the annotation value (foreign key).
        start_time: Start time of the annotation.
        end_time: End time of the annotation.
        tier_id: ID of the tier this annotation belongs to.

    Returns:
        The created annotation object.

    Raises:
        Exception: If annotation creation fails.

    """
    annotation = Annotation(
        annotation_id=annotation_id,
        elan_id=elan_id,
        value_id=value_id,
        start_time=start_time,
        end_time=end_time,
        tier_id=tier_id,
    )

    try:
        db.add(annotation)
        await db.commit()
        await db.refresh(annotation)
        return annotation
    except Exception:
        await db.rollback()
        raise


async def check_annotation_exists(
    db: AsyncSession, annotation_id: str, elan_id: int
) -> bool:
    result = await db.execute(
        select(Annotation.annotation_id).filter(
            Annotation.annotation_id == annotation_id, Annotation.elan_id == elan_id
        )
    )
    return result.scalar_one_or_none() is not None


async def delete_annotations_by_tier(db: AsyncSession, tier_id: str) -> int:
    """Delete all annotations for a tier.

    Args:
        db: Database session.
        tier_id: ID of the tier whose annotations to delete.

    Returns:
        Number of annotations deleted.

    """
    try:
        result = await db.execute(
            select(Annotation).filter(Annotation.tier_id == tier_id)
        )
        annotations = list(result.scalars().all())
        count = len(annotations)

        for annotation in annotations:
            await db.delete(annotation)

        await db.commit()
        await delete_unused_annotation_values(db)
        return count
    except Exception:
        await db.rollback()
        raise


async def bulk_create_annotations(
    db: AsyncSession, tiers_data: list[dict], elan_id: int, value_map: dict[str, int]
) -> None:
    from app.model.annotation import Annotation

    all_annotations = []
    for tier_data in tiers_data:
        tier_id = tier_data["tier_id"]
        for ann in tier_data["annotations"]:
            all_annotations.append(
                Annotation(
                    annotation_id=ann["annotation_id"],
                    elan_id=elan_id,
                    value_id=value_map[ann["annotation_value"]],
                    start_time=ann["start_time"],
                    end_time=ann["end_time"],
                    tier_id=tier_id,
                )
            )
    if all_annotations:
        db.add_all(all_annotations)
        await db.flush()
