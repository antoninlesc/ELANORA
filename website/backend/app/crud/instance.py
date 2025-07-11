from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.model.instance import Instance


async def get_instance_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(Instance))
    return result.scalar_one()


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
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance
