import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.centralized_logging import get_logger
from app.utils.project_backup import create_hidden_folder_in_root, update_backup

logger = get_logger()


@dataclass
class FileUploadResult:
    """Result of uploading a single file."""

    filename: str
    size: int
    existed: bool
    success: bool
    error: str | None = None


class GitBranchManager:
    """Handles Git branch operations."""

    def __init__(self, project_path: Path):
        """Initialize with the project path."""
        self.project_path = project_path
        self.commandRunner = GitCommandRunner(project_path)

    def create_upload_branch(self, user_name: str, file_count: int) -> str:
        """Create a unique branch for file uploads."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"upload_batch_{user_name}_{timestamp}_{file_count}_files"

        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=self.project_path,
            check=True,
        )
        logger.info(f"Created and switched to branch: {branch_name}")
        return branch_name

    def switch_to_master(self) -> None:
        """Switch to master branch."""
        subprocess.run(
            ["git", "checkout", "master"],
            cwd=self.project_path,
            check=True,
        )
        logger.info("Switched to master branch")

    def delete_branch(self, branch_name: str) -> None:
        """Delete a branch."""
        self.commandRunner.delete_branch(branch_name)
        logger.info(f"Deleted branch: {branch_name}")


class FileUploadProcessor:
    """Processes file uploads to Git."""

    def __init__(self, project_path: Path):
        """Initialize with the project path."""
        self.project_path = project_path

    async def process_files(
        self, files, existing_files: list[str]
    ) -> tuple[list[FileUploadResult], list[FileUploadResult]]:
        """Process all uploaded files and return success/failure lists."""
        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                result = await self._process_single_file(file, existing_files)
                uploaded_files.append(result)
                logger.info(f"Added file to Git: {file.filename}")
            except Exception as e:
                failed_result = FileUploadResult(
                    filename=file.filename,
                    size=file.size or 0,
                    existed=file.filename in existing_files,
                    success=False,
                    error=str(e),
                )
                failed_files.append(failed_result)
                logger.error(f"Failed to process file {file.filename}: {e}")

        return uploaded_files, failed_files

    async def _process_single_file(
        self, file, existing_files: list[str]
    ) -> FileUploadResult:
        """Process a single file upload."""
        # Ensure elan_files directory exists
        elan_files_dir = self.project_path / "elan_files"
        elan_files_dir.mkdir(exist_ok=True)

        dest_path = elan_files_dir / file.filename
        logger.debug(f"Processing file: {file.filename} -> {dest_path}")

        # Always save the file - let Git determine if it changed
        content = await file.read()
        with open(dest_path, "wb") as buffer:
            buffer.write(content)

        logger.info(f"File saved: {dest_path} ({len(content)} bytes)")

        # Add to git - Git will handle change detection
        try:
            runner = GitCommandRunner(self.project_path)
            runner.run(["add", f"elan_files/{file.filename}"], check=True)
            logger.debug(f"Git add successful for {file.filename}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Git add failed for {file.filename}: {e}")
            raise RuntimeError(f"Failed to add file to Git: {e}") from e

        return FileUploadResult(
            filename=file.filename,
            size=file.size or 0,
            existed=file.filename in existing_files,
            success=True,
        )

    def commit_files(
        self, uploaded_files: list[FileUploadResult], user_name: str
    ) -> None:
        """Commit all uploaded files with Git's change detection."""
        logger.info(f"Attempting to commit {len(uploaded_files)} files")

        runner = GitCommandRunner(self.project_path)

        # Let Git determine what actually changed
        status_result = runner.run(["status", "--porcelain"])
        staged_files = []

        for line in status_result.stdout.splitlines():
            if line.strip():
                status_code = line[:2]
                filename = line[3:].strip()
                if status_code[0] in ["A", "M", "D"]:  # Staged changes
                    staged_files.append(filename)

        if not staged_files:
            logger.info(
                "No changes detected by Git - all files are identical to existing versions"
            )
            return  # Don't treat this as an error

        logger.info(f"Git detected changes in: {staged_files}")

        # Build commit message based on what Git actually detected
        file_count = len(uploaded_files)
        changed_count = len(staged_files)
        identical_count = file_count - changed_count

        commit_message = f"Batch upload: {file_count} ELAN files"
        if identical_count > 0:
            commit_message += f" ({changed_count} changed, {identical_count} identical)"

        full_message = (
            f"{commit_message}\n\n"
            f"Uploaded by: {user_name}\n"
            f"Files: {', '.join([f.filename for f in uploaded_files])}"
        )

        logger.debug(f"Commit message: {full_message}")

        try:
            runner.run(["commit", "-m", full_message], check=True)
            update_backup(self.project_path.name, self.project_path.parent)
            logger.info(f"Successfully committed {changed_count} changed files")
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stderr:
                logger.info("No changes to commit - all files are identical")
                return  # Success case
            else:
                logger.error(f"Git commit failed: {e.stderr}")
                raise RuntimeError(f"Git commit failed: {e.stderr}") from e


