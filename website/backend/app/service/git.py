import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logging import get_logger
from app.core.config import ELAN_PROJECTS_BASE_PATH
from app.crud.project import (
    create_project_db,
    delete_project_db,
    get_project_by_name,
    get_project_id_by_name,
    list_projects_by_instance,
    list_projects_by_user,
    project_exists_by_name,
    get_project_by_id,
)
from app.crud.elan_file import (
    get_elan_files_by_project,
    get_elan_file_name_by_id,
    get_elan_file_by_filename_and_project,
    update_elan_file_name,
)
from app.service.database_rename_handler import DatabaseRenameHandler
from app.service.git_status_parser import GitStatusParser, GitFileStatusAnalyzer
from app.crud import elan_file_media as elan_media_crud
from app.crud.effective_naming_standard import get_effective_standards_for_project
from app.schema.responses.git import (
    FileRenameResponse,
    BulkRenameResponse,
    RenameResult,
)


from app.core.exceptions import RenameConflictError
from app.crud.project_naming_standard import get_standard_with_components_full
from app.core.effective_naming_standard_locations import get_location_id_by_name
from app.schema.common.git import FileStatus
from app.schema.responses.git import ProjectInfo, ProjectSyncCheckResponse
from app.service.elan import ElanService
from app.utils.project_backup import restore_project_backup
from app.service.git_operations import (
    FileUploadProcessor,
    GitBranchManager,
    GitCommandRunner,
    delete_project_folder,
)
from app.utils.project_backup import (
    create_project_backup_structure,
    remove_project_backup,
    rename_project_backup_folder,
)
from app.utils.project_setup_utils import (
    copy_githooks,
    create_gitignore,
    create_project_structure,
    create_readme,
    update_project_githooks,
)
from app.utils.validation import ValidationUtils

logger = get_logger()


