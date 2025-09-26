"""CRUD operations for Address model."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.address import Address
from app.utils.database import DatabaseUtils


async def get_address_by_id(db: AsyncSession, address_id: int) -> Address | None:
    """Get an address by its ID."""
    return await DatabaseUtils.get_by_id(db, Address, "address_id", address_id)


async def create_address(db: AsyncSession, address: Address) -> Address:
    """Create a new address."""
    instance = await DatabaseUtils.create(db, address)
    await db.flush()
    await db.refresh(instance)
    return instance


async def update_address(db: AsyncSession, address: Address) -> Address:
    """Update an existing address (syncs changes to DB)."""
    await db.flush()
    await db.refresh(address)
    return address
