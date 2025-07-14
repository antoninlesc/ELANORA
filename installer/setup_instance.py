import asyncio
from app.core.config import ENVIRONMENT
from app.db.database import get_session_maker
from app.crud.instance import get_instance_count, create_instance


async def main():
    print("Imported config for environment:", ENVIRONMENT)
    print("=== ELANORA Instance Setup ===")
    name = input("Instance name: ")
    institution = input("Institution name: ")
    email = input("Contact email: ")
    domain = input("Domain: ")
    timezone = input("Timezone (e.g. Europe/Brussels): ")
    language = input("Default language (e.g. en): ")

    session_maker = get_session_maker()
    async with session_maker() as db:
        count = await get_instance_count(db)
        if count > 0:
            print("Instance already exists. Exiting.")
            return

        await create_instance(
            db,
            name,
            institution,
            email,
            domain,
            timezone,
            language,
        )
        print("Instance created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