class GitService:
    """Service for managing Git operations for ELAN projects."""

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize the Git service.

        Args:
            base_path: Custom base path for projects. If None, uses config value.

        """
        if base_path is None:
            current_file = Path(__file__)
            elanora_root = current_file.parent.parent.parent.parent.parent
            self.base_path = elanora_root / ELAN_PROJECTS_BASE_PATH
        else:
            self.base_path = Path(base_path)

        self.base_path.mkdir(parents=True, exist_ok=True)

    def check_git_availability(self) -> dict[str, Any]:
        """Check if Git is available on the system."""
        try:
            runner = GitCommandRunner(self.base_path)
            result = runner.run(["--version"])
            return {
                "git_available": result.returncode == 0,
                "version": result.stdout.strip() if result.returncode == 0 else None,
                "status": "ready" if result.returncode == 0 else "error",
            }
        except FileNotFoundError:
            return {
                "git_available": False,
                "version": None,
                "status": "missing",
                "error": "Git not installed",
            }

    async def create_project(
        self,
        project_name: str,
        description: str,
        db: AsyncSession,
        user_id: int,
        instance_id: int = 1,
    ) -> dict[str, Any]:
        """Create a new project with Git repository and description."""
        project_path = self.base_path / project_name

        logger.info(f"Checking if project folder exists: {project_path}")
        logger.info(f"Folder exists? {project_path.exists()}")

        if project_path.exists():
            logger.warning(f"Project folder '{project_path}' already exists.")
            raise ValueError(f"Project '{project_name}' already exists")

        exists = await project_exists_by_name(db, project_name)
        logger.info(f"Checking if project exists in DB: {project_name} -> {exists}")
        if exists:
            logger.warning(f"Project '{project_name}' already exists in the database.")
            raise ValueError(f"Project '{project_name}' already exists")

        try:
            # Create project directory and structure
            create_project_structure(project_path)
            create_project_backup_structure(project_name)
            runner = GitCommandRunner(project_path)
            runner.init_repo()

            # Create .gitignore and README
            create_gitignore(project_path)
            create_readme(project_path, project_name)

            # Copy githooks
            copy_githooks(project_path, project_name)

            # Initial commit
            runner.add_all()
            runner.commit("Initial project setup")

            # Paths
            hooks_dir = project_path / ".git" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)

            # Save to database
            await create_project_db(
                db=db,
                project_name=project_name,
                description=description,
                project_path=str(project_path),
                instance_id=instance_id,
                creator_user_id=user_id,
            )
            await db.commit()

            return {
                "project_name": project_name,
                "path": str(project_path),
                "status": "created",
                "git_initialized": True,
                "created_at": datetime.now().isoformat(),
            }

        except Exception as e:
            await db.rollback()
            raise RuntimeError(f"Project creation failed: {e}") from e

    def commit_changes(
        self, project_name: str, commit_message: str, user_name: str = "user"
    ) -> dict[str, Any]:
        """Commit changes to a project."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            runner = GitCommandRunner(project_path)

            # Check if there are changes to commit
            if not runner.get_status().strip():
                raise ValueError("No changes to commit")

            # Add all changes
            runner.add_all()

            # Commit with user info
            full_message = f"{commit_message}\n\nCommitted by: {user_name}"
            runner.commit(full_message)

            # Get commit hash
            commit_hash = runner.get_commit_hash()

            return {
                "project_name": project_name,
                "message": commit_message,
                "commit_hash": commit_hash,
                "status": "committed",
                "committed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            raise RuntimeError(f"Commit failed: {e}") from e

    async def add_elan_files(
        self,
        project_id: int,
        files: list[UploadFile],
        db: AsyncSession,
        user_id: int,
        user_name: str,
    ) -> dict[str, Any]:
        """Add multiple ELAN files to the project with branch-based workflow."""
        # Fetch project details by ID
        project = await get_project_by_id(db, project_id)
        if not project:
            logger.error(f"Project with ID '{project_id}' not found in database")
            raise ValueError(f"Project with ID '{project_id}' not found")
        logger.info(
            f"Fetched project: project_id={project.project_id}, project_name={project.project_name}"
        )

        project_path = self.base_path / project.project_name
        logger.info(
            f"Starting add_elan_files for project ID: {project_id}, user: {user_name}, files: {[f.filename for f in files]}"
        )

        # Get location ID for upload page
        location_id = get_location_id_by_name("uploadPage")
        if location_id is None:
            logger.warning(
                "Location ID for 'uploadPage' not found; defaulting to no compliance check"
            )
        else:
            logger.debug(f"Using location ID: {location_id} for upload page")

        standard = None
        if location_id is not None:
            # Fetch effective standards using CRUD
            effective_standards = await get_effective_standards_for_project(
                db, project_id, location_id
            )
            logger.info(
                f"Fetched {len(effective_standards)} effective standards for project_id={project_id}, location_id={location_id}"
            )
            if effective_standards:
                # Use the first effective standard (adjust if multiple need handling)
                effective_standard = effective_standards[0]
                logger.debug(
                    f"Using effective standard: id={effective_standard.id}, naming_standard_id={effective_standard.naming_standard_id}"
                )
                # Fetch the full naming standard with components
                full_standard = await get_standard_with_components_full(
                    db, effective_standard.naming_standard_id
                )
                if full_standard:
                    # Extract the dict format expected by ValidationUtils
                    standard = {
                        "pattern": full_standard["pattern"],
                        "components": full_standard["components"],
                    }
                    logger.info(
                        f"Fetched full naming standard: pattern='{full_standard['pattern']}', components_count={len(full_standard['components'])}"
                    )
                else:
                    logger.warning(
                        f"No full naming standard found for naming_standard_id={effective_standard.naming_standard_id}"
                    )
            else:
                logger.info(
                    "No effective standards found; proceeding without compliance check"
                )
        else:
            logger.info("No location ID; skipping standard fetching")

        # Check filename compliance for each file
        compliant_files = []
        non_compliant_files = []
        try:
            for file in files:
                filename = file.filename
                if ValidationUtils.is_filename_compliant(standard, filename):
                    compliant_files.append(filename)
                    logger.debug(f"File '{filename}' is compliant with naming standard")
                else:
                    non_compliant_files.append(filename)
                    logger.warning(
                        f"File '{filename}' is non-compliant with naming standard"
                    )
            if non_compliant_files:
                logger.error(
                    f"Compliance check failed for files: {non_compliant_files}"
                )
                raise ValueError(
                    f"Filename '{non_compliant_files[0]}' does not comply with the project's naming standard."
                )  # Raise for first failure
            else:
                logger.info(f"All {len(files)} files are compliant: {compliant_files}")
        except Exception as e:
            logger.error(
                f"Compliance check error for files {[f.filename for f in files]}: {e}",
                exc_info=True,
            )
            raise ValueError(
                f"Filename compliance check failed due to data issue: {e}"
            ) from e
        # Proceed with the rest of the method
        self._validate_upload_request(project_path, files)
        logger.info("Upload request validated successfully")

        try:
            # Setup Git environment
            self._configure_git_user(project_path, user_name)
            existing_files = self._get_existing_files(project_path, files)

            # Initialize managers
            branch_manager = GitBranchManager(project_path)
            file_processor = FileUploadProcessor(project_path)

            # Create branch and process files
            branch_manager.create_upload_branch(user_name, len(files))
            uploaded_files, failed_files = await file_processor.process_files(
                files, existing_files
            )

            if not uploaded_files:
                raise RuntimeError("No files were successfully uploaded")

            # Commit
            file_processor.commit_files(uploaded_files, user_name)

            # Build response
            logger.info(
                f"Successfully processed upload for project: {project.project_name}"
            )
            return self._build_upload_response(
                project.project_name,
                uploaded_files,
                failed_files,
                existing_files,
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to add ELAN files: {e}") from e
        except Exception as e:
            logger.error(f"Batch file operation failed: {e}")
            raise RuntimeError(f"Failed to add ELAN files: {e}") from e

    async def list_projects(
        self, db: AsyncSession, instance_id: int
    ) -> list[ProjectInfo]:
        """List all projects for a given instance.

        Args:
            db (AsyncSession): The database session.
            instance_id (int): The instance identifier.

        Returns:
            list[ProjectInfo]: A list of project information objects.

        """
        projects = await list_projects_by_instance(db, instance_id)
        return [
            ProjectInfo(
                project_id=p.project_id,
                project_name=p.project_name,
                project_description=p.description,
            )
            for p in projects
        ]

    async def list_user_projects(
        self, db: AsyncSession, user_id: int, instance_id: int
    ) -> list[ProjectInfo]:
        """List projects that a specific user has access to."""
        projects = await list_projects_by_user(db, user_id, instance_id)
        return [
            ProjectInfo(
                project_id=p.project_id,
                project_name=p.project_name,
                project_description=p.description,
            )
            for p in projects
        ]

    async def init_project_from_folder_upload(
        self,
        project_name: str,
        description: str,
        files: list[UploadFile],
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        """Initialize a new project from a folder upload, saving .eaf files, creating a git repository, and updating the database.

        Args:
            project_name (str): The name of the new project.
            description (str): Description of the project.
            files (list[UploadFile]): List of uploaded files.
            db (AsyncSession): Database session.
            user_id (int): ID of the user creating the project.

        Returns:
            dict: Information about the initialized project.

        Raises:
            ValueError: If the project already exists.

        """
        logger.info(
            "Starting project initialization from folder upload for project: %s",
            project_name,
        )
        logger.info("User ID: %s, Files count: %d", user_id, len(files))
        logger.debug("Files: %s", [f.filename for f in files])

        project_path = self.base_path / project_name
        elan_files_dir = project_path / "elan_files"
        logger.debug("Project path: %s", project_path)
        logger.debug("ELAN files directory: %s", elan_files_dir)

        if project_path.exists():
            logger.error("Project path already exists: %s", project_path)
            raise ValueError(f"Project '{project_name}' already exists")

        logger.info("Creating project directories")
        project_path.mkdir(parents=True, exist_ok=True)
        elan_files_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Directories created successfully")

        # Create README.md and .gitignore
        logger.info("Creating gitignore and README files")
        create_gitignore(project_path)
        create_readme(project_path, project_name)
        logger.debug("Project files created")

        # Save only .eaf files, directly in elan_files directory
        logger.info("Processing uploaded files")
        saved_files = []
        for file in files:
            logger.debug("Processing file: %s", file.filename)
            if not file.filename or not file.filename.lower().endswith(".eaf"):
                logger.debug("Skipping non-.eaf file: %s", file.filename)
                continue

            dest_path = elan_files_dir / Path(file.filename).name
            logger.debug("Saving .eaf file: %s to %s", file.filename, dest_path)

            try:
                file_content = await file.read()
                logger.debug("Read %d bytes from %s", len(file_content), file.filename)

                async with aiofiles.open(dest_path, "wb") as f:
                    await f.write(file_content)

                logger.debug("Successfully saved: %s", dest_path)
                saved_files.append(file.filename)
            except Exception as e:
                logger.error("Failed to save file %s: %s", file.filename, e)
                raise

        logger.info("Saved %d .eaf files: %s", len(saved_files), saved_files)

        # Git operations
        logger.info("Initializing Git repository")
        runner = GitCommandRunner(project_path)
        runner.init_repo()
        logger.debug("Git repository initialized")

        runner.add_all()
        logger.debug("Files added to Git")

        runner.commit("Initial commit from uploaded folder")
        logger.debug("Initial commit created")

        try:
            logger.info("Creating project in database")
            await create_project_db(
                db=db,
                project_name=project_name,
                description=description,
                project_path=str(project_path),
                instance_id=1,
                creator_user_id=user_id,
            )
            await db.commit()
            logger.debug("Project created in database successfully")

            logger.info("Processing ELAN files for database")
            elan_service = ElanService(db)
            elan_files = list(elan_files_dir.rglob("*.eaf"))
            logger.info(
                "Found %d .eaf files to process: %s",
                len(elan_files),
                [f.name for f in elan_files],
            )

            processed_files = []
            skipped_files = []
            failed_files = []

            for elan_file in elan_files:
                logger.debug("Processing ELAN file: %s", elan_file)
                try:
                    result = await elan_service.process_single_file(
                        str(elan_file), user_id, project_name
                    )

                    if result["status"] == "processed":
                        processed_files.append(result["filename"])
                    elif result["status"] == "skipped":
                        skipped_files.append(result["filename"])
                    elif result["status"] == "failed":
                        failed_files.append(result["filename"])

                except Exception as e:
                    logger.error("Failed to process ELAN file %s: %s", elan_file, e)
                    failed_files.append(elan_file.name)
                    raise

            await db.commit()
            logger.info(
                "ELAN processing complete. Processed: %d, Skipped: %d, Failed: %d",
                len(processed_files),
                len(skipped_files),
                len(failed_files),
            )

            if skipped_files:
                logger.info("Skipped files (already in database): %s", skipped_files)
            if failed_files:
                logger.warning("Failed files: %s", failed_files)

        except Exception as e:
            await db.rollback()
            logger.error("Failed to initialize project from folder: %s", e)
            logger.error("Rolling back database changes")
            raise

        result = {
            "project_name": project_name,
            "path": str(project_path),
            "status": "initialized",
            "git_initialized": True,
            "created_at": datetime.now().isoformat(),
        }

        logger.info("Project initialization completed successfully")
        logger.debug("Result: %s", result)

        return result

    async def _sync_elan_files_with_db(
        self, project_path: Path, db: AsyncSession, user_id: int, project_name: str
    ):
        """Parse all .eaf files in the project and update the database."""
        elan_service = ElanService(db)
        elan_files = list((project_path / "elan_files").glob("*.eaf"))
        for elan_file in elan_files:
            await elan_service.process_single_file(
                str(elan_file), user_id, project_name
            )

    def _validate_upload_request(
        self, project_path: Path, files: list[UploadFile]
    ) -> None:
        """Validate the upload request."""
        if not project_path.exists():
            raise FileNotFoundError(
                "Project not found at the specified path: {project_path}"
            )
        if not files:
            raise ValueError("No files provided")
        for file in files:
            if not file.filename:
                raise ValueError("All files must have filenames")

    def _get_existing_files(
        self, project_path: Path, files: list[UploadFile]
    ) -> list[str]:
        """Get list of files that already exist."""
        existing_files = []
        for file in files:
            filename = file.filename if file.filename is not None else ""
            dest_path = project_path / "elan_files" / filename
            if filename and dest_path.exists():
                existing_files.append(filename)
        return existing_files

    def _build_upload_response(
        self,
        project_name: str,
        uploaded_files,
        failed_files,
        existing_files: list[str],
        upload_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the upload response."""
        if upload_info is None:
            # Simple response for direct upload
            return {
                "project_name": project_name,
                "uploaded_files": [
                    self._convert_upload_result(f) for f in uploaded_files
                ],
                "failed_files": [self._convert_upload_result(f) for f in failed_files],
                "total_uploaded": len(uploaded_files),
                "total_failed": len(failed_files),
                "existing_files_updated": len(existing_files),
                "new_files_added": len(uploaded_files) - len(existing_files),
                "status": "completed",
                "requires_approval": False,
                "uploaded_at": datetime.now().isoformat(),
                "message": "Upload completed successfully",
            }
        else:
            # Legacy response for approval workflow
            return {
                "project_name": project_name,
                "branch_name": upload_info.get("branch_name"),
                "uploaded_files": [
                    self._convert_upload_result(f) for f in uploaded_files
                ],
                "failed_files": [self._convert_upload_result(f) for f in failed_files],
                "total_uploaded": len(uploaded_files),
                "total_failed": len(failed_files),
                "existing_files_updated": len(existing_files),
                "new_files_added": len(uploaded_files) - len(existing_files),
                "status": upload_info["status"],
                "requires_approval": upload_info.get("requires_approval", True),
                "has_differences": upload_info.get("has_differences", False),
                "upload_summary": {
                    "new_files": upload_info.get("new_files", []),
                    "modified_files": upload_info.get("modified_files", []),
                    "deleted_files": upload_info.get("deleted_files", []),
                },
                "admin_info": {
                    "pending_approval_since": upload_info.get("pending_approval_since"),
                    "approval_branch": upload_info.get("branch_name"),
                    "original_branch": upload_info.get("original_branch"),
                    "next_steps": "Upload saved for admin approval. Admin needs to test merge and resolve any conflicts.",
                },
                "uploaded_at": datetime.now().isoformat(),
                "message": upload_info.get(
                    "message", "Upload completed and saved for admin approval"
                ),
            }

    def _convert_upload_result(self, result) -> dict:
        """Convert FileUploadResult to dict for response."""
        if hasattr(result, "success"):
            return {
                "filename": result.filename,
                "size": result.size,
                "existed": result.existed,
            }
        return result  # Already a dict

    def get_branches(self, project_name: str) -> dict[str, Any]:
        """Get all branches for a project."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            runner = GitCommandRunner(project_path)
            branches_raw = runner.get_branches()
            branches = []
            current_branch = None

            for line in branches_raw:
                stripped_line = line.strip()
                if stripped_line.startswith("* "):
                    current_branch = stripped_line[2:]
                    branches.append({"name": current_branch, "is_current": True})
                elif stripped_line and not stripped_line.startswith("remotes/"):
                    branches.append({"name": stripped_line, "is_current": False})

            return {
                "project_name": project_name,
                "branches": branches,
                "current_branch": current_branch,
            }

        except Exception as e:
            raise RuntimeError(f"Failed to get branches: {e}") from e

    def _configure_git_user(self, project_path: Path, instance_name: str) -> None:
        runner = GitCommandRunner(project_path)
        runner.configure_user(instance_name)

    def _create_readme(self, project_name: str) -> str:
        """Generate README content for a new project."""
        return f"# {project_name}\n\nThis is the ELAN project '{project_name}'.\n"

    def _parse_git_status(self, status_output: str) -> list[dict[str, str]]:
        """Parse the output of 'git status --porcelain'."""
        files = []
        pattern = re.compile(r"^([ MADRCU\?]{1,2})\s+(.*)$")
        for line in status_output.strip().splitlines():
            if not line:
                continue
            match = pattern.match(line)
            if match:
                status = match.group(1).strip()
                filename = match.group(2).strip()
                files.append({"filename": filename, "status": status})
        return files

    def _get_recent_commits(
        self, project_path: Path, count: int = 5
    ) -> list[dict[str, str]]:
        """Get recent commits for the project."""
        runner = GitCommandRunner(project_path)
        result = runner.get_log(count)
        commits = []
        for line in result.strip().splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(
                    {
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                    }
                )
        return commits

    def checkout_branch(self, project_name: str, branch_name: str) -> dict[str, str]:
        """Switch to a different branch in the given project."""
        project_path = self.base_path / project_name
        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")
        try:
            runner = GitCommandRunner(project_path)
            runner.checkout(branch_name)
            return {
                "project_name": project_name,
                "branch_name": branch_name,
                "status": "checked_out",
                "message": f"Switched to branch '{branch_name}' in project '{project_name}'.",
            }
        except Exception as e:
            raise RuntimeError(f"Failed to checkout branch: {e}") from e

    async def list_project_files(
        self, project_name: str, db: AsyncSession, include_media: bool = False
    ) -> dict[str, Any]:
        """Return enriched .eaf files for the project using CRUD, optionally with media information."""
        project = await get_project_by_name(db, project_name)
        if not project:
            raise ValueError(f"Project '{project_name}' not found.")

        # Use CRUD to get files with user info
        db_files = await get_elan_files_by_project(db, project.project_id)

        # If media is requested, get media information
        media_mapping = {}
        if include_media:
            files_with_media = (
                await elan_media_crud.get_project_files_with_media_simple(
                    db, project.project_id
                )
            )

            # Create a mapping of filename to media info
            media_mapping = {
                file_data["filename"]: {
                    "media_filenames": file_data["media_filenames"],
                    "elan_id": file_data["elan_id"],
                }
                for file_data in files_with_media
            }

        enriched_files = []
        for elan_file, username in db_files:
            file_path = Path(elan_file.absolute_file_path)
            logger.info(f"Getting info for file: {file_path}")

            # Build base file info
            file_info = {
                "name": elan_file.filename,
                "size": elan_file.file_size,
                "lastModified": elan_file.last_modified.isoformat()
                if elan_file.last_modified
                else None,
                "lastUpdatedBy": username or "N/A",
                "type": "file",
            }

            # Add media information if requested
            if include_media:
                if elan_file.filename in media_mapping:
                    media_info = media_mapping[elan_file.filename]
                    file_info["media_filenames"] = media_info["media_filenames"]
                    file_info["elan_id"] = media_info["elan_id"]
                else:
                    file_info["media_filenames"] = []
                    file_info["elan_id"] = elan_file.elan_id

            enriched_files.append(file_info)

        logger.info(f"Retrieved files for project '{project_name}': {enriched_files}")
        return {"files": enriched_files}

    async def synchronize_project(
        self, project_name: str, db: AsyncSession, user_id: int
    ) -> dict:
        """Idempotently synchronize the project's elan_files with the database."""
        project_path = self.base_path / project_name
        runner = GitCommandRunner(project_path)

        logger.info(f"Starting synchronization for project: {project_name}")

        # Add all changes to staging area
        runner.add_all()

        # Get file statuses directly (not via sync check to avoid serialization)
        elan_files_dir = project_path / "elan_files"

        # Stage all changes first to enable rename detection for filesystem renames
        logger.info("Staging all changes to detect filesystem renames...")
        status_output = runner.get_status_with_renames()

        logger.info(f"Git status output: '{status_output}'")

        # Use GitStatusParser for cleaner parsing
        parser = GitStatusParser()
        analyzer = GitFileStatusAnalyzer(parser)

        # Get all Git-tracked files
        all_tracked_result = runner.run(["ls-files"], check=True)
        all_tracked_files = set(all_tracked_result.stdout.strip().splitlines())
        logger.info(f"All tracked files in Git: {all_tracked_files}")

        # Use the analyzer to process all files
        files_status, processed_files = analyzer.analyze_project_files(
            status_output, all_tracked_files, elan_files_dir
        )
        logger.info(f"Processed files: {processed_files}")
        logger.info(f"Files status: {files_status}")

        elan_service = ElanService(db)
        updated_files = []
        deleted_files = []

        logger.info(f"Processing {len(files_status)} file status changes")

        for file_status in files_status:
            filename = file_status.filename
            status = file_status.status
            file_path = project_path / filename

            logger.info(f"Processing file: {filename} with status: {status}")

            try:
                if status in {"added", "untracked"}:
                    if file_path.exists():
                        logger.info(f"Adding new file in DB: {file_path}")
                        await elan_service.process_single_file(
                            str(file_path), user_id, project_name
                        )
                        updated_files.append(file_path)
                        logger.info(f"Successfully added file to DB: {file_path}")
                    else:
                        logger.warning(
                            f"File marked as {status} but doesn't exist: {file_path}"
                        )
                elif status == "modified":
                    if file_path.exists():
                        logger.info(f"Updating modified file in DB: {file_path}")
                        await elan_service.process_single_file_and_update(
                            str(file_path), user_id, project_name
                        )
                        updated_files.append(file_path)
                        logger.info(f"Successfully updated file in DB: {file_path}")
                    else:
                        logger.warning(
                            f"File marked as modified but doesn't exist: {file_path}"
                        )
                elif status == "deleted":
                    logger.info(f"Removing deleted file from DB: {filename}")
                    await elan_service.delete_elan_files_from_db(filename, project_name)
                    deleted_files.append(filename)
                    logger.info(f"Successfully deleted file from DB: {filename}")
                elif status == "renamed":
                    # Handle Git-detected renames by updating database filename
                    old_filename = file_status.old_filename
                    new_filename = file_status.new_filename

                    logger.info(f"Processing rename: {old_filename} -> {new_filename}")

                    if old_filename and new_filename:
                        # Extract just the filename from the full path for database lookup
                        old_filename_only = Path(old_filename).name
                        new_filename_only = Path(new_filename).name

                        logger.info(
                            f"Database rename: {old_filename_only} -> {new_filename_only}"
                        )
                        rename_handler = DatabaseRenameHandler(db)
                        success = await rename_handler.process_rename(
                            old_filename_only, new_filename_only, project_name
                        )
                        if success:
                            updated_files.append(project_path / new_filename)
                        else:
                            logger.warning(
                                f"Failed to process rename: {old_filename_only} -> {new_filename_only}"
                            )
                    else:
                        logger.warning(
                            f"Rename detected but missing old/new filename info: {file_status}"
                        )
                else:
                    logger.warning(f"Unknown status '{status}' for file: {filename}")
            except Exception as e:
                logger.error(
                    f"Failed to process file {filename} with status {status}: {e}"
                )
                # Continue processing other files instead of failing completely

        # Commit database changes if any were made
        await db.commit()
        logger.info("Database changes committed")

        # Commit changes if any
        status_output = runner.get_status()
        if status_output.strip():
            runner.commit(f"Synchronized project '{project_name}' with ELAN files")

        logger.info(f"Synchronization complete for project: {project_name}")

        # Return a status/check response
        return ProjectSyncCheckResponse(
            project_name=project_name,
            in_sync=True,
            files_status=[
                FileStatus(
                    filename=str(f), status="updated", description="File updated"
                )
                for f in updated_files
            ]
            + [
                FileStatus(filename=f, status="deleted", description="File deleted")
                for f in deleted_files
            ],
        ).model_dump()

    async def delete_project(self, project_name: str, db: AsyncSession):
        """Delete a project by its ID."""
        logger.info(f"Starting deletion of project: {project_name}")
        # Remove all DB artifacts (project, files, annotations, etc.)
        try:
            await delete_project_db(db, project_name)
            logger.info(f"Database records deleted for project: {project_name}")
            await db.commit()
        except Exception as db_exc:
            await db.rollback()
            logger.error(
                f"Failed to delete project from DB: {project_name} | Error: {db_exc}"
            )
            raise

        # Remove the project folder from disk
        if not project_name:
            logger.error(f"Project name not found for project_name: {project_name}")
            raise ValueError(f"Project name not found for project_name: {project_name}")
        project_path = self.base_path / project_name
        delete_project_folder(project_path)

    async def edit_project(
        self,
        old_project_name: str,
        new_project_name: str,
        new_project_description: str | None,
        db: AsyncSession,
    ) -> dict:
        """Edit an existing project both in the filesystem and in the database.

        Args:
            old_project_name (str): The current name of the project.
            new_project_name (str): The new name to assign to the project.
            new_project_description (str | None): The new description.
            db (AsyncSession): The database session.

        Returns:
            dict: A dictionary containing the new project name and description.

        Raises:
            ValueError: If the old project is not found in the database.
            FileNotFoundError: If the old project folder does not exist.
            FileExistsError: If the target project folder already exists.
            Exception: If renaming the folder fails.

        """
        logger.info(
            f"Starting edit of project: '{old_project_name}' to '{new_project_name}'"
        )
        project = await get_project_by_name(db, old_project_name)
        if not project:
            logger.error(f"Project '{old_project_name}' not found in DB")
            raise ValueError(f"Project '{old_project_name}' not found in DB")

        old_path = Path(self.base_path) / old_project_name

        # Only rename if the name is actually changed
        if new_project_name != old_project_name:
            new_path = Path(self.base_path) / new_project_name
            if not old_path.exists():
                logger.error(
                    f"Project folder '{old_project_name}' not found at {old_path}"
                )
                raise FileNotFoundError(
                    f"Project folder '{old_project_name}' not found"
                )
            if new_path.exists():
                logger.error(
                    f"Target project folder '{new_project_name}' already exists at {new_path}"
                )
                raise FileExistsError(
                    f"Target project folder '{new_project_name}' already exists"
                )
            try:
                os.rename(old_path, new_path)
                logger.info(f"Renamed folder from '{old_path}' to '{new_path}'")
            except Exception as e:
                logger.error(f"Failed to rename folder: {e}")
                raise

            project.project_name = new_project_name
            project.project_path = str(new_path)
            rename_project_backup_folder(old_project_name, project.project_name)
            update_project_githooks(new_path, project.project_name)
        else:
            # Name unchanged, just update description
            logger.info("Project name unchanged, only updating description.")

        project.description = new_project_description
        await db.commit()
        logger.info(
            f"Edited project in DB: '{old_project_name}' -> '{new_project_name}'"
        )
        logger.info(f"Changed project description to: {new_project_description}")
        return {
            "new_project_name": new_project_name,
            "new_project_description": new_project_description,
        }

    def synchronize_project_check(self, project_name: str) -> dict:
        """Check for changes in a Git-managed project and analyze file status.

        Analyzes the Git status to detect file changes in the elan_files directory
        and compares against tracked files to determine sync status.

        Args:
            project_name: Name of the project to check for changes

        Returns:
            Dictionary containing project sync status and file change information

        """
        project_path = self.base_path / project_name
        elan_files_dir = project_path / "elan_files"
        git_dir = project_path / ".git"

        logger.info(f"GitService base_path: {self.base_path}")
        logger.info(f"Project path: {project_path}")
        logger.info(f"Project path exists: {project_path.exists()}")

        if not project_path.exists():
            return {
                "project_name": project_name,
                "status": "missing_folder",
                "in_sync": False,
                "files_status": [],
            }
        if not git_dir.exists():
            return {
                "project_name": project_name,
                "status": "missing_git",
                "in_sync": False,
                "files_status": [],
            }
        if not elan_files_dir.exists():
            return {
                "project_name": project_name,
                "status": "missing_elan_files",
                "in_sync": False,
                "files_status": [],
            }

        runner = GitCommandRunner(project_path)

        # Stage all changes first to enable rename detection for filesystem renames
        logger.info("Staging all changes to detect filesystem renames...")
        status_output = runner.get_status_with_renames()

        logger.info(f"Git status output: '{status_output}'")

        # Use GitStatusParser for cleaner parsing
        parser = GitStatusParser()
        analyzer = GitFileStatusAnalyzer(parser)

        # Get all Git-tracked files
        all_tracked_result = runner.run(["ls-files"], check=True)
        all_tracked_files = set(all_tracked_result.stdout.strip().splitlines())
        logger.info(f"All tracked files in Git: {all_tracked_files}")

        # Use the analyzer to process all files
        files_status, processed_files = analyzer.analyze_project_files(
            status_output, all_tracked_files, elan_files_dir
        )

        logger.info(f"Processed files: {processed_files}")
        logger.info(f"Files status: {files_status}")

        in_sync = not bool(files_status)

        return ProjectSyncCheckResponse(
            project_name=project_name, in_sync=in_sync, files_status=files_status
        ).model_dump()

    def discard_local_changes(self, project_name: str) -> str:
        project_path = self.base_path / project_name
        runner = GitCommandRunner(project_path)
        remotes = runner.run(["remote", "-v"]).stdout.strip()
        if "origin" in remotes:
            logger.info(f"Remote 'origin' found for project '{project_name}'")
            runner.run(["fetch", "origin"], check=True)
            runner.reset_hard("origin/master")
        else:
            logger.warning(f"No remote 'origin' found for project '{project_name}'")
            runner.reset_hard()
        runner.clean(force=True, directories=True)
        return "Local changes discarded and folder reset to match the latest remote master."

    async def restore_project_from_backup(
        self, project_name: str, db: AsyncSession, user_id: int
    ) -> str:
        """Restore the project folder from the most recent backup (including .git, elan_files, README.md).

        and update the database to match the restored state.
        """
        restore_project_backup(project_name, self.base_path)

        await self.synchronize_project(project_name, db, user_id)

        return (
            f"Project '{project_name}' restored from backup and database synchronized."
        )

    async def decline_project_backup(self, db: AsyncSession, project_name: str) -> None:
        """Remove the backup folder for the project and delete all related data."""
        # Remove backup
        remove_project_backup(project_name)

        # Determine if the project folder exists
        project_path = self.base_path / project_name
        if project_path.exists():
            delete_project_folder(project_path)

        # Remove all DB artifacts
        await delete_project_db(db, project_name)
        await db.commit()

    async def rename_file(
        self, project_name: str, elan_id: int, new_filename: str, db: AsyncSession
    ) -> FileRenameResponse:
        """Rename a single file in the project using elan_id."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        # Get current filename from database
        old_filename = await get_elan_file_name_by_id(db, elan_id)
        if not old_filename:
            raise FileNotFoundError(f"ELAN file with ID {elan_id} not found")

        old_file_path = project_path / "elan_files" / old_filename
        new_file_path = project_path / "elan_files" / new_filename

        if not old_file_path.exists():
            raise FileNotFoundError(
                f"File '{old_filename}' not found in project filesystem"
            )

        # Check for conflict: if target filename already exists, get its elan_id
        if new_file_path.exists():
            conflict_elan_id = None
            # Get project_id to find the conflicting file
            project_id = await get_project_id_by_name(db, project_name)
            if project_id:
                conflicting_file = await get_elan_file_by_filename_and_project(
                    db, new_filename, project_id
                )
                if conflicting_file:
                    conflict_elan_id = conflicting_file.elan_id

            # Raise custom conflict exception with conflict info
            logger.warning(
                f"Rename conflict detected: {new_filename} already exists (conflict_elan_id={conflict_elan_id})"
            )
            raise RenameConflictError(
                f"File '{new_filename}' already exists in project",
                conflict_elan_id=conflict_elan_id,
                message_key="rename_file_conflict",
            )

        try:
            # 1. Update database first
            await update_elan_file_name(db, elan_id, new_filename)
            logger.info(
                f"Updated database filename for elan_id={elan_id}: {old_filename} -> {new_filename}"
            )

            # 2. Rename the file on filesystem
            old_file_path.rename(new_file_path)
            logger.info(f"Renamed file on filesystem: {old_filename} -> {new_filename}")

            # 3. Update git (add the rename operation)
            runner = GitCommandRunner(project_path)
            runner.add_all()  # Add all changes including the rename
            commit_hash = runner.commit(
                f"Rename file: {old_filename} -> {new_filename}"
            )
            logger.info(f"Committed rename to git with hash: {commit_hash}")

            # 4. Commit database transaction
            await db.commit()
            logger.info(
                f"Successfully completed file rename: {old_filename} -> {new_filename}"
            )

            return FileRenameResponse(
                project_name=project_name,
                old_filename=old_filename,
                new_filename=new_filename,
                success=True,
                committed=True,
                commit_hash=commit_hash,
                renamed_at=datetime.now().isoformat(),
                message=f"Successfully renamed {old_filename} to {new_filename}",
            )

        except Exception as e:
            logger.error(f"Error during file rename: {e!s}")

            # Rollback database
            await db.rollback()
            logger.info("Rolled back database transaction")

            # Try to rollback filesystem change if possible
            if new_file_path.exists() and not old_file_path.exists():
                try:
                    new_file_path.rename(old_file_path)
                    logger.info(
                        f"Rolled back filesystem rename: {new_filename} -> {old_filename}"
                    )
                except Exception as rollback_error:
                    logger.warning(f"Could not rollback file rename: {rollback_error}")

            raise e
            raise RuntimeError(f"Failed to rename file: {e}") from e

    async def rename_files(
        self, project_name: str, renames: list[dict], db: AsyncSession
    ) -> BulkRenameResponse:
        """Rename multiple files in the project using elan_ids."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        successful_renames = []
        failed_renames = []

        try:
            runner = GitCommandRunner(project_path)

            # Process each rename individually
            for rename_info in renames:
                result = await self._process_single_bulk_rename(
                    rename_info, project_path, db, runner
                )

                if result.success:
                    successful_renames.append(result)
                else:
                    failed_renames.append(result)

            # Commit all changes if any were successful
            commit_hash = await self._finalize_bulk_rename(
                successful_renames, runner, db
            )

            # Count conflicts
            conflicts_count = sum(
                1 for result in failed_renames if result.conflict_elan_id is not None
            )

            # Determine message key based on results
            message_key = None
            if conflicts_count > 0:
                message_key = (
                    "bulk_rename_conflicts"
                    if conflicts_count == len(failed_renames)
                    else "bulk_rename_mixed_errors"
                )
            elif len(failed_renames) > 0:
                message_key = "bulk_rename_errors"
            else:
                message_key = "bulk_rename_success"

            return BulkRenameResponse(
                project_name=project_name,
                total_files=len(renames),
                successful_renames=len(successful_renames),
                failed_renames=len(failed_renames),
                results=successful_renames + failed_renames,
                committed=len(successful_renames) > 0,
                commit_hash=commit_hash,
                renamed_at=datetime.now().isoformat(),
                message=f"Renamed {len(successful_renames)}/{len(renames)} files successfully",
                conflicts_count=conflicts_count,
                message_key=message_key,
            )

        except Exception as e:
            logger.error(f"Critical error during bulk rename: {e!s}")
            await db.rollback()
            raise RuntimeError(f"Bulk rename failed: {e}") from e

    async def _process_single_bulk_rename(
        self,
        rename_info: dict,
        project_path: Path,
        db: AsyncSession,
        runner: GitCommandRunner,
    ) -> RenameResult:
        """Process a single rename operation within a bulk rename."""
        try:
            elan_id = rename_info.get("elan_id")
            new_filename = rename_info.get("new_filename")

            if not elan_id or not new_filename:
                raise ValueError("Missing elan_id or new_filename")

            # Get current filename
            old_filename = await get_elan_file_name_by_id(db, elan_id)
            if not old_filename:
                raise FileNotFoundError(f"ELAN file with ID {elan_id} not found")

            old_file_path = project_path / "elan_files" / old_filename
            new_file_path = project_path / "elan_files" / new_filename

            # Validate file existence and new name availability
            if not old_file_path.exists():
                raise FileNotFoundError(
                    f"File '{old_filename}' not found in filesystem"
                )

            # Check for conflict: if target filename already exists, get its elan_id
            if new_file_path.exists():
                conflict_elan_id = None
                # Get project_id to find the conflicting file
                project_name = project_path.name
                project_id = await get_project_id_by_name(db, project_name)
                if project_id:
                    conflicting_file = await get_elan_file_by_filename_and_project(
                        db, new_filename, project_id
                    )
                    if conflicting_file:
                        conflict_elan_id = conflicting_file.elan_id

                # Raise custom conflict exception with conflict info
                raise RenameConflictError(
                    f"File '{new_filename}' already exists in project",
                    conflict_elan_id=conflict_elan_id,
                    message_key="rename_file_conflict",
                )

            # Update database
            await update_elan_file_name(db, elan_id, new_filename)

            # Rename file
            old_file_path.rename(new_file_path)

            # Stage for git
            runner.add_all()

            return RenameResult(
                old_filename=old_filename,
                new_filename=new_filename,
                success=True,
                error=None,
            )

        except RenameConflictError as e:
            logger.warning(
                f"Rename conflict for elan_id {rename_info.get('elan_id')}: {e!s}"
            )

            # Try to get old filename for error reporting
            old_filename = ""
            try:
                if rename_info.get("elan_id"):
                    old_filename = (
                        await get_elan_file_name_by_id(db, rename_info.get("elan_id"))
                        or ""
                    )
            except Exception:
                logger.warning(
                    f"Could not get filename for elan_id {rename_info.get('elan_id')}"
                )

            return RenameResult(
                old_filename=old_filename,
                new_filename=rename_info.get("new_filename", ""),
                success=False,
                error=str(e),
                conflict_elan_id=e.conflict_elan_id,
                message_key=e.message_key,
            )

        except Exception as e:
            logger.error(
                f"Failed to rename file with elan_id {rename_info.get('elan_id')}: {e!s}"
            )

            # Try to get old filename for error reporting
            old_filename = ""
            try:
                if rename_info.get("elan_id"):
                    old_filename = (
                        await get_elan_file_name_by_id(db, rename_info.get("elan_id"))
                        or ""
                    )
            except Exception:
                logger.warning(
                    f"Could not get filename for elan_id {rename_info.get('elan_id')}"
                )

            return RenameResult(
                old_filename=old_filename,
                new_filename=rename_info.get("new_filename", ""),
                success=False,
                error=str(e),
            )

    async def _finalize_bulk_rename(
        self, successful_renames: list, runner: GitCommandRunner, db: AsyncSession
    ) -> str | None:
        """Finalize the bulk rename operation by committing or rolling back."""
        commit_hash = None
        if successful_renames:
            commit_message = f"Bulk rename: {len(successful_renames)} files"
            commit_hash = runner.commit(commit_message)
            await db.commit()
            logger.info(
                f"Successfully completed bulk rename of {len(successful_renames)} files"
            )
        else:
            await db.rollback()
            logger.warning("No files were successfully renamed")

        return commit_hash
