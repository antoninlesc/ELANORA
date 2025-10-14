"""LinguisticType CRUD operations using DatabaseUtils."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.linguistic_type import LinguisticType
from app.utils.database import DatabaseUtils

logger = get_logger()


async def get_linguistic_types_by_content_id(
    db: AsyncSession, content_id: int
) -> list[LinguisticType]:
    """Get all linguistic types for a specific file content."""
    filters = {"content_id": content_id}
    order_by = [LinguisticType.linguistic_type_id]
    return await DatabaseUtils.get_by_filter(
        db, LinguisticType, filters, order_by=order_by
    )


async def get_linguistic_type_by_id_and_content(
    db: AsyncSession, linguistic_type_id: str, content_id: int
) -> LinguisticType | None:
    """Get a specific linguistic type by ID and content."""
    filters = {"linguistic_type_id": linguistic_type_id, "content_id": content_id}
    return await DatabaseUtils.get_one_or_none(db, LinguisticType, filters=filters)


async def create_linguistic_type(
    db: AsyncSession,
    linguistic_type_id: str,
    content_id: int,
    time_alignable: bool = True,
    constraints: str | None = None,
    controlled_vocabulary_ref: str | None = None,
    graphic_references: bool = False,
) -> LinguisticType:
    """Create a new linguistic type."""
    linguistic_type = LinguisticType(
        linguistic_type_id=linguistic_type_id,
        content_id=content_id,
        time_alignable=time_alignable,
        constraints=constraints,
        controlled_vocabulary_ref=controlled_vocabulary_ref,
        graphic_references=graphic_references,
    )
    return await DatabaseUtils.create(db, linguistic_type)


async def bulk_create_linguistic_types(
    db: AsyncSession, linguistic_types_data: list[dict]
) -> None:
    """Bulk create linguistic types for performance."""
    await DatabaseUtils.bulk_insert(
        db, LinguisticType, linguistic_types_data, ignore_duplicates=True
    )


async def delete_linguistic_types_by_content_id(
    db: AsyncSession, content_id: int
) -> int:
    """Delete all linguistic types for a specific content."""
    return await DatabaseUtils.delete_by_filter(
        db, LinguisticType, content_id=content_id
    )


async def upsert_linguistic_type(
    db: AsyncSession,
    linguistic_type_id: str,
    content_id: int,
    time_alignable: bool = True,
    constraints: str | None = None,
    controlled_vocabulary_ref: str | None = None,
    graphic_references: bool = False,
) -> tuple[LinguisticType, bool]:
    """Get or create linguistic type using upsert."""
    defaults = {
        "time_alignable": time_alignable,
        "constraints": constraints,
        "controlled_vocabulary_ref": controlled_vocabulary_ref,
        "graphic_references": graphic_references,
    }
    return await DatabaseUtils.upsert(
        db,
        LinguisticType,
        defaults=defaults,
        linguistic_type_id=linguistic_type_id,
        content_id=content_id,
    )


async def check_linguistic_type_exists(
    db: AsyncSession, linguistic_type_id: str, content_id: int
) -> bool:
    """Check if linguistic type exists for specific content."""
    filters = {"linguistic_type_id": linguistic_type_id, "content_id": content_id}
    result = await DatabaseUtils.get_one_or_none(db, LinguisticType, filters=filters)
    return result is not None
