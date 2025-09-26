"""CRUD operations for Country model."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.country import Country
from app.utils.database import DatabaseUtils


async def get_country_by_code(db: AsyncSession, country_code: str) -> Country | None:
    """Get a country by its code."""
    filters = {"country_code": country_code}
    return await DatabaseUtils.get_one_or_none(db, Country, filters=filters)


async def create_country(db: AsyncSession, country: Country) -> Country:
    """Create a new country."""
    instance = await DatabaseUtils.create(db, country)
    await db.flush()
    await db.refresh(instance)
    return instance
