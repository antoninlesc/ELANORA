from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import asyncio
from app.model.annotation_value import AnnotationValue
from app.core.centralized_logging import get_logger

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
    import time

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
            new_values = [AnnotationValue(annotation_value=v) for v in missing_values]
            max_retries = 5
            retry_delay = 0.2
            for attempt in range(1, max_retries + 1):
                try:
                    db.add_all(new_values)
                    await db.commit()
                    db.expire_all()
                    logger.info(
                        f"[bulk_get_or_create_annotation_values] Inserted {len(new_values)} new values on attempt {attempt}."
                    )
                    break
                except IntegrityError as e:
                    logger.warning(
                        f"[bulk_get_or_create_annotation_values] IntegrityError during bulk insert (attempt {attempt}): {e}. Rolling back and retrying fetch."
                    )
                    await db.rollback()
                    # Sleep to avoid race conditions
                    time.sleep(retry_delay)
                except Exception as e:
                    logger.error(
                        f"[bulk_get_or_create_annotation_values] Unexpected error during bulk insert (attempt {attempt}): {e}"
                    )
                    await db.rollback()
                    time.sleep(retry_delay)
            # Always re-fetch after insert attempts
            result = await db.execute(
                select(AnnotationValue).where(
                    AnnotationValue.annotation_value.in_(missing_values)
                )
            )
            for obj in result.scalars():
                value_map[obj.annotation_value] = obj.value_id
            still_missing = [v for v in missing_values if v not in value_map]
            logger.info(
                f"[bulk_get_or_create_annotation_values] After bulk insert, still missing: {still_missing}"
            )
            # Try single inserts for any still missing
            for v in still_missing:
                for attempt in range(1, max_retries + 1):
                    try:
                        db.add(AnnotationValue(annotation_value=v))
                        await db.commit()
                        db.expire_all()
                        logger.info(
                            f"[bulk_get_or_create_annotation_values] Inserted missing value '{v}' on attempt {attempt}."
                        )
                        break
                    except IntegrityError as e:
                        logger.info(
                            f"[bulk_get_or_create_annotation_values] IntegrityError on single insert for '{v}' (attempt {attempt}): {e}. Likely duplicate, will re-query."
                        )
                        await db.rollback()
                        time.sleep(retry_delay)
                    except Exception as e:
                        logger.error(
                            f"[bulk_get_or_create_annotation_values] Unexpected error on single insert for '{v}' (attempt {attempt}): {e}"
                        )
                        await db.rollback()
                        time.sleep(retry_delay)
                # Always re-fetch after insert attempts
                result = await db.execute(
                    select(AnnotationValue).where(AnnotationValue.annotation_value == v)
                )
                obj = result.scalars().first()
                if obj:
                    value_map[obj.annotation_value] = obj.value_id
            # Final check
            final_missing = [v for v in still_missing if v not in value_map]
            if final_missing:
                # Log DB state for debugging
                logger.error(
                    f"[bulk_get_or_create_annotation_values] Failed to insert or fetch annotation values after all attempts: {final_missing}"
                )
                db_values = await db.execute(select(AnnotationValue.annotation_value))
                logger.error(
                    f"[bulk_get_or_create_annotation_values] Current annotation values in DB: {[row[0] for row in db_values]}"
                )
                # Log session/transaction state
                logger.error(
                    f"[bulk_get_or_create_annotation_values] Session info: dirty={db.dirty}, new={db.new}, in_transaction={db.in_transaction()}"
                )
                raise RuntimeError(
                    f"Could not insert or fetch annotation values: {final_missing}"
                )
    logger.info(
        f"[bulk_get_or_create_annotation_values] Completed. Returning value_map with {len(value_map)} entries."
    )
    return value_map
