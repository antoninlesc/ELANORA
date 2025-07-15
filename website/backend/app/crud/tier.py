"""Tier CRUD operations - Pure database access layer."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.tier import Tier


async def get_tier_by_id(db: AsyncSession, tier_id: str) -> Tier | None:
    """Retrieve a tier by ID."""
    result = await db.execute(select(Tier).filter(Tier.tier_id == tier_id))
    return result.scalar_one_or_none()


async def get_all_tiers(db: AsyncSession) -> list[Tier]:
    """Get all tiers."""
    result = await db.execute(select(Tier))
    return list(result.scalars().all())


async def get_child_tiers(db: AsyncSession, parent_tier_id: str) -> list[Tier]:
    """Get all child tiers of a parent tier."""
    result = await db.execute(
        select(Tier).filter(Tier.parent_tier_id == parent_tier_id)
    )
    return list(result.scalars().all())


async def get_root_tiers(db: AsyncSession) -> list[Tier]:
    """Get all root tiers (no parent)."""
    result = await db.execute(select(Tier).filter(Tier.parent_tier_id.is_(None)))
    return list(result.scalars().all())


async def create_tier_in_db(
    db: AsyncSession, tier_id: str, tier_name: str, parent_tier_id: str | None = None
) -> Tier:
    """Create a new tier in the database."""
    tier = Tier(tier_id=tier_id, tier_name=tier_name, parent_tier_id=parent_tier_id)

    try:
        db.add(tier)
        await db.commit()
        await db.refresh(tier)
        return tier
    except Exception:
        await db.rollback()
        raise


async def check_tier_exists(db: AsyncSession, tier_id: str) -> bool:
    """Check if a tier exists."""
    result = await db.execute(select(Tier.tier_id).filter(Tier.tier_id == tier_id))
    return result.scalar_one_or_none() is not None
