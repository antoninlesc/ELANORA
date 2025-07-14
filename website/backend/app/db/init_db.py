"""Database initialization utilities.

This module provides utilities for creating and managing database tables.
"""

# Import all models to ensure they are registered with the Base metadata
# This must be imported here to ensure all tables are created
import model  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.database import Base, get_engine


async def create_tables(engine: AsyncEngine | None = None) -> None:
    """Create all database tables."""
    if engine is None:
        engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables(engine: AsyncEngine | None = None) -> None:
    """Drop all database tables."""
    if engine is None:
        engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def recreate_tables(engine: AsyncEngine | None = None) -> None:
    """Drop and recreate all database tables."""
    await drop_tables(engine)
    await create_tables(engine)
