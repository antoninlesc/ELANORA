#!/usr/bin/env python3

import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "website", "backend"))

from app.db.database import get_db
from sqlalchemy import text


async def main():
    print("=== Fixing Database State to Match Filesystem ===")

    async for db in get_db():
        try:
            print("1. Updating database to match current filesystem state...")

            # Update elan_id 706 from CLSFB1912_S040.eaf to TEST_RENAME_S040.eaf
            await db.execute(
                text("""
                UPDATE FILE_CONTENT 
                SET filename = 'TEST_RENAME_S040.eaf'
                WHERE content_id = 8
            """)
            )

            await db.execute(
                text("""
                UPDATE ELAN_FILE 
                SET file_path = 'lsfb/elan_files/TEST_RENAME_S040.eaf'
                WHERE elan_id = 706
            """)
            )

            await db.commit()
            print("✅ Database updated successfully!")

            # Verify the update
            print("\n2. Verifying database state after update...")
            elan_result = await db.execute(
                text("""
                SELECT e.elan_id, e.file_path, e.content_id, f.filename 
                FROM ELAN_FILE e 
                JOIN FILE_CONTENT f ON e.content_id = f.content_id 
                WHERE e.elan_id = 706
            """)
            )

            updated_record = elan_result.fetchone()
            if updated_record:
                elan_id, file_path, content_id, filename = updated_record
                print(f"  elan_id: {elan_id}")
                print(f"  file_path: {file_path}")
                print(f"  content_id: {content_id}")
                print(f"  filename: {filename}")
                print("✅ Database now matches filesystem!")
            else:
                print("❌ Failed to verify update")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            break


if __name__ == "__main__":
    asyncio.run(main())
