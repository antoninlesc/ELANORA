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
from app.crud.pending_upload import (
    save_pending_upload,
    get_pending_uploads,
)
from app.crud.project import (
    create_project_db,
    delete_project_db,
    get_project_by_name,
    list_projects_by_instance,
    list_projects_by_user,
    project_exists_by_name,
)
from app.crud.elan_file import get_elan_files_by_project
from app.schema.common.git import FileStatus
from app.schema.responses.git import ProjectInfo, ProjectSyncCheckResponse
from app.service.elan import ElanService
from app.service.git_operations import (
    FileUploadProcessor,
    GitBranchManager,
    GitCommandRunner,
    GitDiffAnalyzer,
    delete_project_folder,
)
from app.utils.file_processing import list_untracked_contents
from app.utils.project_backup import (
    create_project_backup_structure,
    remove_project_backup,
    restore_project_backup,
    rename_project_backup_folder,
)
from app.utils.project_setup_utils import (
    copy_githooks,
    create_gitignore,
    create_project_structure,
    create_readme,
    update_project_githooks,
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
        user_name: str,
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

            # Create branch and process files
            branch_name = branch_manager.create_upload_branch(user_name, len(files))
            uploaded_files, failed_files = await file_processor.process_files(
                files, existing_files
            )

            if not uploaded_files:
                raise RuntimeError("No files were successfully uploaded")

            # Commit
            file_processor.commit_files(uploaded_files, user_name)
            upload_info = await self._save_upload_for_admin_approval(
                branch_manager,
                diff_analyzer,
                branch_name,
                db=db,
                username=user_name,
                project_path=project_path,
            )

            # Build response
            return self._build_upload_response(
                project_name,
                uploaded_files,
                failed_files,
                existing_files,
                upload_info,
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to add ELAN files: {e}") from e
        except Exception as e:
            logger.error(f"Batch file operation failed: {e}")
            raise RuntimeError(f"Failed to add ELAN files: {e}") from e

    async def _save_upload_for_admin_approval(
        self,
        branch_manager: GitBranchManager,
        diff_analyzer: GitDiffAnalyzer,
        branch_name: str,
        db: AsyncSession,
        username: str,
        project_path: Path,
    ) -> dict[str, Any]:
        """Save upload for admin approval instead of attempting immediate merge."""
        logger.info(f"Saving upload branch '{branch_name}' for admin approval")

        # Analyze what was uploaded
        branch_manager.switch_to_master()
        analysis = diff_analyzer.analyze_merge_differences(branch_name)
        logger.info(
            f"Upload analysis - New: {len(analysis.new_files)}, Modified: {len(analysis.modified_files)}, Deleted: {len(analysis.deleted_files)}"
        )

        # Always save for admin approval (no immediate merging)
        approval_branch_name = f"{branch_name}_pending_approval"
        runner = GitCommandRunner(project_path)

        try:
            # Rename upload branch to indicate it's pending approval
            runner.run(["branch", "-m", branch_name, approval_branch_name], check=True)
            logger.info(
                f"Branch renamed to '{approval_branch_name}' for admin approval"
            )

            # Store basic upload info in database for admin review
            upload_info = {
                "status": "pending_admin_approval",
                "has_conflicts": False,  # Unknown until admin tests merge
                "has_differences": len(analysis.modified_files) > 0
                or len(analysis.deleted_files) > 0,
                "requires_approval": True,
                "branch_name": approval_branch_name,
                "original_branch": branch_name,
                "new_files": analysis.new_files,
                "modified_files": analysis.modified_files,
                "deleted_files": analysis.deleted_files,
                "analysis": analysis,
                "message": f"Upload saved for admin approval. {len(analysis.new_files)} new files, {len(analysis.modified_files)} modified files.",
                "pending_approval_since": datetime.now().isoformat(),
                "uploaded_by": username,
            }

            # Save upload info to database for admin dashboard
            await self._save_pending_upload_to_db(
                upload_info, project_path, db, username
            )

            return upload_info

        except Exception as e:
            logger.error(f"Failed to save upload for approval: {e}")
            # Cleanup on error
            try:
                runner.run(["branch", "-D", approval_branch_name], check=False)
            except:
                pass
            raise RuntimeError(f"Failed to save upload for approval: {e}") from e

    async def _save_pending_upload_to_db(
        self, upload_info: dict, project_path: Path, db: AsyncSession, username: str
    ):
        """Save pending upload info to database for admin review."""
        try:
            project = await get_project_by_name(db, project_path.name)
            if project:
                # Create a pending upload record using the existing conflicts table
                # We'll use this as a "pending upload" entry
                upload_record = {
                    "type": "PENDING_UPLOAD",
                    "status": "PENDING_ADMIN_APPROVAL",
                    "upload_data": {
                        "branch_name": upload_info["branch_name"],
                        "original_branch": upload_info["original_branch"],
                        "uploaded_by": username,
                        "new_files_count": len(upload_info["new_files"]),
                        "modified_files_count": len(upload_info["modified_files"]),
                        "deleted_files_count": len(upload_info["deleted_files"]),
                        "new_files": upload_info["new_files"],
                        "modified_files": upload_info["modified_files"],
                        "deleted_files": upload_info["deleted_files"],
                        "pending_since": upload_info["pending_approval_since"],
                        "has_differences": upload_info["has_differences"],
                        "has_conflicts": upload_info["has_conflicts"],
                    },
                    "resolution_info": {
                        "can_auto_resolve": False,
                        "requires_admin_approval": True,
                        "suggested_action": "admin_test_merge",
                        "available_strategies": ["test_merge"],
                    },
                    "detected_at": upload_info["pending_approval_since"],
                }

                # Save to conflicts table as "pending upload"
                await save_pending_upload(
                    db,
                    project.project_id,
                    upload_info["branch_name"],
                    upload_record,
                )

                logger.info(
                    f"Saved pending upload info for admin review: {upload_info['branch_name']}"
                )

        except Exception as e:
            logger.error(f"Failed to save pending upload to DB: {e}")

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

    async def get_pending_uploads_with_status(
        self, project_name: str, db: AsyncSession
    ) -> dict[str, Any]:
        """Get pending uploads and compute their merge readiness in real-time."""
        project_path = self.base_path / project_name
        runner = GitCommandRunner(project_path)

        # Get pending uploads from DB
        project = await get_project_by_name(db, project_name)
        pending_uploads = await get_pending_uploads(db, project.project_id)

        upload_status = []
        ready_count = 0
        conflicts_count = 0

        for upload in pending_uploads:
            branch_name = upload.branch_name

            # Test merge in real-time to check status
            try:
                runner.checkout("master")
                merge_test = runner.run(
                    ["merge", "--no-commit", "--no-ff", branch_name], check=False
                )

                if merge_test.returncode == 0:
                    # Clean merge - ready to go
                    runner.run(["merge", "--abort"], check=False)
                    status = "ready_to_merge"
                    conflicts = []
                    ready_count += 1
                else:
                    # Has conflicts - get details
                    conflicted_files = runner.get_conflicted_files()
                    runner.run(["merge", "--abort"], check=False)
                    status = "needs_resolution"
                    conflicts = conflicted_files
                    conflicts_count += 1

                upload_data = upload.git_details.get("upload_data")

                upload_status.append(
                    {
                        "upload_id": upload.upload_id
                        if hasattr(upload, "upload_id")
                        else upload.get("upload_id"),
                        "branch_name": branch_name,
                        "original_branch": upload_data.get(
                            "original_branch",
                            branch_name.replace("_pending_approval", ""),
                        ),
                        "upload_type": upload.upload_type.value
                        if hasattr(upload, "upload_type")
                        else upload.get("upload_type", "pending_upload"),
                        "description": upload.upload_description
                        if hasattr(upload, "upload_description")
                        else upload.get("description", ""),
                        "status": upload.status.value
                        if hasattr(upload, "status")
                        else upload.get("status", "pending_admin_approval"),
                        "uploaded_at": upload.detected_at.isoformat()
                        if hasattr(upload, "detected_at") and upload.detected_at
                        else upload.get("uploaded_at"),
                        "uploaded_by": upload_data.get("uploaded_by"),
                        "merge_status": status,
                        "conflicted_files": conflicts,
                        "conflicted_files_count": len(conflicts),
                        "tested_at": datetime.now().isoformat(),
                    }
                )

            except Exception as e:
                upload_status.append(
                    {
                        "upload_id": upload.upload_id
                        if hasattr(upload, "upload_id")
                        else upload.get("upload_id"),
                        "branch_name": branch_name,
                        "original_branch": upload_data.get(
                            "original_branch",
                            branch_name.replace("_pending_approval", ""),
                        ),
                        "upload_type": upload.upload_type.value
                        if hasattr(upload, "upload_type")
                        else upload.get("upload_type", "pending_upload"),
                        "description": upload.upload_description
                        if hasattr(upload, "upload_description")
                        else upload.get("description", ""),
                        "status": upload.status.value
                        if hasattr(upload, "status")
                        else upload.get("status", "pending_admin_approval"),
                        "uploaded_at": upload.detected_at.isoformat()
                        if hasattr(upload, "detected_at") and upload.detected_at
                        else upload.get("uploaded_at"),
                        "uploaded_by": None,
                        "merge_status": "error",
                        "error": str(e),
                        "can_auto_merge": False,
                    }
                )

        return {
            "project_name": project_name,
            "pending_uploads": upload_status,
            "total_pending": len(upload_status),
            "ready_count": ready_count,
            "conflicts_count": conflicts_count,
        }

    def _build_upload_response(
        self,
        project_name: str,
        uploaded_files,
        failed_files,
        existing_files: list[str],
        upload_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the upload response for the admin approval workflow."""
        return {
            "project_name": project_name,
            "branch_name": upload_info.get("branch_name"),  # Use approval branch name
            "uploaded_files": [self._convert_upload_result(f) for f in uploaded_files],
            "failed_files": [self._convert_upload_result(f) for f in failed_files],
            "total_uploaded": len(uploaded_files),
            "total_failed": len(failed_files),
            "existing_files_updated": len(existing_files),
            "new_files_added": len(uploaded_files) - len(existing_files),
            # Workflow status
            "status": upload_info["status"],  # "pending_admin_approval"
            "requires_approval": upload_info.get("requires_approval", True),
            "has_differences": upload_info.get("has_differences", False),
            # Upload summary
            "upload_summary": {
                "new_files": upload_info.get("new_files", []),
                "modified_files": upload_info.get("modified_files", []),
                "deleted_files": upload_info.get("deleted_files", []),
            },
            # Admin workflow info
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

    async def list_project_files(self, project_name: str, db: AsyncSession) -> dict[str, Any]:
        """Return enriched .eaf files for the project using CRUD."""
        project = await get_project_by_name(db, project_name)
        if not project:
            raise ValueError(f"Project '{project_name}' not found.")

        # Use CRUD to get files with user info
        db_files = await get_elan_files_by_project(db, project.project_id)
        enriched_files = []
        for elan_file, username in db_files:
            file_path = Path(elan_file.file_path)
            if file_path.exists():
                last_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                enriched_files.append({
                    "name": elan_file.filename,
                    "size": elan_file.file_size,
                    "lastModified": last_modified,
                    "lastUpdatedBy": username or "N/A",
                    "type": "file"
                })
            else:
                enriched_files.append({
                    "name": elan_file.filename,
                    "size": elan_file.file_size,
                    "lastModified": "N/A",
                    "lastUpdatedBy": username or "N/A",
                    "type": "file"
                })

        return {"files": enriched_files}

    async def synchronize_project(
        self, project_name: str, db: AsyncSession, user_id: int
    ) -> dict:
        """Idempotently synchronize the project's elan_files with the database."""
        project_path = self.base_path / project_name
        runner = GitCommandRunner(project_path)

        logger.info(f"[SYNC] Starting synchronization for project: {project_name}")

        # Add all changes to staging area
        runner.add_all()

        # Use the sync check logic to get file statuses
        sync_check = self.synchronize_project_check(project_name)
        files_status = sync_check["files_status"]

        elan_service = ElanService(db)
        updated_files = []
        deleted_files = []

        for file_info in files_status:
            filename = file_info["filename"]
            status = file_info["status"]
            file_path = project_path / filename
            if status in {"added", "untracked"}:
                if file_path.exists():
                    logger.info(f"[SYNC] Adding new file in DB: {file_path}")
                    await elan_service.process_single_file(str(file_path), user_id, project_name)
                    updated_files.append(file_path)
            elif status == "modified":
                if file_path.exists():
                    logger.info(f"[SYNC] Updating modified file in DB: {file_path}")
                    await elan_service.process_single_file_and_update(str(file_path), user_id, project_name)
                    updated_files.append(file_path)
            elif status == "deleted":
                logger.info(f"[SYNC] Removing deleted file from DB: {filename}")
                await elan_service.delete_elan_files_from_db(filename, project_name)
                deleted_files.append(filename)

        # Commit changes if any
        status_output = runner.get_status()
        if status_output.strip():
            runner.commit(f"Synchronized project '{project_name}' with ELAN files")

        logger.info(f"[SYNC] Synchronization complete for project: {project_name}")

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
        tracked_files = set()

        for entry in self._parse_git_status(status_output):
            code = entry["status"]
            filename = entry["filename"]
            status = status_map.get(code, code)
            clean_filename = filename.strip('"').strip("'")
            tracked_files.add(clean_filename)
            file_path = Path(clean_filename)
            # Only consider .eaf files directly in elan_files
            if (
                file_path.parent == Path("elan_files")
                and file_path.suffix.lower() == ".eaf"
            ):
                files_status.append(
                    FileStatus(
                        filename=file_path.as_posix(),
                        status=status,
                        description=f"File {file_path.as_posix()} is {status}",
                    )
                )

        # Scan elan_files folder for .eaf files not reported by git
        for file in elan_files_dir.glob("*.eaf"):
            rel_path = Path("elan_files") / file.name
            if rel_path.as_posix() not in tracked_files:
                files_status.append(
                    FileStatus(
                        filename=rel_path.as_posix(),
                        status="untracked",
                        description=f"File {rel_path.as_posix()} is untracked (not reported by git)",
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
