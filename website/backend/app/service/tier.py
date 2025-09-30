from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.crud.elan_file import get_elan_ids_for_project
from app.crud.elan_file import get_elan_file_by_id
from app.crud.project import get_project_by_id, get_project_id_by_name
from app.crud.tier import get_tiers_by_elan_id
from app.crud.tier_group import (
    create_tier_group,
    get_tier_groups_by_project,
    get_tier_groups_by_section,
    get_tier_groups_by_tier_ids,
    update_tier_group_section,
)
from app.crud.tier_section import (
    create_tier_section,
    delete_tier_section,
    get_tier_sections_by_project,
    update_tier_section_name,
)
from app.model.tier import Tier
from app.schema.responses.tier import SectionInfo, TierGroupInfo, TierNode

logger = get_logger()


class TierService:
    """Service class for handling tier-related operations."""

    @staticmethod
    def build_tier_tree(tiers: list[Tier]) -> list[TierNode]:
        tier_map = {tier.tier_id: tier for tier in tiers}
        children_map = {tier.tier_id: [] for tier in tiers}
        for tier in tiers:
            if tier.parent_tier_id and tier.parent_tier_id in tier_map:
                children_map[tier.parent_tier_id].append(tier)

        roots = [
            tier
            for tier in tiers
            if not tier.parent_tier_id or tier.parent_tier_id not in tier_map
        ]

        def serialize(tier):
            return TierNode(
                tier_id=tier.tier_id,
                tier_name=tier.tier_name,
                parent_tier_id=tier.parent_tier_id,
                children=[serialize(child) for child in children_map[tier.tier_id]],
            )

        return [serialize(root) for root in roots]

    @staticmethod
    async def get_project_tiers_grouped_by_file(db: AsyncSession, project_name: str):
        project_id = await get_project_id_by_name(db, project_name)
        if not project_id:
            logger.error(f"Project not found: {project_name}")
            return {}

        elan_ids = await get_elan_ids_for_project(db, project_id)
        if not elan_ids:
            return {}

        result = {}
        for elan_id in elan_ids:
            elan_file = await get_elan_file_by_id(db, elan_id)
            if not elan_file:
                continue
            tiers = await get_tiers_by_elan_id(db, elan_id)
            if not tiers:
                result[elan_file.filename] = []
                continue
            result[elan_file.filename] = TierService.build_tier_tree(tiers)

        return {"tiers": result}


class TierSectionService:
    @staticmethod
    async def create_section(
        db,
        project_id: int,
        name: str,
        is_staged: bool = False,
        session_id: str | None = None,
    ):
        try:
            section = await create_tier_section(
                db, project_id, name, is_staged, session_id
            )
            await db.commit()
            return section
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def rename_section(
        db, tier_section_id: int, new_name: str, is_staged: bool = False
    ):
        try:
            section = await update_tier_section_name(db, tier_section_id, new_name)
            await db.commit()
            return section
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_section(db, tier_section_id: int, is_staged: bool = False):
        try:
            result = await delete_tier_section(db, tier_section_id)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_sections_for_project(db, project_id: int):
        return await get_tier_sections_by_project(db, project_id)

    @staticmethod
    async def get_sections_and_groups(
        db, project_id: int, include_staged: bool = False
    ):
        sections = await get_tier_sections_by_project(db, project_id, include_staged)
        tier_groups = await get_tier_groups_by_project(db, project_id, include_staged)

        project = await get_project_by_id(db, project_id)
        if not project:
            return {"sections": [], "tier_groups": []}
        elan_ids = await get_elan_ids_for_project(db, project_id)
        all_project_tiers = []
        for elan_id in elan_ids:
            tiers = await get_tiers_by_elan_id(db, elan_id)
            all_project_tiers.extend(tiers)

        # Remove duplicates (same tier might appear in multiple files)
        seen_tier_ids = set()
        unique_tiers = []
        for tier in all_project_tiers:
            if tier.tier_id not in seen_tier_ids:
                seen_tier_ids.add(tier.tier_id)
                unique_tiers.append(tier)

        # Get existing tier groups with their tier info
        tier_group_info = []
        assigned_tier_ids = set()
        for group in tier_groups:
            from app.crud.tier import get_tier_by_id

            tier = await get_tier_by_id(db, group.tier_id)
            if tier:
                tier_group_info.append(
                    TierGroupInfo(
                        tier_group_id=group.tier_group_id,
                        tier_name=group.tier_name,
                        section_id=group.section_id,
                        tier_id=group.tier_id,
                        parent_tier_id=tier.parent_tier_id,
                    )
                )
                assigned_tier_ids.add(group.tier_id)

        # Build sections with optional staged flags
        sections_list = [
            SectionInfo(
                section_id=s.tier_section_id,
                name=s.section_name,
                is_staged=s.is_staged if include_staged else None,
                session_id=s.session_id if include_staged else None,
            )
            for s in sections
        ]

        return {
            "sections": sections_list,
            "tier_groups": tier_group_info,
        }


class TierGroupService:
    @staticmethod
    async def assign_group_to_section(
        db,
        tier_group_id: int,
        section_id: int,
        project_id: int,
        tier_id: int,
        tier_name: str,
        is_staged: bool = False,
    ):
        try:
            # Get the tier hierarchy (parent + all children)
            from app.crud.tier_group import get_tier_hierarchy

            tier_hierarchy = await get_tier_hierarchy(db, tier_id)

            created_or_updated_ids = []

            for tier_id_in_hierarchy in tier_hierarchy:
                # Get tier info
                from app.crud.tier import get_tier_by_id

                tier = await get_tier_by_id(db, tier_id_in_hierarchy)
                if not tier:
                    continue

                # Check if tier group already exists
                existing_groups = await get_tier_groups_by_tier_ids(
                    db, project_id, [tier_id_in_hierarchy]
                )
                existing_group = existing_groups[0] if existing_groups else None

                if existing_group:
                    # Update existing tier group
                    await update_tier_group_section(
                        db, existing_group.tier_group_id, section_id
                    )
                    created_or_updated_ids.append(existing_group.tier_group_id)
                else:
                    # This should not happen since tier_group_id is provided, but handle gracefully
                    raise ValueError(
                        f"Tier group for tier {tier_id_in_hierarchy} not found"
                    )

            await db.commit()
            return created_or_updated_ids[0] if created_or_updated_ids else None
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def create_group(
        db,
        section_id: int,
        project_id: int,
        tier_id: int,
        tier_name: str,
        is_staged: bool = False,
    ):
        try:
            group = await create_tier_group(
                db, section_id, project_id, tier_id, tier_name, is_staged
            )
            await db.commit()
            return group
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_groups_for_section(db, section_id: int):
        return await get_tier_groups_by_section(db, section_id)
