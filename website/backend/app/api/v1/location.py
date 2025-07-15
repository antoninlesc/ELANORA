"""
API endpoints for location data (countries and cities).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.dependency.database import get_db_dep
from app.schema.responses.location import CountryResponse, CityResponse
from app.service.location import LocationService

router = APIRouter(tags=["Location"])


@router.get("/countries", response_model=List[CountryResponse])
async def get_countries(db: AsyncSession = get_db_dep) -> List[CountryResponse]:
    """Get all available countries."""
    return await LocationService.get_all_countries(db)


@router.get("/cities", response_model=List[CityResponse])
async def get_cities_by_country(
    country_id: int, db: AsyncSession = get_db_dep
) -> List[CityResponse]:
    """Get all cities for a specific country."""
    return await LocationService.get_cities_by_country(db, country_id)


@router.get("/cities/all", response_model=List[CityResponse])
async def get_all_cities(db: AsyncSession = get_db_dep) -> List[CityResponse]:
    """Get all cities with country information."""
    return await LocationService.get_all_cities(db)
