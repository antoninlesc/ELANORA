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
    list_projects_by_instance,
    list_projects_by_user,
    project_exists_by_name,
)
from app.schema.common.git import FileStatus
from app.schema.responses.git import ProjectInfo, ProjectSyncCheckResponse
from app.service.elan import ElanService
from app.service.git_diff_parser import GitDiffParser
from app.service.git_operations import (
    FileUploadProcessor,
    GitBranchManager,
    GitCommandRunner,
    GitDiffAnalyzer,
    GitMerger,
    delete_project_folder,
)
from app.utils.file_processing import list_untracked_contents
from app.utils.project_backup import (
    create_project_backup_structure,
    remove_project_backup,
    restore_project_backup,
)
from app.utils.project_setup_utils import (
    copy_githooks,
    create_gitignore,
    create_project_structure,
    create_readme,
)

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
        project_name: str,
        files: list[UploadFile],
        db: AsyncSession,
        user_id: int,
        user_name: str = "user",
    ) -> dict[str, Any]:
        """Add multiple ELAN files to the project with branch-based workflow."""
        project_path = self.base_path / project_name
        logger.info(f"Adding {len(files)} ELAN files to project: {project_name}")

        self._validate_upload_request(project_path, files)

        try:
            # Setup Git environment
            self._configure_git_user(project_path, user_name)
            existing_files = self._get_existing_files(project_path, files)

            # Initialize managers
            branch_manager = GitBranchManager(project_path)
            file_processor = FileUploadProcessor(project_path)
            diff_analyzer = GitDiffAnalyzer(project_path)
            merger = GitMerger(project_path)

            # Create branch and process files
            branch_name = branch_manager.create_upload_branch(user_name, len(files))
            uploaded_files, failed_files = await file_processor.process_files(
                files, existing_files
            )

            if not uploaded_files:
                raise RuntimeError("No files were successfully uploaded")

            # Commit and attempt merge
            file_processor.commit_files(uploaded_files, user_name)
            merge_result = await self._attempt_merge(
                branch_manager,
                diff_analyzer,
                merger,
                branch_name,
                db=db,
                user_id=user_id,
                project_path=project_path,
            )

            # Build response
            return self._build_upload_response(
                project_name,
                branch_name,
                uploaded_files,
                failed_files,
                existing_files,
                merge_result,
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
        project_path = self.base_path / project_name
        elan_files_dir = project_path / "elan_files"
        if project_path.exists():
            raise ValueError(f"Project '{project_name}' already exists")
        project_path.mkdir(parents=True, exist_ok=True)
        elan_files_dir.mkdir(parents=True, exist_ok=True)

        # Create README.md and .gitignore
        create_gitignore(project_path)
        create_readme(project_path, project_name)

        # Save only .eaf files, directly in elan_files directory
        for file in files:
            if not file.filename or not file.filename.lower().endswith(".eaf"):
                continue
            dest_path = elan_files_dir / Path(file.filename).name
            async with aiofiles.open(dest_path, "wb") as f:
                await f.write(await file.read())

        runner = GitCommandRunner(project_path)
        runner.init_repo()
        runner.add_all()
        runner.commit("Initial commit from uploaded folder")

        try:
            await create_project_db(
                db=db,
                project_name=project_name,
                description=description,
                project_path=str(project_path),
                instance_id=1,
                creator_user_id=user_id,
            )
            await db.commit()

            elan_service = ElanService(db)
            elan_files = list(elan_files_dir.rglob("*.eaf"))
            for elan_file in elan_files:
                await elan_service.process_single_file(
                    str(elan_file), user_id, project_name
                )
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to initialize project from folder: {e}")
            raise

        return {
            "project_name": project_name,
            "path": str(project_path),
            "status": "initialized",
            "git_initialized": True,
            "created_at": datetime.now().isoformat(),
        }

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
            raise FileNotFoundError("Project not found")
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

    async def _attempt_merge(
        self,
        branch_manager: GitBranchManager,
        diff_analyzer: GitDiffAnalyzer,
        merger: GitMerger,
        branch_name: str,
        db: AsyncSession,
        user_id: int,
        project_path: Path,
    ) -> dict[str, Any]:
        logger.info(f"Attempting to merge branch '{branch_name}' to master branch")
        diff_parser = GitDiffParser()
        branch_manager.switch_to_master()
        analysis = diff_analyzer.analyze_merge_differences(branch_name, diff_parser)
        merge_result = merger.auto_merge_if_safe(branch_name, analysis)

        if merge_result["status"] == "merged_successfully":
            branch_manager.delete_branch(branch_name)
            # --- Sync DB with merged ELAN files ---
            if db and user_id and project_path:
                await self._sync_elan_files_with_db(
                    project_path, db, user_id, project_name=branch_name
                )

        logger.info(f"Merge result: {merge_result['status']}")
        return merge_result

    def _build_upload_response(
        self,
        project_name: str,
        branch_name: str,
        uploaded_files,
        failed_files,
        existing_files: list[str],
        merge_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the upload response."""
        # Determine final status
        if merge_result["status"] == "merged_successfully":
            final_status = "uploaded_and_merged"
        elif merge_result.get("has_conflicts", False):
            final_status = "uploaded_with_conflicts"
        else:
            final_status = "uploaded_pending_review"

        return {
            "project_name": project_name,
            "branch_name": branch_name,
            "uploaded_files": [self._convert_upload_result(f) for f in uploaded_files],
            "failed_files": [self._convert_upload_result(f) for f in failed_files],
            "total_uploaded": len(uploaded_files),
            "total_failed": len(failed_files),
            "existing_files_updated": len(existing_files),
            "new_files_added": len(uploaded_files) - len(existing_files),
            "merge_status": merge_result["status"],
            "has_conflicts": merge_result.get("has_conflicts", False),
            "conflicts": merge_result.get("file_changes", []),
            "new_files_in_merge": merge_result.get("new_files", []),
            "modified_files_in_merge": merge_result.get("modified_files", []),
            "status": final_status,
            "uploaded_at": datetime.now().isoformat(),
            "message": merge_result.get("message", "Batch upload completed"),
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

    async def resolve_conflicts(
        self,
        project_name: str,
        branch_name: str,
        resolution_strategy: str,
        db: AsyncSession,
        user_id: int,
    ) -> dict[str, Any]:
        """Resolve conflicts and merge a branch, then sync ELAN files with DB."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            runner = GitCommandRunner(project_path)
            result = runner.resolve_conflicts(branch_name, resolution_strategy)

            # --- Sync DB with merged ELAN files ---
            await self._sync_elan_files_with_db(project_path, db, user_id, project_name)

            return {
                "project_name": project_name,
                **result,
                "resolved_at": datetime.now().isoformat(),
            }

        except Exception as e:
            raise RuntimeError(f"Failed to resolve conflicts: {e}") from e

    def _configure_git_user(self, project_path: Path, instance_name: str) -> None:
        runner = GitCommandRunner(project_path)
        runner.configure_user(instance_name)

    def _detect_merge_conflicts(self, project_path: Path) -> list[dict[str, str]]:
        """Detect and parse merge conflicts."""
        try:
            # Get files with conflicts
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )

            conflicts = []
            if result.stdout:
                for filename in result.stdout.strip().split("\n"):
                    if filename.strip():
                        # Get conflict details for each file
                        conflict_details = self._get_conflict_details(
                            project_path, filename.strip()
                        )
                        conflicts.append(
                            {
                                "filename": filename.strip(),
                                "type": "content_conflict",
                                "details": conflict_details,
                            }
                        )

            return conflicts

        except subprocess.CalledProcessError:
            return []

    def _get_conflict_details(
        self, project_path: Path, filename: str
    ) -> dict[str, Any]:
        """Get detailed information about a specific conflict."""
        try:
            # Get the conflict markers and content
            file_path = project_path / filename
            if file_path.exists():
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Count conflict markers
                conflict_markers = content.count("<<<<<<< HEAD")

                return {
                    "conflict_markers_count": conflict_markers,
                    "file_size": len(content),
                    "has_binary_conflict": "<<<<<<< HEAD"
                    not in content,  # Binary files won't have text markers
                }

            return {"error": "File not found"}

        except Exception as e:
            return {"error": str(e)}

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

    def _check_for_conflicts(self, project_path: Path) -> list[dict[str, str]]:
        """Check for merge conflicts in the project."""
        return self._detect_merge_conflicts(project_path)

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

    async def list_project_files(self, project_name: str) -> dict[str, Any]:
        """Return a flat list of .eaf files in the elan_files folder for the given project.

        Always from the master branch. Restore the previous branch after listing.
        """
        project_path = self.base_path / project_name
        elan_files_dir = project_path / "elan_files"
        if not elan_files_dir.exists():
            raise FileNotFoundError(
                f"Project '{project_name}' does not have an 'elan_files' directory."
            )

        runner = GitCommandRunner(project_path)

        # Detect current branch
        current_branch = None
        try:
            branches_raw = runner.get_branches()
            for line in branches_raw:
                stripped_line = line.strip()
                if stripped_line.startswith("* "):
                    current_branch = stripped_line[2:]
                    break
        except Exception:
            current_branch = None

        # Checkout master branch before listing files
        runner.checkout("master")

        # Only list .eaf files directly in elan_files (no recursion, no folders)
        eaf_files = [
            {"name": file.name, "type": "file"}
            for file in elan_files_dir.glob("*.eaf")
            if file.is_file()
        ]

        # Restore previous branch if needed
        if current_branch and current_branch != "master":
            try:
                runner.checkout(current_branch)
            except Exception:
                logger.error(
                    f"Failed to restore previous branch '{current_branch}' after listing files."
                )

        return {"files": eaf_files}

    async def synchronize_project(
        self, project_name: str, db: AsyncSession, user_id: int
    ) -> dict:
        """Idempotently synchronize the project's elan_files with the database.

        Only process files that are new, modified, or deleted.
        """
        project_path = self.base_path / project_name
        elan_files_dir = project_path / "elan_files"
        runner = GitCommandRunner(project_path)

        logger.info(f"[SYNC] Starting synchronization for project: {project_name}")
        logger.info(f"[SYNC] Project path: {project_path}")
        logger.info(f"[SYNC] ELAN files directory: {elan_files_dir}")

        # Add all changes to staging area
        logger.info("[SYNC] Adding all changes to staging area...")
        runner.add_all()

        status_output = runner.get_status()
        logger.info(f"[SYNC] git status output:\n{status_output}")

        added_files = []
        modified_files = []
        untracked_files = []
        deleted_files = []

        for entry in self._parse_git_status(status_output):
            code = entry["status"]
            filename = entry["filename"]
            if filename.lower().endswith(".eaf"):
                if code == "A":
                    added_files.append(project_path / filename)
                elif code == "M":
                    modified_files.append(project_path / filename)
                elif code == "??":
                    untracked_files.append(project_path / filename)
                elif code == "D":
                    deleted_files.append(Path(filename).name)

        elan_service = ElanService(db)

        # Add new files
        for file_path in added_files + untracked_files:
            if file_path.exists():
                logger.info(f"[SYNC] Adding new file in DB: {file_path}")
                await elan_service.process_single_file(
                    str(file_path), user_id, project_name
                )

        # Update modified files
        for file_path in modified_files:
            if file_path.exists():
                logger.info(f"[SYNC] Updating modified file in DB: {file_path}")
                await elan_service.process_single_file_and_update(
                    str(file_path), user_id, project_name
                )

        # Remove deleted files
        for filename in deleted_files:
            logger.info(f"[SYNC] Removing deleted file from DB: {filename}")
            await elan_service.delete_elan_files_from_db(filename, project_name)

        if status_output.strip():
            logger.info("[SYNC] Committing changes to git...")
            runner.commit(f"Synchronized project '{project_name}' with ELAN files")
        else:
            logger.info("[SYNC] No changes to commit.")

        logger.info(f"[SYNC] Synchronization complete for project: {project_name}")

        # Return a status/check response
        return ProjectSyncCheckResponse(
            project_name=project_name,
            in_sync=True,
            files_status=[
                FileStatus(
                    filename=str(f), status="updated", description="File updated"
                )
                for f in modified_files
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
        project_path = self.base_path / project_name
        elan_files_dir = project_path / "elan_files"
        git_dir = project_path / ".git"

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
        status_output = runner.get_status()
        files_status = []

        status_map = {"A": "added", "M": "modified", "D": "deleted", "??": "untracked"}

        for entry in self._parse_git_status(status_output):
            code = entry["status"]
            filename = entry["filename"]
            status = status_map.get(code, code)

            # Remove quotes if present
            clean_filename = filename.strip('"').strip("'")

            if code == "??":
                # Only add .eaf files directly in elan_files (no subfolders)
                file_path = Path(clean_filename)
                if (
                    file_path.parent == Path("elan_files")
                    and file_path.suffix.lower() == ".eaf"
                ):
                    files_status.append(
                        FileStatus(
                            filename=file_path.as_posix(),
                            status="untracked",
                            description=f"File {file_path.as_posix()} is untracked",
                        )
                    )
            elif (
                Path(clean_filename).parent == Path("elan_files")
                and Path(clean_filename).suffix.lower() == ".eaf"
            ):
                files_status.append(
                    FileStatus(
                        filename=Path(clean_filename).as_posix(),
                        status=status,
                        description=f"File {Path(clean_filename).as_posix()} is {status}",
                    )
                )

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

    from app.utils.project_backup import restore_project_backup

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
