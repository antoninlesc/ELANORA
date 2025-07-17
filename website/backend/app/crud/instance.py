from sqlalchemy.ext.asyncio import AsyncSession

from app.model.instance import Instance
from app.utils.database import DatabaseUtils


async def get_instance_count(db: AsyncSession) -> int:
    return await DatabaseUtils.count(db, Instance, None)


async def create_instance(
    db: AsyncSession,
    name: str,
    institution: str,
    email: str,
    domain: str,
    timezone: str,
    language: str,
) -> Instance:
    instance = Instance(
        instance_name=name,
        institution_name=institution,
        contact_email=email,
        domain=domain,
        timezone=timezone,
        default_language=language,
    )
    return await DatabaseUtils.create_and_commit(db, instance)
