import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from fastapi import UploadFile


class GitService:
    """Service for managing Git operations for ELAN projects."""

    def __init__(self, base_path: str = "data/projects") -> None:
        """Initialize the Git service."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def check_git_availability(self) -> Dict[str, Any]:
        """Check if Git is available on the system."""
        try:
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True
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

    def create_project(self, project_name: str) -> Dict[str, Any]:
        """Create a new project with Git repository."""
        project_path = self.base_path / project_name

        if project_path.exists():
            raise ValueError(f"Project '{project_name}' already exists")

        try:
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=project_path, check=True)

            # Create project structure
            (project_path / "elan_files").mkdir(exist_ok=True)
            (project_path / "media").mkdir(exist_ok=True)

            # Create README
            readme_content = self._create_readme(project_name)
            with open(project_path / "README.md", "w", encoding="utf-8") as f:
                f.write(readme_content)

            # Initial commit
            subprocess.run(["git", "add", "."], cwd=project_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial project setup"],
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
            raise RuntimeError(f"Git operation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Project creation failed: {e}")

    def get_project_status(self, project_name: str) -> Dict[str, Any]:
        """Get Git status of a project."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            # Get Git status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
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
            raise RuntimeError(f"Git status check failed: {e}")

    def commit_changes(
        self, project_name: str, commit_message: str, user_name: str = "user"
    ) -> Dict[str, Any]:
        """Commit changes to a project."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            # Check if there are changes to commit
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            if not status_result.stdout.strip():
                raise ValueError("No changes to commit")

            # Add all changes
            subprocess.run(["git", "add", "."], cwd=project_path, check=True)

            # Commit with user info
            full_message = f"{commit_message}\n\nCommitted by: {user_name}"
            subprocess.run(
                ["git", "commit", "-m", full_message], cwd=project_path, check=True
            )

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
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
            raise RuntimeError(f"Commit failed: {e}")

    async def add_elan_file(
        self, project_name: str, file: UploadFile, user_name: str = "user"
    ) -> Dict[str, Any]:
        """Add an ELAN file to the project."""
        project_path = self.base_path / project_name

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")

        try:
            # Get filename
            filename = file.filename
            if not filename:
                raise ValueError("File must have a filename")

            # Save file directly to project
            dest_path = project_path / "elan_files" / filename

            with open(dest_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # Commit the file
            subprocess.run(
                ["git", "add", f"elan_files/{filename}"], cwd=project_path, check=True
            )
            commit_message = f"Add ELAN file: {filename}"
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"{commit_message}\n\nUploaded by: {user_name}",
                ],
                cwd=project_path,
                check=True,
            )

            return {
                "filename": filename,
                "project_name": project_name,
                "status": "added",
                "added_at": datetime.now().isoformat(),
            }

        except Exception as e:
            raise RuntimeError(f"Failed to add ELAN file: {e}")

    def _create_readme(self, project_name: str) -> str:
        """Create README content for a project."""
        return f"""# {project_name}

ELAN Collaboration Project

## Files
- elan_files/ - Your .eaf annotation files
- media/ - Audio/video files

## Usage
Upload your ELAN files through the web interface.
All changes are automatically tracked with Git.

## Created
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    def _parse_git_status(self, status_output: str) -> List[Dict[str, str]]:
        """Parse Git status output."""
        files: List[Dict[str, str]] = []
        if status_output:
            for line in status_output.strip().split("\n"):
                if line.strip():
                    status = line[:2]
                    filename = line[3:]
                    files.append(
                        {
                            "filename": filename,
                            "status": status,
                            "description": self._parse_status_code(status),
                        }
                    )
        return files

    def _parse_status_code(self, status_code: str) -> str:
        """Parse Git status codes."""
        status_map: Dict[str, str] = {
            "M ": "Modified",
            "A ": "Added",
            "D ": "Deleted",
            "R ": "Renamed",
            "??": "Untracked",
            "UU": "Conflict (both modified)",
        }
        return status_map.get(status_code, "Unknown")

    def _get_recent_commits(self, project_path: Path, limit: int = 5) -> List[str]:
        """Get recent commits from a project."""
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", f"-{limit}"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            commits: List[str] = []
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        commits.append(line)
            return commits
        except subprocess.CalledProcessError:
            return []

    def _check_for_conflicts(self, project_path: Path) -> List[str]:
        """Check for merge conflicts in a project."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            conflicts: List[str] = []
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        conflicts.append(line)
            return conflicts
        except subprocess.CalledProcessError:
            return []
