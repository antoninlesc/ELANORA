"""Service for address-related operations."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func

from app.model.address import Address
from app.model.city import City
from app.schema.requests.user import AddressRequest


class AddressService:
    """Service class for address operations."""

    @classmethod
    async def create_address(
        cls,
        db: AsyncSession,
        address_data: AddressRequest,
    ) -> Address:
        """Create a new address. If city_name is provided, create or get the city, then use its id."""

        # Find or create city by normalized name and country (case-insensitive, strip)
        normalized_city_name = address_data.city_name.strip().lower()
        stmt = select(City).where(
            (City.country_id == address_data.country_id)
            & (func.lower(func.trim(City.city_name)) == normalized_city_name)
        )
        result = await db.execute(stmt)
        city = result.scalar_one_or_none()
        if not city:
            city = City(
                city_name=address_data.city_name.strip(),
                country_id=address_data.country_id,
            )
            db.add(city)
            await db.flush()
            await db.refresh(city)

        address = Address(
            street_number=address_data.street_number,
            street_name=address_data.street_name,
            city_id=city.city_id,
            postal_code=address_data.postal_code,
            address_line_2=address_data.address_line_2,
        )

        db.add(address)
        await db.flush()  # Flush to get the address_id
        await db.refresh(address)

        return address

    @classmethod
    async def get_address_by_id(
        cls,
        db: AsyncSession,
        address_id: int,
    ) -> Optional[Address]:
        """Get an address by its ID.

        Args:
            db (AsyncSession): Database session.
            address_id (int): Address ID.

        Returns:
            Optional[Address]: The address object if found, None otherwise.
        """
        result = await db.execute(
            select(Address).where(Address.address_id == address_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def update_address(
        cls,
        db: AsyncSession,
        address: Address,
        address_data: AddressRequest,
    ) -> Address:
        """Update an existing address.

        Args:
            db (AsyncSession): Database session.
            address (Address): Existing address object.
            address_data (AddressRequest): Updated address data.

        Returns:
            Address: The updated address object.
        """

        # Find or create city by name and country
        stmt = select(City).where(
            City.city_name == address_data.city_name.strip(),
            City.country_id == address_data.country_id,
        )
        result = await db.execute(stmt)
        city = result.scalar_one_or_none()
        if not city:
            city = City(
                city_name=address_data.city_name.strip(),
                country_id=address_data.country_id,
            )
            db.add(city)
            await db.flush()
            await db.refresh(city)

        address.street_number = address_data.street_number
        address.street_name = address_data.street_name
        address.city_id = city.city_id
        address.postal_code = address_data.postal_code
        address.address_line_2 = address_data.address_line_2

        await db.flush()
        await db.refresh(address)

        return address