class GitCommandRunner:
    """Runs generic git commands and returns results."""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def run(self, args: list[str], check: bool = False) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self.project_path,
            capture_output=True,
            text=True,
            check=check,
        )

    def get_status(self) -> str:
        return self.run(["status", "--porcelain"]).stdout

    def stage_all_changes(self) -> None:
        """Stage all changes to enable rename detection."""
        self.run(["add", "-A"], check=True)

    def get_status_with_renames(self) -> str:
        """Get status after staging changes to detect renames."""
        self.stage_all_changes()
        return self.get_status()

    def get_log(self, count: int = 5) -> str:
        return self.run(
            ["log", f"-{count}", "--pretty=format:%h|%an|%ad|%s", "--date=iso"]
        ).stdout

    def get_conflicted_files(self) -> list[str]:
        result = self.run(["diff", "--name-only", "--diff-filter=U"])
        return [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]

    def get_conflict_details(self, filename: str) -> dict[str, Any]:
        file_path = self.project_path / filename
        if file_path.exists():
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            conflict_markers = content.count("<<<<<<< HEAD")
            return {
                "conflict_markers_count": conflict_markers,
                "file_size": len(content),
                "has_binary_conflict": "<<<<<<< HEAD" not in content,
            }
        return {"error": "File not found"}

    def configure_user(self, instance_name: str):
        """Configure Git user using the instance name."""
        # Clean the instance name for use in email (lowercase, no spaces)
        safe_name = instance_name.lower().replace(" ", "_")
        email = f"{safe_name}@elanora.local"
        self.run(["config", "user.name", instance_name], check=True)
        self.run(["config", "user.email", email], check=True)
        logger.info(f"Configured Git user: {instance_name} <{email}>")
        update_backup(self.project_path.name, self.project_path.parent)

    def get_branches(self) -> list[str]:
        result = self.run(["branch", "-a"], check=True)
        return result.stdout.strip().split("\n")

    def reset_hard(self, ref: str = "HEAD"):
        self.run(["reset", "--hard", ref], check=True)

    def clean(self, force: bool = True, directories: bool = True):
        args = ["clean"]
        if force:
            args.append("-f")
        if directories:
            args.append("-d")
        self.run(args, check=True)

    def checkout(self, branch: str):
        self.run(["checkout", branch], check=True)

    def add_all(self):
        self.run(["add", "."], check=True)
        update_backup(self.project_path.name, self.project_path.parent)

    def commit(self, message: str):
        self.run(["commit", "-m", message], check=True)
        update_backup(self.project_path.name, self.project_path.parent)

    def push(self, branch: str = "master"):
        self.run(["push", "origin", branch], check=True)
        update_backup(self.project_path.name, self.project_path.parent)

    def get_commit_hash(self) -> str:
        return self.run(["rev-parse", "HEAD"]).stdout.strip()

    def init_repo(self):
        self.run(["init"], check=True)
        update_backup(self.project_path.name, self.project_path.parent)

    def add_file(self, filepath: str):
        self.run(["add", filepath], check=True)
        update_backup(self.project_path.name, self.project_path.parent)

    def merge(self, branch_name: str, message: str, no_ff: bool = True):
        args = ["merge", branch_name]
        if no_ff:
            args.append("--no-ff")
        args += ["-m", message]
        self.run(args, check=True)
        update_backup(self.project_path.name, self.project_path.parent)

    def diff_stat(self, branch_name: str) -> str:
        return self.run(["diff", f"master...{branch_name}", "--stat"]).stdout

    def delete_branch_localy(self, branch_name: str):
        self.run(["branch", "-D", branch_name], check=False)

    def delete_branch_on_remote(self, branch_name: str):
        self.run(["push", "origin", "--delete", branch_name], check=False)

    def delete_branch(self, branch_name: str):
        self.delete_branch_localy(branch_name)
        self.delete_branch_on_remote(branch_name)
        update_backup(self.project_path.name, self.project_path.parent)

    def cleanup_on_error(self, branch_name: str | None = None):
        """Cleanup on error: optionally delete a branch, then checkout master."""
        try:
            if branch_name:
                self.run(["branch", "-D", branch_name], check=False)
            self.run(["checkout", "master"], check=False)
            update_backup(self.project_path.name, self.project_path.parent)
        except Exception:
            logger.exception("Exception occurred during cleanup_on_error")

    def detect_merge_conflicts(self) -> list[dict[str, str]]:
        result = self.run(["diff", "--name-only", "--diff-filter=U"])
        conflicts = []
        if result.stdout:
            for filename in result.stdout.strip().split("\n"):
                if filename.strip():
                    conflict_details = self.get_conflict_details(filename.strip())
                    conflicts.append(
                        {
                            "filename": filename.strip(),
                            "type": "content_conflict",
                            "details": conflict_details,
                        }
                    )
        return conflicts

    def get_current_branch(self) -> str:
        """Get the current branch name."""
        try:
            result = self.run(["branch", "--show-current"])
            return result.stdout.strip()
        except:
            # Fallback method
            try:
                result = self.run(["rev-parse", "--abbrev-ref", "HEAD"])
                return result.stdout.strip()
            except:
                return "master"


