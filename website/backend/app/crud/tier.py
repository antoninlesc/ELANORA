"""Tier CRUD operations - Pure database access layer."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.model.tier import Tier
from app.core.centralized_logging import get_logger

logger = get_logger()


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
    db: AsyncSession,
    tier_id: str,
    tier_name: str,
    elan_id: int,
    parent_tier_id: Optional[str] = None,
) -> Tier:
    """Create a new tier in the database."""

    if elan_id is None:
        raise ValueError(
            "elan_id cannot be None when creating a Tier. This indicates a bug in the calling code."
        )

    tier = Tier(
        tier_id=tier_id,
        tier_name=tier_name,
        elan_id=elan_id,
        parent_tier_id=parent_tier_id,
    )

    try:
        db.add(tier)
        await db.commit()
        await db.refresh(tier)
        return tier
    except Exception:
        await db.rollback()
        raise


async def get_tiers_by_elan_id(db: AsyncSession, elan_id: int) -> list[Tier]:
    """Get all tiers for a given ELAN file."""
    result = await db.execute(select(Tier).filter(Tier.elan_id == elan_id))
    return list(result.scalars().all())


async def check_tier_exists(db: AsyncSession, tier_id: str) -> bool:
    """Check if a tier exists."""
    result = await db.execute(select(Tier.tier_id).filter(Tier.tier_id == tier_id))
    return result.scalar_one_or_none() is not None
