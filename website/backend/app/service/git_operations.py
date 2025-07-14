import subprocess
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.centralized_logging import get_logger

logger = get_logger()


@dataclass
class FileUploadResult:
    """Result of uploading a single file."""

    filename: str
    size: int
    existed: bool
    success: bool
    error: str | None = None


@dataclass
class MergeAnalysis:
    """Analysis of merge differences."""

    new_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]
    has_conflicts: bool
    file_changes: list[dict] | None = None


class GitBranchManager:
    """Handles Git branch operations."""

    def __init__(self, project_path: Path):
        """Initialize with the project path."""
        self.project_path = project_path

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
        subprocess.run(
            ["git", "branch", "-d", branch_name],
            cwd=self.project_path,
            check=False,
        )
        logger.info(f"Deleted branch: {branch_name}")


class GitDiffAnalyzer:
    """Analyzes Git differences between branches."""

    def __init__(self, project_path: Path):
        """Initialize with the project path."""
        self.project_path = project_path

    def analyze_merge_differences(self, branch_name: str, diff_parser) -> MergeAnalysis:
        """Analyze differences between master and branch."""
        diff_result = subprocess.run(
            ["git", "diff", f"master...{branch_name}", "--name-status"],
            cwd=self.project_path,
            capture_output=True,
            text=True,
            check=False,
        )

        new_files = []
        modified_files = []
        deleted_files = []

        for line in diff_result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    status, filename = parts
                    if status == "A":
                        new_files.append(filename)
                    elif status == "M":
                        modified_files.append(filename)
                    elif status == "D":
                        deleted_files.append(filename)

        has_conflicts = len(modified_files) > 0 or len(deleted_files) > 0
        file_changes = []

        if has_conflicts:
            file_changes = self._get_detailed_changes(
                branch_name, modified_files, diff_parser
            )

        return MergeAnalysis(
            new_files=new_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            has_conflicts=has_conflicts,
            file_changes=file_changes,
        )

    def _get_detailed_changes(
        self, branch_name: str, modified_files: list[str], diff_parser
    ) -> list[dict]:
        """Get detailed changes for modified files."""
        file_changes = []
        for filename in modified_files:
            file_diff_result = subprocess.run(
                ["git", "diff", f"master...{branch_name}", "--", filename],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if file_diff_result.stdout:
                parsed_changes = diff_parser.parse_git_diff_output(
                    file_diff_result.stdout, filename
                )
                file_changes.append(parsed_changes)

        return file_changes


class GitMerger:
    """Handles Git merge operations."""

    def __init__(self, project_path: Path):
        """Initialize with the project path."""
        self.project_path = project_path

    def auto_merge_if_safe(
        self, branch_name: str, analysis: MergeAnalysis
    ) -> dict[str, Any]:
        """Automatically merge if only new files, otherwise return conflict info."""
        if not analysis.has_conflicts:
            return self._perform_auto_merge(branch_name, analysis.new_files)
        else:
            return self._create_conflict_response(branch_name, analysis)

    def _perform_auto_merge(
        self, branch_name: str, new_files: list[str]
    ) -> dict[str, Any]:
        """Perform automatic merge for new files only."""
        subprocess.run(
            [
                "git",
                "merge",
                branch_name,
                "--no-ff",
                "-m",
                f"Merge batch upload branch '{branch_name}' into master - {len(new_files)} new files added",
            ],
            cwd=self.project_path,
            check=True,
        )

        logger.info(f"Successfully merged {len(new_files)} new files")
        return {
            "status": "merged_successfully",
            "has_conflicts": False,
            "has_differences": True,
            "new_files": new_files,
            "modified_files": [],
            "deleted_files": [],
            "message": f"Successfully merged {len(new_files)} new files",
        }

    def _create_conflict_response(
        self, branch_name: str, analysis: MergeAnalysis
    ) -> dict[str, Any]:
        """Create response for conflicts that need review."""
        # Get summary stats
        detailed_diff = subprocess.run(
            ["git", "diff", f"master...{branch_name}", "--stat"],
            cwd=self.project_path,
            capture_output=True,
            text=True,
            check=False,
        )

        logger.warning(
            f"Conflicts detected - modified files: {analysis.modified_files}"
        )
        return {
            "status": "changes_detected",
            "has_conflicts": True,
            "has_differences": True,
            "new_files": analysis.new_files,
            "modified_files": analysis.modified_files,
            "deleted_files": analysis.deleted_files,
            "diff_summary": detailed_diff.stdout,
            "file_changes": analysis.file_changes,
            "branch_name": branch_name,
            "message": f"Conflicts detected - {len(analysis.modified_files)} modified files require review",
        }


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
        dest_path = self.project_path / "elan_files" / file.filename

        # Save file
        with open(dest_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Add to git
        subprocess.run(
            ["git", "add", f"elan_files/{file.filename}"],
            cwd=self.project_path,
            check=True,
        )

        return FileUploadResult(
            filename=file.filename,
            size=file.size or 0,
            existed=file.filename in existing_files,
            success=True,
        )

    def commit_files(
        self, uploaded_files: list[FileUploadResult], user_name: str
    ) -> None:
        """Commit all uploaded files."""
        file_count = len(uploaded_files)
        existing_count = sum(1 for f in uploaded_files if f.existed)
        new_count = file_count - existing_count

        commit_message = f"Batch upload: {file_count} ELAN files"
        if existing_count > 0:
            commit_message += f" ({existing_count} updated, {new_count} new)"

        full_message = (
            f"{commit_message}\n\n"
            f"Uploaded by: {user_name}\n"
            f"Files: {', '.join([f.filename for f in uploaded_files])}"
        )

        subprocess.run(
            ["git", "commit", "-m", full_message],
            cwd=self.project_path,
            check=True,
        )
        logger.info(f"Committed {file_count} files to Git")


class GitCommandRunner:
    """Runs generic git commands and returns results."""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def run(self, args: list[str], check: bool = False) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + args,
            cwd=self.project_path,
            capture_output=True,
            text=True,
            check=check,
        )

    def get_status(self) -> str:
        return self.run(["status", "--porcelain"]).stdout

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

    def get_branches(self) -> list[str]:
        result = self.run(["branch", "-a"], check=True)
        return result.stdout.strip().split("\n")

    def checkout(self, branch: str):
        self.run(["checkout", branch], check=True)

    def add_all(self):
        self.run(["add", "."], check=True)

    def commit(self, message: str):
        self.run(["commit", "-m", message], check=True)

    def get_commit_hash(self) -> str:
        return self.run(["rev-parse", "HEAD"]).stdout.strip()

    def init_repo(self):
        self.run(["init"], check=True)

    def add_file(self, filepath: str):
        self.run(["add", filepath], check=True)

    def merge(self, branch_name: str, message: str, no_ff: bool = True):
        args = ["merge", branch_name]
        if no_ff:
            args.append("--no-ff")
        args += ["-m", message]
        self.run(args, check=True)

    def diff_stat(self, branch_name: str) -> str:
        return self.run(["diff", f"master...{branch_name}", "--stat"]).stdout

    def delete_branch(self, branch_name: str):
        self.run(["branch", "-d", branch_name], check=False)

    def resolve_conflicts(
        self, branch_name: str, resolution_strategy: str
    ) -> dict[str, Any]:
        self.checkout("master")
        self.run(["merge", branch_name, "--no-ff"], check=False)
        if resolution_strategy == "accept_incoming":
            self.run(["checkout", "--theirs", "."], check=True)
        elif resolution_strategy == "accept_current":
            self.run(["checkout", "--ours", "."], check=True)
        self.run(["add", "."], check=True)
        self.run(
            [
                "commit",
                "-m",
                f"Resolve conflicts from {branch_name} using {resolution_strategy}",
            ],
            check=True,
        )
        self.run(["branch", "-d", branch_name], check=False)
        return {
            "branch_name": branch_name,
            "resolution_strategy": resolution_strategy,
            "status": "resolved",
        }

    def cleanup_on_error(self):
        try:
            self.run(["checkout", "master"], check=False)
        except Exception:
            pass

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
        except Exception:
            pass
        logger.error(
            f"Failed to delete file or folder during rmtree: {path} | Function: {func.__name__} | Error: {exc}\nTraceback: {''.join(traceback.format_exception(*exc_info)) if isinstance(exc_info, tuple) else str(exc_info)}"
        )

    try:
        shutil.rmtree(project_path, onexc=on_rm_exc)
        logger.info(f"Successfully deleted project folder: {project_path}")
    except Exception as fs_exc:
        logger.error(
            f"Failed to delete project folder: {project_path} | Error: {fs_exc}"
        )
        raise RuntimeError(
            f"Failed to delete project folder: {project_path} | Error: {fs_exc}"
        )