def delete_project_folder(project_path: Path) -> None:
    """Delete the project folder and log errors with details."""
    if not project_path.exists():
        logger.warning(f"Project folder does not exist: {project_path}")
        return

    def on_rm_exc(func, path, exc_info):
        import traceback

        exc = (
            exc_info[1]
            if isinstance(exc_info, tuple) and len(exc_info) > 1
            else exc_info
        )
        # Try to remove read-only and retry
        try:
            import os
            import stat

            os.chmod(path, stat.S_IWRITE)
            func(path)
            logger.info(f"Retried and deleted after chmod: {path}")
            return
        except Exception as exc:
            logger.exception(
                f"Exception occurred while retrying delete for {path}: {exc}"
            )
        logger.error(
            f"Failed to delete file or folder during rmtree: {path} | Function: {func.__name__} | Error: {exc}\nTraceback: {''.join(traceback.format_exception(*exc_info)) if isinstance(exc_info, tuple) else str(exc_info)}"
        )

    try:
        shutil.rmtree(project_path, onexc=on_rm_exc)
        logger.info(f"Successfully deleted project folder: {project_path}")
        backup_path = create_hidden_folder_in_root() / project_path.name
        if backup_path.exists():
            shutil.rmtree(backup_path)
            logger.info(f"Deleted backup for project: {project_path.name}")

    except Exception as fs_exc:
        logger.error(
            f"Failed to delete project folder: {project_path} | Error: {fs_exc}"
        )
        raise RuntimeError(
            f"Failed to delete project folder: {project_path} | Error: {fs_exc}"
        )
