"""CRUD operations for Country model."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.country import Country
from app.utils.database import DatabaseUtils


async def get_country_by_code(db: AsyncSession, country_code: str) -> Country | None:
    """Get a country by its code."""
    countries = await DatabaseUtils.get_by_filter(
        db, Country, {"country_code": country_code}
    )
    return countries[0] if countries else None


async def create_country(db: AsyncSession, country: Country) -> Country:
    """Create a new country."""
    instance = await DatabaseUtils.create(db, country)
    await db.flush()
    await db.refresh(instance)
    return instance
