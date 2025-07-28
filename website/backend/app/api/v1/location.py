"""API endpoints for location data (countries and cities)."""

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db_dep
from app.schema.responses.location import CityResponse, CountryResponse
from app.service.location import LocationService

router = APIRouter()


@router.get("/countries", response_model=list[CountryResponse])
async def get_countries(db: AsyncSession = get_db_dep) -> list[CountryResponse]:
    """Get all available countries."""
    return await LocationService.get_all_countries(db)


@router.get("/cities", response_model=list[CityResponse])
async def get_cities_by_country(
    country_id: int, db: AsyncSession = get_db_dep
) -> list[CityResponse]:
    """Get all cities for a specific country."""
    return await LocationService.get_cities_by_country(db, country_id)


@router.get("/cities/all", response_model=list[CityResponse])
async def get_all_cities(db: AsyncSession = get_db_dep) -> list[CityResponse]:
    """Get all cities with country information."""
    return await LocationService.get_all_cities(db)
