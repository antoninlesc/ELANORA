import pytest
from sqlalchemy import select

from app.db.database import get_db
from app.models.instance import Instance


@pytest.mark.asyncio
async def test_get_all_instances():
    """Test pour vérifier la récupération des instances."""
    async for session in get_db():
        try:
            result = await session.execute(select(Instance))
            instances = result.scalars().all()

            assert isinstance(instances, list)
            print(f"Instances récupérées: {len(instances)}")

            # Si vous avez des données de test, vous pouvez vérifier
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
    """Test pour récupérer une instance par ID."""
    async for session in get_db():
        try:
            result = await session.execute(
                select(Instance).where(Instance.instance_id == 1)
            )
            instance = result.scalar_one_or_none()

            if instance:
                # Affiche toutes les colonnes de l'instance sous forme de dict
                print(instance.__dict__)
                # Ou, pour un affichage plus propre (sans _sa_instance_state)
                print(
                    {
                        k: v
                        for k, v in instance.__dict__.items()
                        if not k.startswith("_sa_")
                    }
                )
                assert instance.instance_id == 1
            else:
                print("Aucune instance trouvée avec l'ID 1")
        finally:
            await session.close()
        break
