#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'website', 'backend'))

from app.db.database import get_db_sync
from app.model.elan_file import ElanFile
from app.model.file_content import FileContent
from app.model.project import Project

def main():
    print("=== Current Database State ===")
    
    with get_db_sync() as db:
        # Get the lsfb project
        project = db.query(Project).filter(Project.project_name == 'lsfb').first()
        if not project:
            print("Project 'lsfb' not found!")
            return
        
        print(f"Project: {project.project_name} (ID: {project.project_id})")
        print()
        
        # Get all ELAN files for this project
        elan_files = db.query(ElanFile).filter(ElanFile.project_id == project.project_id).all()
        
        print("ELAN_FILE table entries:")
        for elan_file in elan_files:
            print(f"  elan_id: {elan_file.elan_id}")
            print(f"  file_path: {elan_file.file_path}")
            print(f"  content_id: {elan_file.content_id}")
            print(f"  last_modified: {elan_file.last_modified}")
            print()
        
        # Get all FILE_CONTENT entries
        content_ids = [ef.content_id for ef in elan_files]
        file_contents = db.query(FileContent).filter(FileContent.content_id.in_(content_ids)).all()
        
        print("FILE_CONTENT table entries:")
        for file_content in file_contents:
            print(f"  content_id: {file_content.content_id}")
            print(f"  filename: {file_content.filename}")
            print(f"  content_hash: {file_content.content_hash[:16]}...")
            print(f"  file_size: {file_content.file_size}")
            print()

if __name__ == "__main__":
    main()
