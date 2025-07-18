from sqlalchemy.ext.asyncio import AsyncSession
from app.model.tier_group import TierGroup
from app.utils.database import DatabaseUtils


async def create_tier_group(
    db: AsyncSession, section_id: int | None, project_id: int, elan_file_name: str
) -> TierGroup:
    group = TierGroup(
        section_id=section_id, project_id=project_id, elan_file_name=elan_file_name
    )
    return await DatabaseUtils.create_and_commit(db, group)


async def get_tier_group_by_id(
    db: AsyncSession, tier_group_id: int
) -> TierGroup | None:
    return await DatabaseUtils.get_by_id(db, TierGroup, "tier_group_id", tier_group_id)


async def get_tier_groups_by_section(
    db: AsyncSession, section_id: int
) -> list[TierGroup]:
    return await DatabaseUtils.get_by_filter(db, TierGroup, {"section_id": section_id})


async def get_tier_groups_by_project(
    db: AsyncSession, project_id: int
) -> list[TierGroup]:
    return await DatabaseUtils.get_by_filter(db, TierGroup, {"project_id": project_id})


async def update_tier_group_section(
    db: AsyncSession, tier_group_id: int, new_section_id: int | None
) -> int:
    return await DatabaseUtils.update_by_filter(
        db, TierGroup, {"tier_group_id": tier_group_id}, {"section_id": new_section_id}
    )


async def delete_tier_group(db: AsyncSession, tier_group_id: int) -> int:
    return await DatabaseUtils.delete_by_filter(
        db, TierGroup, tier_group_id=tier_group_id, auto_commit=True
    )
