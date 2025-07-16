import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.core.centralized_logging import get_logger
from app.core.config import ELAN_PROJECTS_BASE_PATH
from app.db.database import get_session_maker
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.project import (
    create_project_db,
    delete_project_db,
    list_projects_by_instance,
    project_exists_by_name,
    get_project_by_name,
)
from app.crud.conflicts import save_git_conflicts, get_git_conflicts_for_branch
from app.model.enums import ConflictStatus

from app.service.elan import ElanService
from app.service.git_diff_parser import GitDiffParser
from app.service.git_operations import (
    GitCommandRunner,
    GitBranchManager,
    FileUploadProcessor,
    GitDiffAnalyzer,
    GitMerger,
    delete_project_folder,
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
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)

            runner = GitCommandRunner(project_path)

            # Initialize Git repository
            runner.init_repo()

            # Create project structure
            (project_path / "elan_files").mkdir(exist_ok=True)

            # Create .gitignore to only track .eaf files in elan_files/
            gitignore_content = (
                "*\n!.gitignore\n!README.md\n!elan_files/\n!elan_files/*.eaf\n"
            )
            with open(project_path / ".gitignore", "w", encoding="utf-8") as f:
                f.write(gitignore_content)

            # Create README
            readme_content = self._create_readme(project_name)
            with open(project_path / "README.md", "w", encoding="utf-8") as f:
                f.write(readme_content)

            # Initial commit
            runner.add_all()
            runner.commit("Initial project setup")

            # Paths
            central_githooks = project_path.parent / ".githooks"
            hooks_dir = project_path / ".git" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)

            # Install all hooks found in the central .githooks
            for hook_file in central_githooks.iterdir():
                if hook_file.is_file():
                    hook_name = hook_file.name
                    hook_dest = hooks_dir / hook_name

                    # Read template and substitute variables
                    with open(hook_file, "r", encoding="utf-8") as f:
                        hook_content = f.read()
                    hook_content = (
                        hook_content.replace("{{REPO_NAME}}", project_name)
                        .replace("{{WORK_TREE}}", str(project_path))
                        .replace("{{GIT_DIR}}", str(project_path / ".git"))
                    )
                    with open(hook_dest, "w", encoding="utf-8") as f:
                        f.write(hook_content)
                    os.chmod(hook_dest, 0o775)

            # Save to database
            await create_project_db(
                db=db,
                project_name=project_name,
                description=description,
                project_path=str(project_path),
                instance_id=instance_id,
                creator_user_id=user_id,
            )

            return {
                "project_name": project_name,
                "path": str(project_path),
                "status": "created",
                "git_initialized": True,
                "created_at": datetime.now().isoformat(),
            }

        except Exception as e:
            raise RuntimeError(f"Project creation failed: {e}") from e

    def get_project_status(self, project_name: str) -> dict[str, Any]:
        """Get Git status of a project."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            runner = GitCommandRunner(project_path)

            # Get Git status
            files = self._parse_git_status(runner.get_status())

            # Get recent commits
            commits = self._get_recent_commits(project_path)

            # Check for conflicts
            conflicts = self._check_for_conflicts(project_path)

            return {
                "project_name": project_name,
                "files": files,
                "recent_commits": commits,
                "conflicts": conflicts,
                "status": "ok",
            }

        except Exception as e:
            raise RuntimeError(f"Git status check failed: {e}") from e

    # TODO: error 500 when commiting file that is already in folder projects
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
            self._cleanup_on_error(project_path)
            raise RuntimeError(f"Failed to add ELAN files: {e}") from e
        except Exception as e:
            logger.error(f"Batch file operation failed: {e}")
            raise RuntimeError(f"Failed to add ELAN files: {e}") from e

    async def list_projects(self, db: AsyncSession, instance_id: int) -> list[str]:
        projects = await list_projects_by_instance(db, instance_id)
        return [p.project_name for p in projects]

    async def init_project_from_folder_upload(
        self,
        project_name: str,
        description: str,
        files: list[UploadFile],
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        # 1. Create the project at the usual path
        project_path = self.base_path / project_name
        elan_files_dir = project_path / "elan_files"
        if project_path.exists():
            raise ValueError(f"Project '{project_name}' already exists")
        project_path.mkdir(parents=True, exist_ok=True)
        elan_files_dir.mkdir(parents=True, exist_ok=True)

        # 2. Save only .eaf files, preserving folder structure
        for file in files:
            if not file.filename or not file.filename.lower().endswith(".eaf"):
                continue
            # file.filename is the relative path (e.g., "subfolder/file.eaf")
            dest_path = elan_files_dir / file.filename
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

        # 3. Initialize git repo, commit, and register in DB (reuse your existing logic)
        runner = GitCommandRunner(project_path)
        runner.init_repo()
        runner.add_all()
        runner.commit("Initial commit from uploaded folder")

        await create_project_db(
            db=db,
            project_name=project_name,
            description=description,
            project_path=str(project_path),
            instance_id=1,
            creator_user_id=user_id,
        )

        # 4. Parse and store ELAN files in DB
        elan_service = ElanService(db)
        elan_files = list(elan_files_dir.rglob("*.eaf"))
        for elan_file in elan_files:
            await elan_service.process_single_file(
                str(elan_file), user_id, project_name
            )

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
        elan_files = [f for f in (project_path / "elan_files").glob("*.eaf")]
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

        if (
            merge_result.get("has_conflicts", False)
            or merge_result["status"] == "changes_detected"
        ):
            conflicts = self._extract_conflicts_from_merge_result(
                merge_result, project_path
            )
            if conflicts:
                # Get project_id from project_name
                project = await get_project_by_name(db, project_path.name)
                if project:
                    await save_git_conflicts(
                        db, project.project_id, branch_name, conflicts
                    )
                    logger.info(
                        f"Saved {len(conflicts)} git conflicts for branch {branch_name}"
                    )

        if merge_result["status"] == "merged_successfully":
            branch_manager.delete_branch(branch_name)
            # --- Sync DB with merged ELAN files ---
            if db and user_id and project_path:
                await self._sync_elan_files_with_db(
                    project_path, db, user_id, project_name=branch_name
                )

        logger.info(f"Merge result: {merge_result['status']}")
        return merge_result

    async def get_conflicts(
        self,
        project_name: str,
        branch_name: str,
        db: AsyncSession,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Get git conflicts for a specific branch (hybrid approach)."""
        try:
            # Get project_id from project_name
            project = await get_project_by_name(db, project_name)
            if not project:
                raise FileNotFoundError(f"Project '{project_name}' not found")

            # First, try to get conflicts from database (unless force refresh)
            if not force_refresh:
                db_conflicts = await get_git_conflicts_for_branch(
                    db, project.project_id, branch_name, status=ConflictStatus.DETECTED
                )

                if db_conflicts:
                    # Check if conflicts are recent (less than 1 hour old)
                    latest_conflict = max(db_conflicts, key=lambda c: c.detected_at)
                    age_hours = (
                        datetime.now() - latest_conflict.detected_at
                    ).total_seconds() / 3600

                    if age_hours < 1:  # Use cached conflicts if less than 1 hour old
                        conflicts = []
                        for db_conflict in db_conflicts:
                            conflicts.append(
                                {
                                    "conflict_id": db_conflict.conflict_id,
                                    "filename": db_conflict.filename,
                                    "type": db_conflict.conflict_type.value,
                                    "details": db_conflict.conflict_description,
                                    "git_details": db_conflict.git_details,
                                    "severity": db_conflict.severity.value,
                                    "detected_at": db_conflict.detected_at.isoformat()
                                    if db_conflict.detected_at
                                    else None,
                                }
                            )

                        return {
                            "project_name": project_name,
                            "branch_name": branch_name,
                            "conflicts": conflicts,
                            "has_conflicts": len(conflicts) > 0,
                            "source": "database",
                            "total_conflicts": len(conflicts),
                            "cache_age_hours": round(age_hours, 2),
                        }

            # If no conflicts in database or force refresh, do live detection
            live_result = self._detect_live_conflicts(project_name, branch_name)

            # Update database with fresh conflicts
            if live_result["conflicts"]:
                await save_git_conflicts(
                    db, project.project_id, branch_name, live_result["conflicts"]
                )
                logger.info(
                    f"Updated database with {len(live_result['conflicts'])} fresh git conflicts"
                )

            live_result["source"] = "live_detection"
            return live_result

        except Exception as e:
            logger.error(f"Error getting git conflicts: {e}")
            # Fallback to live detection
            fallback_result = self._detect_live_conflicts(project_name, branch_name)
            fallback_result["source"] = "fallback"
            fallback_result["error"] = str(e)
            return fallback_result

    def _detect_live_conflicts(
        self, project_name: str, branch_name: str
    ) -> dict[str, Any]:
        """Detect conflicts live from git (your existing implementation enhanced)."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            runner = GitCommandRunner(project_path)

            # Store current branch
            current_branch = None
            try:
                branches_raw = runner.get_branches()
                for line in branches_raw:
                    line = line.strip()
                    if line.startswith("* "):
                        current_branch = line[2:]
                        break
            except Exception:
                current_branch = None

            # Switch to master to check differences
            runner.checkout("master")

            # Analyze differences between master and the branch
            diff_analyzer = GitDiffAnalyzer(project_path)
            diff_parser = GitDiffParser()
            analysis = diff_analyzer.analyze_merge_differences(branch_name, diff_parser)

            conflicts = []

            # Check if there are actual merge conflicts by attempting a test merge
            try:
                test_branch = f"test_merge_{branch_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                runner.run(["checkout", "-b", test_branch], check=True)

                merge_result = runner.run(
                    ["merge", branch_name, "--no-commit"], check=False
                )

                if merge_result.returncode != 0:
                    conflicted_files = runner.get_conflicted_files()

                    for filename in conflicted_files:
                        conflict_details = runner.get_conflict_details(filename)
                        conflicts.append(
                            {
                                "filename": filename,
                                "type": "merge_conflict",
                                "details": f"Merge conflict with {conflict_details.get('conflict_markers_count', 0)} conflict markers",
                                "conflict_info": conflict_details,
                            }
                        )

                # Clean up test branch
                runner.checkout("master")
                runner.run(["branch", "-D", test_branch], check=False)

            except Exception as e:
                logger.error(f"Error during conflict detection: {e}")
                # Fallback to analyzing modified files
                for modified_file in analysis.modified_files:
                    conflicts.append(
                        {
                            "filename": modified_file,
                            "type": "content_conflict",
                            "details": f"File modified in branch '{branch_name}' - requires review",
                        }
                    )

            # Restore original branch
            if current_branch and current_branch != "master":
                try:
                    runner.checkout(current_branch)
                except Exception:
                    pass

            return {
                "project_name": project_name,
                "branch_name": branch_name,
                "conflicts": conflicts,
                "has_conflicts": len(conflicts) > 0,
                "new_files": analysis.new_files,
                "modified_files": analysis.modified_files,
                "deleted_files": analysis.deleted_files,
                "total_conflicts": len(conflicts),
            }

        except Exception as e:
            raise RuntimeError(f"Failed to get conflicts: {e}") from e

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
        if hasattr(result, "success"):  # FileUploadResult object
            return {
                "filename": result.filename,
                "size": result.size,
                "existed": result.existed,
            }
        return result  # Already a dict

    def _cleanup_on_error(self, project_path: Path) -> None:
        """Cleanup on error - try to return to master branch."""
        try:
            subprocess.run(
                ["git", "checkout", "master"],
                cwd=project_path,
                check=False,
            )
        except:
            pass

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
                line = line.strip()
                if line.startswith("* "):
                    current_branch = line[2:]
                    branches.append({"name": current_branch, "is_current": True})
                elif line and not line.startswith("remotes/"):
                    branches.append({"name": line, "is_current": False})

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
        for line in status_output.strip().splitlines():
            if not line:
                continue
            status = line[:2].strip()
            filename = line[3:].strip()
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

    async def list_project_files(self, project_name: str) -> Dict[str, Any]:
        """
        Return a tree of .eaf files and folders containing .eaf files for the given project,
        always from the master branch. Restore the previous branch after listing.
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
                line = line.strip()
                if line.startswith("* "):
                    current_branch = line[2:]
                    break
        except Exception:
            current_branch = None

        # Checkout master branch before listing files
        runner.checkout("master")

        def build_tree(path: Path) -> dict | None:
            if path.is_file():
                if path.suffix.lower() == ".eaf":
                    return {"name": path.name, "type": "file"}
                return None
            children = []
            for child in sorted(
                path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
            ):
                subtree = build_tree(child)
                if subtree:
                    children.append(subtree)
            if children:
                return {"name": path.name, "type": "folder", "children": children}
            return None

        tree = build_tree(elan_files_dir)

        # Restore previous branch if needed
        if current_branch and current_branch != "master":
            try:
                runner.checkout(current_branch)
            except Exception:
                pass

        return {"tree": tree}

    async def synchronize_project(
        self, project_name: str, db: AsyncSession, user_id: int
    ):
        """
        - Checkout master branch
        - Add/commit new/changed .eaf files in elan_files/
        - Parse all .eaf files and update the DB
        """
        project_path = self.base_path / project_name
        elan_files_dir = project_path / "elan_files"
        runner = GitCommandRunner(project_path)

        # Work on master branch
        current_branch = None
        try:
            branches_raw = runner.get_branches()
            for line in branches_raw:
                line = line.strip()
                if line.startswith("* "):
                    current_branch = line[2:]
                    break
        except Exception:
            pass
        if current_branch != "master":
            runner.checkout("master")

        # Add and commit new/changed .eaf files
        runner.add_all()
        if runner.get_status().strip():
            runner.commit("Synchronize .eaf files from filesystem")

        elan_service = ElanService(db)
        elan_files = list(elan_files_dir.rglob("*.eaf"))
        for elan_file in elan_files:
            await elan_service.process_single_file(
                str(elan_file), user_id, project_name
            )

        # Restore previous branch
        if current_branch and current_branch != "master":
            try:
                runner.checkout(current_branch)
            except Exception:
                pass

        return (
            f"Synchronized {len(elan_files)} .eaf files for project '{project_name}'."
        )

    async def delete_project(self, project_name: str, db: AsyncSession, user_id: int):
        logger.info(f"Starting deletion of project: {project_name}")
        # Remove all DB artifacts (project, files, annotations, etc.)
        try:
            await delete_project_db(db, project_name)
            logger.info(f"Database records deleted for project: {project_name}")
        except Exception as db_exc:
            logger.error(
                f"Failed to delete project from DB: {project_name} | Error: {db_exc}"
            )
            raise

        # Remove the project folder from disk
        project_path = self.base_path / project_name
        delete_project_folder(project_path)

    async def rename_project(
        self,
        old_project_name: str,
        new_project_name: str,
        db: AsyncSession,
    ) -> dict:
        logger.info(
            f"Starting rename of project: '{old_project_name}' to '{new_project_name}'"
        )
        project = await get_project_by_name(db, old_project_name)
        if not project:
            logger.error(f"Project '{old_project_name}' not found in DB")
            raise ValueError(f"Project '{old_project_name}' not found in DB")

        old_path = Path(self.base_path) / old_project_name
        new_path = Path(self.base_path) / new_project_name
        if not old_path.exists():
            logger.error(f"Project folder '{old_project_name}' not found at {old_path}")
            raise FileNotFoundError(f"Project folder '{old_project_name}' not found")
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
        await db.commit()
        logger.info(
            f"Renamed project in DB: '{old_project_name}' -> '{new_project_name}'"
        )

        return {"new_project_name": new_project_name}

    def _extract_conflicts_from_merge_result(
        self, merge_result: dict, project_path: Path
    ) -> list[dict]:
        """Extract detailed conflict information from merge result."""
        conflicts = []

        # Get conflicts from the merge result
        if "file_changes" in merge_result:
            for change in merge_result["file_changes"]:
                conflict_details = self._get_conflict_details(
                    project_path, change["filename"]
                )
                conflicts.append(
                    {
                        "filename": change["filename"],
                        "type": "merge_conflict",
                        "details": {
                            "change_type": change.get("change_type", "unknown"),
                            "conflict_info": conflict_details,
                            "branch_content": change.get("branch_content", ""),
                            "master_content": change.get("master_content", ""),
                            "additions": change.get("total_additions", 0),
                            "deletions": change.get("total_deletions", 0),
                        },
                    }
                )

        # Also check for actual git conflict markers
        runner = GitCommandRunner(project_path)
        conflicted_files = runner.get_conflicted_files()

        for filename in conflicted_files:
            if not any(c["filename"] == filename for c in conflicts):
                conflict_details = runner.get_conflict_details(filename)
                conflicts.append(
                    {
                        "filename": filename,
                        "type": "content_conflict",
                        "details": conflict_details,
                    }
                )

        return conflicts
