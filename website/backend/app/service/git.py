import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from core.centralized_logging import get_logger
from core.config import ELAN_PROJECTS_BASE_PATH
from fastapi import UploadFile

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
            website_root = current_file.parent.parent.parent.parent
            self.base_path = website_root / ELAN_PROJECTS_BASE_PATH
            logger.info(f"GitService initialized with base path: {self.base_path}")
        else:
            self.base_path = Path(base_path)

        self.base_path.mkdir(parents=True, exist_ok=True)

    def check_git_availability(self) -> dict[str, Any]:
        """Check if Git is available on the system."""
        try:
            result = subprocess.run(
                [  # noqa: S607,
                    "git",
                    "--version",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
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

    def create_project(self, project_name: str) -> dict[str, Any]:
        """Create a new project with Git repository."""
        project_path = self.base_path / project_name

        if project_path.exists():
            raise ValueError(f"Project '{project_name}' already exists")

        try:
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=project_path, check=True)  # noqa: S607

            # Create project structure
            (project_path / "elan_files").mkdir(exist_ok=True)

            # Create README
            readme_content = self._create_readme(project_name)
            with open(project_path / "README.md", "w", encoding="utf-8") as f:
                f.write(readme_content)

            # Initial commit
            subprocess.run(["git", "add", "."], cwd=project_path, check=True)  # noqa: S607
            subprocess.run(
                ["git", "commit", "-m", "Initial project setup"],  # noqa: S607
                cwd=project_path,
                check=True,
            )

            return {
                "project_name": project_name,
                "path": str(project_path),
                "status": "created",
                "git_initialized": True,
                "created_at": datetime.now().isoformat(),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git operation failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Project creation failed: {e}") from e

    def get_project_status(self, project_name: str) -> dict[str, Any]:
        """Get Git status of a project."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            # Get Git status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],  # noqa: S607
                check=False,
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            # Parse file status
            files = self._parse_git_status(status_result.stdout)

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

        except subprocess.CalledProcessError as e:
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
            # Check if there are changes to commit
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],  # noqa: S607
                check=False,
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            if not status_result.stdout.strip():
                raise ValueError("No changes to commit")

            # Add all changes
            subprocess.run(["git", "add", "."], cwd=project_path, check=True)  # noqa: S607

            # Commit with user info
            full_message = f"{commit_message}\n\nCommitted by: {user_name}"
            subprocess.run(  # noqa: S603
                [  # noqa: S607,
                    "git",
                    "commit",
                    "-m",
                    full_message,
                ],
                cwd=project_path,
                check=True,
            )

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],  # noqa: S607
                check=False,
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            return {
                "project_name": project_name,
                "message": commit_message,
                "commit_hash": hash_result.stdout.strip(),
                "status": "committed",
                "committed_at": datetime.now().isoformat(),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Commit failed: {e}") from e

    async def add_elan_file(
        self, project_name: str, file: UploadFile, user_name: str = "user"
    ) -> dict[str, Any]:
        """Add an ELAN file to the project with branch-based workflow."""
        project_path = self.base_path / project_name
        logger.info(f"Adding ELAN file to project: {project_name}")
        logger.info(f"File details: {file.filename}, size: {file.size}")
        logger.info(f"Project Path: {project_path}")

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            # Configure Git user
            self._configure_git_user(project_path, user_name)

            # Get filename
            filename = file.filename
            if not filename:
                raise ValueError("File must have a filename")

            # Create a unique branch name for this upload
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_name = f"upload_{user_name}_{timestamp}_{filename.replace('.', '_')}"

            # Check if file already exists in main branch
            dest_path = project_path / "elan_files" / filename
            file_exists = dest_path.exists()

            # Always create a new branch for the upload
            subprocess.run(  # noqa: S603
                ["git", "checkout", "-b", branch_name],  # noqa: S607
                cwd=project_path,
                check=True,
            )
            logger.info(f"Switched to new branch: {branch_name}")
            # Save the uploaded file
            with open(dest_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # Add and commit the file in the new branch
            subprocess.run(  # noqa: S603
                ["git", "add", f"elan_files/{filename}"],  # noqa: S607
                cwd=project_path,
                check=True,
            )
            logger.info(f"Added file to Git: {dest_path}")

            commit_message = (
                f"{'Update' if file_exists else 'Add'} ELAN file: {filename}"
            )
            subprocess.run(  # noqa: S603
                [
                    "git",
                    "commit",
                    "-m",
                    f"{commit_message}\n\nUploaded by: {user_name}",
                ],
                cwd=project_path,
                check=True,
            )
            logger.info(f"Committed file to Git: {commit_message}")

            # Try to merge back to main branch
            logger.info(f"Attempting to merge branch '{branch_name}' to main branch")
            merge_result = self._attempt_merge_to_main(
                project_path, branch_name, filename
            )
            logger.info(f"Merge result: {merge_result}")

            return {
                "filename": filename,
                "project_name": project_name,
                "branch_name": branch_name,
                "file_existed": file_exists,
                "merge_status": merge_result["status"],
                "has_conflicts": merge_result["has_conflicts"],
                "conflicts": merge_result.get("conflicts", []),
                "status": "added"
                if not merge_result["has_conflicts"]
                else "conflicts_detected",
                "added_at": datetime.now().isoformat(),
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e}")
            # Try to go back to main branch if something failed
            try:
                subprocess.run(
                    ["git", "checkout", "main"],  # noqa: S607
                    cwd=project_path,
                    check=False,
                )
            except:
                pass
            raise RuntimeError(f"Failed to add ELAN file: {e}") from e
        except Exception as e:
            logger.error(f"File operation failed: {e}")
            raise RuntimeError(f"Failed to add ELAN file: {e}") from e

    def _configure_git_user(
        self, project_path: Path, user_name: str = "ELAN User"
    ) -> None:
        """Configure Git user for the project repository."""
        try:
            # Set user.name
            subprocess.run(  # noqa: S603
                ["git", "config", "user.name", user_name],  # noqa: S607
                cwd=project_path,
                check=True,
            )
            # Set user.email
            subprocess.run(
                ["git", "config", "user.email", "elan@localhost"],  # noqa: S607
                cwd=project_path,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to configure Git user: {e}")

    def _attempt_merge_to_main(
        self, project_path: Path, branch_name: str, filename: str
    ) -> dict[str, Any]:
        """Check for differences before merging using git diff."""
        try:
            # Switch back to main branch
            subprocess.run(
                ["git", "checkout", "master"],  # noqa: S607
                cwd=project_path,
                check=True,
            )
            logger.info("Switched to main branch: master")

            # Check for ANY differences using git diff
            diff_result = subprocess.run(  # noqa: S603
                [
                    "git",
                    "diff",
                    f"master...{branch_name}",
                    "--",
                    f"elan_files/{filename}",
                ],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            logger.info(f"diff_result: {diff_result}")
            logger.info(f"Git diff result: {diff_result.stdout.strip()}")

            if diff_result.stdout.strip():
                # There are differences - parse and return them
                differences = self._parse_git_diff_output(diff_result.stdout, filename)
                logger.info(f"Differences detected in file '{filename}': {differences}")
                return {
                    "status": "changes_detected",
                    "has_conflicts": False,
                    "has_differences": True,
                    "differences": differences,
                    "branch_name": branch_name,
                    "message": "Changes detected - manual review required before merge",
                }
            else:
                logger.info(
                    f"No differences detected in file '{filename}' between branches '{branch_name}' and 'master'."
                )
                # No differences - safe to merge automatically
                logger.info(
                    f"Attempting to merge branch '{branch_name}' into 'master' without conflicts."
                )
                merge_result = subprocess.run(  # noqa: S603
                    [
                        "git",
                        "merge",
                        branch_name,
                        "--no-ff",
                        "-m",
                        f"Merge branch '{branch_name}' into master",
                    ],
                    cwd=project_path,
                    check=True,
                )
                logger.info(f"Merge result: {merge_result}")
                subprocess.run(  # noqa: S603
                    ["git", "branch", "-d", branch_name],  # noqa: S607
                    cwd=project_path,
                    check=False,
                )
                logger.info(f"Deleted branch '{branch_name}' after successful merge.")

                return {
                    "status": "merged_successfully",
                    "has_conflicts": False,
                    "has_differences": False,
                }

        except subprocess.CalledProcessError as e:
            logger.error(f"Merge attempt failed: {e}")
            return {
                "status": "merge_error",
                "has_conflicts": False,
                "error": str(e),
            }

    def _parse_git_diff_output(self, diff_output: str, filename: str) -> dict[str, Any]:
        """Parse git diff output to extract detailed change information."""
        try:
            lines = diff_output.split("\n")
            changes = {
                "filename": filename,
                "added_lines": [],
                "removed_lines": [],
                "modified_sections": [],
                "total_additions": 0,
                "total_deletions": 0,
                "hunks": [],
                "summary": "",
                "diff_raw": diff_output,
            }

            current_hunk = None
            line_number_old = 0
            line_number_new = 0

            for line in lines:
                if line.startswith("@@"):
                    # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                    import re

                    hunk_match = re.match(
                        r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)", line
                    )
                    if hunk_match:
                        line_number_old = int(hunk_match.group(1))
                        line_number_new = int(hunk_match.group(3))

                        current_hunk = {
                            "old_start": line_number_old,
                            "new_start": line_number_new,
                            "old_count": int(hunk_match.group(2))
                            if hunk_match.group(2)
                            else 1,
                            "new_count": int(hunk_match.group(4))
                            if hunk_match.group(4)
                            else 1,
                            "context": hunk_match.group(5).strip()
                            if hunk_match.group(5)
                            else "",
                            "changes": [],
                        }
                        changes["hunks"].append(current_hunk)

                elif line.startswith("+") and not line.startswith("+++"):
                    # Added line
                    change = {
                        "type": "addition",
                        "line_number": line_number_new,
                        "content": line[1:],  # Remove the + prefix
                    }
                    changes["added_lines"].append(change)
                    if current_hunk:
                        current_hunk["changes"].append(change)
                    changes["total_additions"] += 1
                    line_number_new += 1

                elif line.startswith("-") and not line.startswith("---"):
                    # Removed line
                    change = {
                        "type": "deletion",
                        "line_number": line_number_old,
                        "content": line[1:],  # Remove the - prefix
                    }
                    changes["removed_lines"].append(change)
                    if current_hunk:
                        current_hunk["changes"].append(change)
                    changes["total_deletions"] += 1
                    line_number_old += 1

                elif line.startswith(" "):
                    # Context line (unchanged)
                    if current_hunk:
                        current_hunk["changes"].append(
                            {
                                "type": "context",
                                "line_number_old": line_number_old,
                                "line_number_new": line_number_new,
                                "content": line[1:],  # Remove the space prefix
                            }
                        )
                    line_number_old += 1
                    line_number_new += 1

            # Create summary
            if changes["total_additions"] and changes["total_deletions"]:
                changes["summary"] = (
                    f"{changes['total_additions']} additions, {changes['total_deletions']} deletions"
                )
            elif changes["total_additions"]:
                changes["summary"] = f"{changes['total_additions']} additions"
            elif changes["total_deletions"]:
                changes["summary"] = f"{changes['total_deletions']} deletions"
            else:
                changes["summary"] = "No changes"

            return changes

        except Exception as e:
            logger.error(f"Error parsing git diff: {e}")
            return {"error": str(e), "diff_raw": diff_output, "filename": filename}

    def _detect_merge_conflicts(self, project_path: Path) -> list[dict[str, str]]:
        """Detect and parse merge conflicts."""
        try:
            # Get files with conflicts
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],  # noqa: S607
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

    def get_branches(self, project_name: str) -> dict[str, Any]:
        """Get all branches for a project."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            # Get all branches
            result = subprocess.run(
                ["git", "branch", "-a"],  # noqa: S607
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True,
            )

            branches = []
            current_branch = None

            for line in result.stdout.strip().split("\n"):
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

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get branches: {e}") from e

    def resolve_conflicts(
        self,
        project_name: str,
        branch_name: str,
        resolution_strategy: str = "accept_incoming",
    ) -> dict[str, Any]:
        """Resolve conflicts and merge a branch."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            # Switch to main branch
            subprocess.run(
                ["git", "checkout", "main"],  # noqa: S607
                cwd=project_path,
                check=True,
            )

            # Attempt merge again
            subprocess.run(  # noqa: S603
                ["git", "merge", branch_name, "--no-ff"],  # noqa: S607
                cwd=project_path,
                check=False,
            )

            # Apply resolution strategy
            if resolution_strategy == "accept_incoming":
                # Accept all incoming changes
                subprocess.run(
                    ["git", "checkout", "--theirs", "."],  # noqa: S607
                    cwd=project_path,
                    check=True,
                )
            elif resolution_strategy == "accept_current":
                # Keep current version
                subprocess.run(
                    ["git", "checkout", "--ours", "."],  # noqa: S607
                    cwd=project_path,
                    check=True,
                )

            # Add resolved files and commit
            subprocess.run(
                ["git", "add", "."],  # noqa: S607
                cwd=project_path,
                check=True,
            )

            subprocess.run(  # noqa: S603
                [
                    "git",
                    "commit",
                    "-m",
                    f"Resolve conflicts from {branch_name} using {resolution_strategy}",
                ],
                cwd=project_path,
                check=True,
            )

            # Delete the merged branch
            subprocess.run(  # noqa: S603
                ["git", "branch", "-d", branch_name],  # noqa: S607
                cwd=project_path,
                check=False,
            )

            return {
                "project_name": project_name,
                "branch_name": branch_name,
                "resolution_strategy": resolution_strategy,
                "status": "resolved",
                "resolved_at": datetime.now().isoformat(),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to resolve conflicts: {e}") from e
