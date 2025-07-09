import pytest
from sqlalchemy import select

from app.db.database import get_db
from app.model.instance import Instance


@pytest.mark.asyncio
async def test_get_all_instances():
    """Test to verify instance fetching."""
    async for session in get_db():
        try:
            result = await session.execute(select(Instance))
            instances = result.scalars().all()

            assert isinstance(instances, list)
            print(f"Instances fetched: {len(instances)}")

            if instances:
                first_instance = instances[0]
                assert hasattr(first_instance, "instance_id")
                assert hasattr(first_instance, "instance_name")
                assert hasattr(first_instance, "institution_name")

        finally:
            await session.close()
        break


@pytest.mark.asyncio
async def test_get_instance_by_id():
    """Test to fetch an instance by ID."""
    async for session in get_db():
        try:
            result = await session.execute(
                select(Instance).where(Instance.instance_id == 1)
            )
            instance = result.scalar_one_or_none()

            if instance:
                print(instance.__dict__)
                print(
                    {
                        k: v
                        for k, v in instance.__dict__.items()
                        if not k.startswith("_sa_")
                    }
                )
                assert instance.instance_id == 1
            else:
                print("No instance with ID 1 was found.")
        finally:
            await session.close()
        break
