"""Service for address-related operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import address as crud_address
from app.crud import city as crud_city
from app.crud import country as crud_country
from app.model.address import Address
from app.model.city import City
from app.model.country import Country
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
        try:
            # Get or create country
            country = await crud_country.get_country_by_code(
                db, address_data.country_code
            )
            if not country:
                country = Country(
                    country_code=address_data.country_code,
                    country_name=address_data.country_name,
                )
                country = await crud_country.create_country(db, country)

            # Get or create city
            city = await crud_city.get_city_by_name_and_country(
                db, address_data.city_name, country.country_id
            )
            if not city:
                city = City(
                    city_name=address_data.city_name.strip(),
                    country_id=country.country_id,
                )
                city = await crud_city.create_city(db, city)

            # Create address
            address = Address(
                street_number=address_data.street_number,
                street_name=address_data.street_name,
                city_id=city.city_id,
                postal_code=address_data.postal_code,
                address_line_2=address_data.address_line_2,
            )
            address = await crud_address.create_address(db, address)

            await db.commit()
            return address
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def get_address_by_id(
        cls,
        db: AsyncSession,
        address_id: int,
    ) -> Address | None:
        """Get an address by its ID."""
        return await crud_address.get_address_by_id(db, address_id)

    @classmethod
    async def update_address(
        cls,
        db: AsyncSession,
        address: Address,
        address_data: AddressRequest,
    ) -> Address:
        """Update an existing address."""
        try:
            # Get or create country
            country = await crud_country.get_country_by_code(
                db, address_data.country_code
            )
            if not country:
                country = Country(
                    country_code=address_data.country_code,
                    country_name=address_data.country_name,
                )
                country = await crud_country.create_country(db, country)

            # Get or create city
            city = await crud_city.get_city_by_name_and_country(
                db, address_data.city_name, country.country_id
            )
            if not city:
                city = City(
                    city_name=address_data.city_name.strip(),
                    country_id=country.country_id,
                )
                city = await crud_city.create_city(db, city)

            # Update address fields
            address.street_number = address_data.street_number
            address.street_name = address_data.street_name
            address.city_id = city.city_id
            address.postal_code = address_data.postal_code
            address.address_line_2 = address_data.address_line_2

            # Sync changes via CRUD
            address = await crud_address.update_address(db, address)

            await db.commit()
            return address
        except Exception:
            await db.rollback()
            raise
