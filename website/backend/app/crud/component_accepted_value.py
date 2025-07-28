from app.model.component_accepted_value import ComponentAcceptedValue
from app.utils.database import DatabaseUtils


async def create_accepted_values(db, naming_component_id, values: list[str]):
    objs = [
        ComponentAcceptedValue(naming_component_id=naming_component_id, value=v)
        for v in values
    ]
    for obj in objs:
        await DatabaseUtils.create(db, obj)
    await db.flush()
    return objs


async def get_accepted_values(db, naming_component_id):
    return await DatabaseUtils.get_by_filter(
        db, ComponentAcceptedValue, {"naming_component_id": naming_component_id}
    )


async def delete_accepted_values(db, naming_component_id):
    return await DatabaseUtils.delete_by_filter(
        db, ComponentAcceptedValue, naming_component_id=naming_component_id
    )
