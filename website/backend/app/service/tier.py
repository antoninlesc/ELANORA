from app.core.centralized_logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.project import get_project_id_by_name
from app.crud.association import get_elan_ids_for_project, get_tier_ids_for_elan_file
from app.crud.tier import get_tiers_by_ids
from app.model.tier import Tier

logger = get_logger()


class TierService:
    """Service class for handling tier-related operations."""

    @staticmethod
    def build_tier_tree(tiers: list[Tier]) -> list[dict]:
        tier_map = {tier.tier_id: tier for tier in tiers}
        children_map = {tier.tier_id: [] for tier in tiers}
        for tier in tiers:
            if tier.parent_tier_id and tier.parent_tier_id in children_map:
                children_map[tier.parent_tier_id].append(tier)
        roots = [
            tier
            for tier in tiers
            if not tier.parent_tier_id or tier.parent_tier_id not in tier_map
        ]

        def serialize(tier):
            return {
                "tier_id": tier.tier_id,
                "tier_name": tier.tier_name,
                "parent_tier_id": tier.parent_tier_id,
                "children": [serialize(child) for child in children_map[tier.tier_id]],
            }

        return [serialize(root) for root in roots]

    @staticmethod
    async def get_project_tiers_grouped_by_file(db: AsyncSession, project_name: str):
        project_id = await get_project_id_by_name(db, project_name)
        if not project_id:
            logger.error(f"Project not found: {project_name}")
            return []

        # 1. Get all ELAN file IDs for the project
        elan_ids = await get_elan_ids_for_project(db, project_id)
        if not elan_ids:
            return []

        # 2. For each ELAN file, get all tier IDs and then the Tier objects
        tier_groups = []
        for elan_id in elan_ids:
            # Get all tier_ids for this elan file
            tier_ids = await get_tier_ids_for_elan_file(db, elan_id)
            if not tier_ids:
                tier_groups.append([])
                continue
            tiers = await get_tiers_by_ids(db, tier_ids)
            # Build the tree for this file and append
            tier_groups.append(TierService.build_tier_tree(tiers))

        return tier_groups
