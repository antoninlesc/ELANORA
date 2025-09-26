"""CRUD operations for City model."""

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.city import City
from app.utils.database import DatabaseUtils


async def get_city_by_name_and_country(
    db: AsyncSession, city_name: str, country_id: int
) -> City | None:
    """Get a city by normalized name and country ID."""
    normalized_city_name = city_name.strip().lower()
    conditions = [
        City.country_id == country_id,
        func.lower(func.trim(City.city_name)) == normalized_city_name,
    ]
    cities = await DatabaseUtils.get_by_conditions(db, City, conditions, limit=1)
    return cities[0] if cities else None


async def create_city(db: AsyncSession, city: City) -> City:
    """Create a new city."""
    instance = await DatabaseUtils.create(db, city)
    await db.flush()
    await db.refresh(instance)
    return instance
