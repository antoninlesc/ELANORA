"""FileProperty CRUD operations using DatabaseUtils."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.model.file_property import FileProperty
from app.utils.database import DatabaseUtils

logger = get_logger()


async def get_properties_by_content_id(
    db: AsyncSession, content_id: int
) -> list[FileProperty]:
    """Get all properties for a specific file content."""
    filters = {"content_id": content_id}
    order_by = [FileProperty.property_name]
    return await DatabaseUtils.get_by_filter(
        db, FileProperty, filters, order_by=order_by
    )


async def get_properties_as_dict(db: AsyncSession, content_id: int) -> dict[str, str]:
    """Get properties as dictionary mapping property_name -> property_value."""
    properties = await get_properties_by_content_id(db, content_id)
    return {
        prop.property_name: prop.property_value
        for prop in properties
        if prop.property_value
    }


async def get_property_by_name_and_content(
    db: AsyncSession, property_name: str, content_id: int
) -> FileProperty | None:
    """Get a specific property by name and content."""
    filters = {"property_name": property_name, "content_id": content_id}
    return await DatabaseUtils.get_one_or_none(db, FileProperty, filters=filters)


async def create_property(
    db: AsyncSession,
    content_id: int,
    property_name: str,
    property_value: str | None = None,
) -> FileProperty:
    """Create a new file property."""
    file_property = FileProperty(
        content_id=content_id,
        property_name=property_name,
        property_value=property_value,
    )
    return await DatabaseUtils.create(db, file_property)


async def bulk_create_properties(db: AsyncSession, properties_data: list[dict]) -> None:
    """Bulk create properties for performance."""
    await DatabaseUtils.bulk_insert(
        db, FileProperty, properties_data, ignore_duplicates=True
    )


async def update_property_value(
    db: AsyncSession, property_id: int, new_value: str | None
) -> int:
    """Update a property value."""
    filters = {"property_id": property_id}
    update_fields = {"property_value": new_value}
    return await DatabaseUtils.update_by_filter(
        db, FileProperty, filters, update_fields
    )


async def upsert_property(
    db: AsyncSession,
    content_id: int,
    property_name: str,
    property_value: str | None = None,
) -> tuple[FileProperty, bool]:
    """Get or create property using upsert."""
    defaults = {"property_value": property_value}
    return await DatabaseUtils.upsert(
        db,
        FileProperty,
        defaults=defaults,
        content_id=content_id,
        property_name=property_name,
    )


async def delete_properties_by_content_id(db: AsyncSession, content_id: int) -> int:
    """Delete all properties for a specific content."""
    return await DatabaseUtils.delete_by_filter(db, FileProperty, content_id=content_id)


async def get_last_used_annotation_id(db: AsyncSession, content_id: int) -> str | None:
    """Get the lastUsedAnnotationId property value."""
    prop = await get_property_by_name_and_content(
        db, "lastUsedAnnotationId", content_id
    )
    return prop.property_value if prop else None


async def set_last_used_annotation_id(
    db: AsyncSession, content_id: int, annotation_id: str
) -> tuple[FileProperty, bool]:
    """Set or update the lastUsedAnnotationId property."""
    return await upsert_property(db, content_id, "lastUsedAnnotationId", annotation_id)


async def get_file_urn(db: AsyncSession, content_id: int) -> str | None:
    """Get the URN property value."""
    prop = await get_property_by_name_and_content(db, "URN", content_id)
    return prop.property_value if prop else None


async def set_file_urn(
    db: AsyncSession, content_id: int, urn: str
) -> tuple[FileProperty, bool]:
    """Set or update the URN property."""
    return await upsert_property(db, content_id, "URN", urn)
