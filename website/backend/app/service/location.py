"""Service for location-related operations."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.model.country import Country
from app.model.city import City
from app.schema.responses.location import CountryResponse, CityResponse


class LocationService:
    """Service class for location operations."""

    @classmethod
    async def get_all_countries(cls, db: AsyncSession) -> List[CountryResponse]:
        """Retrieve all countries from the database."""
        result = await db.execute(select(Country))
        countries = result.scalars().all()
        return [CountryResponse.model_validate(country) for country in countries]

    @classmethod
    async def get_cities_by_country(
        cls, db: AsyncSession, country_id: int
    ) -> List[CityResponse]:
        """Retrieve all cities for a specific country."""
        result = await db.execute(
            select(City)
            .options(selectinload(City.country))
            .where(City.country_id == country_id)
        )
        cities = result.scalars().all()
        return [CityResponse.model_validate(city) for city in cities]

    @classmethod
    async def get_all_cities(cls, db: AsyncSession) -> List[CityResponse]:
        """Retrieve all cities with their country information."""
        result = await db.execute(select(City).options(selectinload(City.country)))
        cities = result.scalars().all()
        return [CityResponse.model_validate(city) for city in cities]
