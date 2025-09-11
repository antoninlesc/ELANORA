#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'website', 'backend'))

from app.db.database import get_db
from sqlalchemy import text

async def main():
    print("=== Current Database State ===")
    
    async for db in get_db():
        try:
            # Get project ID
            project_result = await db.execute(text("SELECT project_id FROM PROJECT WHERE project_name = 'lsfb'"))
            project = project_result.fetchone()
            if not project:
                print("Project 'lsfb' not found!")
                return
            
            project_id = project[0]
            print(f"Project ID: {project_id}")
            
            # Get ELAN files
            elan_result = await db.execute(text("""
                SELECT e.elan_id, e.file_path, e.content_id, f.filename 
                FROM ELAN_FILE e 
                JOIN FILE_CONTENT f ON e.content_id = f.content_id 
                WHERE e.project_id = :project_id
                ORDER BY e.elan_id
            """), {"project_id": project_id})
            
            elan_files = elan_result.fetchall()
            
            print("\nCurrent database state:")
            for ef in elan_files:
                elan_id, file_path, content_id, filename = ef
                print(f"  elan_id: {elan_id}")
                print(f"  file_path: {file_path}")
                print(f"  content_id: {content_id}")
                print(f"  filename: {filename}")
                print()
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(main())
