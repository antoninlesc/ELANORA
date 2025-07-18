from app.core.centralized_logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.project import get_project_id_by_name, get_project_by_id
from app.crud.association import get_elan_ids_for_project, get_tier_ids_for_elan_file
from app.crud.tier import get_tiers_by_ids
from app.model.tier import Tier
from app.crud.elan_file import get_elan_file_by_id
from app.schema.responses.tier import TierNode
from app.crud.tier_section import (
    create_tier_section,
    get_tier_sections_by_project,
    update_tier_section_name,
    delete_tier_section,
)
from app.crud.tier_group import (
    create_tier_group,
    get_tier_groups_by_section,
    update_tier_group_section,
)
from app.crud.tier_group import get_tier_groups_by_project
from app.schema.responses.tier import TierGroupInfo, SectionInfo

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
            tier_ids = await get_tier_ids_for_elan_file(db, elan_id)
            if not tier_ids:
                result[elan_file.filename] = []
                continue
            tiers = await get_tiers_by_ids(db, tier_ids)
            result[elan_file.filename] = TierService.build_tier_tree(tiers)

        return {"tiers": result}


class TierSectionService:
    @staticmethod
    async def create_section(db, project_id: int, name: str):
        try:
            section = await create_tier_section(db, project_id, name)
            await db.commit()
            return section
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def rename_section(db, tier_section_id: int, new_name: str):
        try:
            section = await update_tier_section_name(db, tier_section_id, new_name)
            await db.commit()
            return section
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_section(db, tier_section_id: int):
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
    async def get_sections_and_groups(db, project_id: int):
        sections = await get_tier_sections_by_project(db, project_id)
        tier_groups = await get_tier_groups_by_project(db, project_id)

        project = await get_project_by_id(db, project_id)
        if not project:
            return {"sections": [], "tier_groups": []}
        tiers_by_file = await TierService.get_project_tiers_grouped_by_file(
            db, project.project_name
        )
        tiers_dict = tiers_by_file.get("tiers", {})

        return {
            "sections": [
                SectionInfo(section_id=s.tier_section_id, name=s.section_name)
                for s in sections
            ],
            "tier_groups": [
                TierGroupInfo(
                    tier_group_id=g.tier_group_id,
                    elan_file_name=g.elan_file_name,
                    section_id=g.section_id,
                    tiers=tiers_dict.get(g.elan_file_name, []),
                )
                for g in tier_groups
            ],
        }


class TierGroupService:
    @staticmethod
    async def assign_group_to_section(db, tier_group_id: int, section_id: int | None):
        try:
            result = await update_tier_group_section(db, tier_group_id, section_id)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def create_group(
        db, section_id: int | None, project_id: int, elan_file_name: str
    ):
        try:
            group = await create_tier_group(db, section_id, project_id, elan_file_name)
            await db.commit()
            return group
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_groups_for_section(db, section_id: int):
        return await get_tier_groups_by_section(db, section_id)
