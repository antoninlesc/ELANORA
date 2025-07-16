from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.annotation_value import AnnotationValue

logger = get_logger()


async def get_or_create_annotation_value(db: AsyncSession, value: str) -> int:
    result = await db.execute(
        select(AnnotationValue).where(AnnotationValue.annotation_value == value)
    )
    annotation_value = result.scalars().first()
    if annotation_value:
        return annotation_value.value_id
    annotation_value = AnnotationValue(annotation_value=value)
    db.add(annotation_value)
    await db.flush()
    return annotation_value.value_id


async def get_annotation_value_by_id(db: AsyncSession, value_id: int) -> str | None:
    result = await db.execute(
        select(AnnotationValue).where(AnnotationValue.value_id == value_id)
    )
    annotation_value = result.scalars().first()
    return annotation_value.annotation_value if annotation_value else None


async def bulk_get_or_create_annotation_values(
    db: AsyncSession, tiers_data: list[dict]
) -> dict[str, int]:
    all_ann_values = set(
        ann["annotation_value"]
        for tier_data in tiers_data
        for ann in tier_data["annotations"]
    )
    value_map = {}
    logger.info(
        f"[bulk_get_or_create_annotation_values] Start. Total unique values: {len(all_ann_values)}"
    )
    if all_ann_values:
        # Fetch existing values
        result = await db.execute(
            select(AnnotationValue).where(
                AnnotationValue.annotation_value.in_(all_ann_values)
            )
        )
        for obj in result.scalars():
            value_map[obj.annotation_value] = obj.value_id
        missing_values = [v for v in all_ann_values if v not in value_map]
        logger.info(
            f"[bulk_get_or_create_annotation_values] Existing values in DB: {len(value_map)}. Missing: {len(missing_values)}"
        )
        if missing_values:
            # Use MySQL ON DUPLICATE KEY UPDATE for idempotent insert
            stmt = mysql_insert(AnnotationValue).values(
                [{"annotation_value": v} for v in missing_values]
            )
            # Do nothing if duplicate (no-op update)
            stmt = stmt.on_duplicate_key_update(
                annotation_value=stmt.inserted.annotation_value
            )
            await db.execute(stmt)
            await db.commit()
            logger.info(
                f"[bulk_get_or_create_annotation_values] Inserted or ignored {len(missing_values)} values."
            )
            # Re-fetch to get IDs
            result = await db.execute(
                select(AnnotationValue).where(
                    AnnotationValue.annotation_value.in_(missing_values)
                )
            )
            for obj in result.scalars():
                value_map[obj.annotation_value] = obj.value_id
    logger.info(
        f"[bulk_get_or_create_annotation_values] Completed. Returning value_map with {len(value_map)} entries."
    )
    return value_map
