from sqlalchemy.ext.asyncio import AsyncSession

from app.model.tier_group import TierGroup
from app.utils.database import DatabaseUtils


async def get_tier_hierarchy(db: AsyncSession, tier_id: int) -> list[int]:
    """Get all tier IDs in the hierarchy (parent and all children)."""
    from app.crud.tier import get_tier_by_id, get_child_tiers

    hierarchy = [tier_id]

    # Get all child tiers recursively
    async def get_children_recursive(parent_id: int):
        children = await get_child_tiers(db, parent_id)
        for child in children:
            hierarchy.append(child.tier_id)
            await get_children_recursive(child.tier_id)

    await get_children_recursive(tier_id)
    return hierarchy


async def create_tier_group(
    db: AsyncSession,
    section_id: int | None,
    project_id: int,
    tier_id: int,
    tier_name: str,
    is_staged: bool = False,
) -> TierGroup:
    group = TierGroup(
        section_id=section_id,
        project_id=project_id,
        tier_id=tier_id,
        tier_name=tier_name,
        is_staged=is_staged,
    )
    return await DatabaseUtils.create(db, group)


async def get_tier_group_by_id(
    db: AsyncSession, tier_group_id: int
) -> TierGroup | None:
    return await DatabaseUtils.get_by_id(db, TierGroup, "tier_group_id", tier_group_id)


async def get_tier_groups_by_section(
    db: AsyncSession, section_id: int, include_staged: bool = False
) -> list[TierGroup]:
    conditions = [TierGroup.section_id == section_id]
    if not include_staged:
        conditions.append(TierGroup.is_staged.is_(False))
    return await DatabaseUtils.get_by_conditions(db, TierGroup, conditions=conditions)


async def get_tier_groups_by_project(
    db: AsyncSession, project_id: int, include_staged: bool = False
) -> list[TierGroup]:
    conditions = [TierGroup.project_id == project_id]
    if not include_staged:
        conditions.append(TierGroup.is_staged.is_(False))
    return await DatabaseUtils.get_by_conditions(db, TierGroup, conditions=conditions)


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


async def delete_tier_groups_for_project_and_tier(
    db: AsyncSession, project_id: int, tier_id: int
) -> int:
    return await DatabaseUtils.delete_by_filter(
        db,
        TierGroup,
        project_id=project_id,
        tier_id=tier_id,
        auto_commit=True,
    )


async def assign_tier_hierarchy_to_section(
    db: AsyncSession, project_id: int, tier_id: int, section_id: int | None
) -> list[TierGroup]:
    """Assign a tier and all its children to a section."""
    from app.crud.tier import get_tier_by_id

    tier_hierarchy = await get_tier_hierarchy(db, tier_id)
    created_groups = []

    for tier_id_in_hierarchy in tier_hierarchy:
        tier = await get_tier_by_id(db, tier_id_in_hierarchy)
        if tier:
            # Check if tier group already exists
            existing = await DatabaseUtils.get_by_filter(
                db,
                TierGroup,
                {"project_id": project_id, "tier_id": tier_id_in_hierarchy},
                limit=1,
            )
            if existing:
                # Update existing group
                await update_tier_group_section(
                    db, existing[0].tier_group_id, section_id
                )
                created_groups.append(existing[0])
            else:
                # Create new group
                group = await create_tier_group(
                    db, section_id, project_id, tier_id_in_hierarchy, tier.tier_name
                )
                created_groups.append(group)

    return created_groups


async def get_tier_groups_by_tier_ids(
    db: AsyncSession, project_id: int, tier_ids: list[int], include_staged: bool = False
) -> list[TierGroup]:
    """Get tier groups for specific tier IDs in a project."""
    if not tier_ids:
        return []
    conditions = [TierGroup.project_id == project_id, TierGroup.tier_id.in_(tier_ids)]
    if not include_staged:
        conditions.append(TierGroup.is_staged.is_(False))
    return await DatabaseUtils.get_by_conditions(db, TierGroup, conditions=conditions)
