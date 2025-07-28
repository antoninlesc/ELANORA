from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join
from app.model.naming_component import NamingComponent
from app.model.project_naming_standard import ProjectNamingStandard
from app.crud.component_accepted_value import (
    create_accepted_values,
    get_accepted_values,
    delete_accepted_values,
)
from app.utils.database import DatabaseUtils


async def get_components_by_standard(
    db: AsyncSession, naming_standard_id: int
) -> list[NamingComponent]:
    components = await DatabaseUtils.get_by_filter(
        db,
        NamingComponent,
        {"naming_standard_id": naming_standard_id},
        order_by=[NamingComponent.order],
    )
    # Attach accepted_values as a list of strings using a different attribute name
    for comp in components:
        values = await get_accepted_values(db, comp.id)
        comp.accepted_values_list = [v.value for v in values]
    return components


async def create_component(
    db: AsyncSession,
    naming_standard_id: int,
    file_type_id: int,
    name: str,
    regex: str,
    description: str | None,
    order: int,
    accepted_values: list[str] | None = None,
) -> NamingComponent:
    component = NamingComponent(
        naming_standard_id=naming_standard_id,
        file_type_id=file_type_id,
        name=name,
        regex=regex,
        description=description,
        order=order,
    )
    await DatabaseUtils.create(db, component)
    await db.flush()
    if accepted_values:
        await create_accepted_values(db, component.id, accepted_values)
    return component


async def update_component(
    db: AsyncSession,
    component_id: int,
    update_fields: dict,
    accepted_values: list[str] | None = None,
) -> int:
    await DatabaseUtils.update_by_filter(
        db, NamingComponent, {"id": component_id}, update_fields
    )
    if accepted_values is not None:
        await delete_accepted_values(db, component_id)
        await create_accepted_values(db, component_id, accepted_values)
    return component_id


async def delete_component(db: AsyncSession, component_id: int) -> int:
    await delete_accepted_values(db, component_id)
    return await DatabaseUtils.delete_by_filter(db, NamingComponent, id=component_id)


async def delete_components_by_standard(
    db: AsyncSession, naming_standard_id: int
) -> int:
    components = await DatabaseUtils.get_by_filter(
        db, NamingComponent, {"naming_standard_id": naming_standard_id}
    )
    for comp in components:
        await delete_accepted_values(db, comp.id)
    return await DatabaseUtils.delete_by_filter(
        db, NamingComponent, naming_standard_id=naming_standard_id
    )


async def get_unique_component_names_by_file_type(
    db: AsyncSession, file_type_id: int
) -> list[str]:
    stmt = (
        select(NamingComponent.name)
        .distinct()
        .where(NamingComponent.file_type_id == file_type_id)
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]


async def get_unique_component_names_by_project(
    db: AsyncSession, project_id: int
) -> list[str]:
    stmt = (
        select(NamingComponent.name)
        .distinct()
        .select_from(
            join(
                NamingComponent,
                ProjectNamingStandard,
                NamingComponent.naming_standard_id == ProjectNamingStandard.id,
            )
        )
        .where(ProjectNamingStandard.project_id == project_id)
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]
