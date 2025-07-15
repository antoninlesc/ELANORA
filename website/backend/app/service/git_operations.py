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


class GitDiffAnalyzer:
    """Analyzes Git differences between branches."""

    def __init__(self, project_path: Path):
        """Initialize with the project path."""
        self.project_path = project_path

    def analyze_merge_differences(self, branch_name: str, diff_parser) -> MergeAnalysis:
        """Analyze differences between master and branch using Git's diff."""
        logger.info(
            f"Analyzing merge differences for branch '{branch_name}' using Git diff"
        )

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

        logger.debug(f"Git diff output: {diff_result.stdout}")

        for line in diff_result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    status, filename = parts
                    logger.debug(f"Git detected: {status} {filename}")
                    if status == "A":
                        new_files.append(filename)
                    elif status == "M":
                        modified_files.append(filename)
                    elif status == "D":
                        deleted_files.append(filename)

        has_conflicts = len(modified_files) > 0 or len(deleted_files) > 0

        logger.info(
            f"Git diff analysis - New: {len(new_files)}, Modified: {len(modified_files)}, Deleted: {len(deleted_files)}"
        )

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

    def selective_merge_with_conflict_isolation(
        self, branch_name: str, analysis: MergeAnalysis
    ) -> dict[str, Any]:
        """Perform selective merge: auto-merge safe files, isolate conflicts."""
        logger.info(f"Starting selective merge for branch '{branch_name}'")
        logger.info(
            f"Analysis summary - New files: {len(analysis.new_files)}, Modified: {len(analysis.modified_files)}, Deleted: {len(analysis.deleted_files)}"
        )

        if not analysis.has_conflicts:
            logger.info("No conflicts detected, performing auto-merge")
            return self._perform_auto_merge(branch_name, analysis.new_files)

        logger.info("Conflicts detected, proceeding with selective merge strategy")
        # If we have conflicts, perform selective merge
        return self._perform_selective_merge(branch_name, analysis)

    def _perform_selective_merge(
        self, branch_name: str, analysis: MergeAnalysis
    ) -> dict[str, Any]:
        """Merge only non-conflicting files, isolate problematic ones."""
        logger.info(f"Performing selective merge for branch '{branch_name}'")
        runner = GitCommandRunner(self.project_path)

        conflict_branch_name = f"{branch_name}_conflicts"

        try:
            # Start from master and create conflict branch
            runner.checkout("master")
            runner.run(["checkout", "-b", conflict_branch_name], check=True)
            logger.info(f"Created conflict branch '{conflict_branch_name}' from master")

            # Cherry-pick ONLY modified files to conflict branch
            if analysis.modified_files:
                logger.info(
                    f"Adding {len(analysis.modified_files)} modified files to conflict branch"
                )
                for modified_file in analysis.modified_files:
                    try:
                        # Get the modified version from upload branch
                        runner.run(
                            ["checkout", branch_name, "--", modified_file], check=True
                        )
                        logger.debug(f"Added modified file: {modified_file}")
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Could not add {modified_file}: {e}")

                # Commit only the modified files
                runner.add_all()
                runner.commit(f"Modified files from {branch_name} for review")
                logger.info("Successfully created conflict branch with modified files")

            # Switch to upload branch and remove ALL conflicting content
            runner.checkout(branch_name)

            # Remove modified files (reset to master version = remove changes)
            if analysis.modified_files:
                logger.info(
                    f"Resetting {len(analysis.modified_files)} modified files to master version"
                )
                for modified_file in analysis.modified_files:
                    try:
                        runner.run(
                            ["checkout", "master", "--", modified_file], check=True
                        )
                        logger.debug(f"Reset to master: {modified_file}")
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Could not reset {modified_file}: {e}")

            # Handle deleted files (restore them from master)
            if analysis.deleted_files:
                logger.info(
                    f"Restoring {len(analysis.deleted_files)} deleted files from master"
                )
                for deleted_file in analysis.deleted_files:
                    try:
                        runner.run(
                            ["checkout", "master", "--", deleted_file], check=True
                        )
                        logger.debug(f"Restored deleted file: {deleted_file}")
                    except subprocess.CalledProcessError as e:
                        logger.debug(
                            f"Could not restore {deleted_file} (may not exist in master): {e}"
                        )

            # Commit the cleanup (this makes upload branch have only new files)
            if analysis.modified_files or analysis.deleted_files:
                runner.add_all()
                runner.commit("Remove conflicting changes - keep only new files")
                logger.info("Cleaned upload branch to contain only new files")

            # Merge clean upload branch to master
            runner.checkout("master")

            # Check what's actually different (should be only new files now)
            diff_check = runner.run(["diff", "--name-only", f"master...{branch_name}"])
            files_to_merge = [
                f.strip() for f in diff_check.stdout.splitlines() if f.strip()
            ]

            if files_to_merge:
                merge_message = (
                    f"Add {len(files_to_merge)} new files from {branch_name}"
                )
                runner.merge(branch_name, merge_message, no_ff=True)
                logger.info(f"Successfully merged {len(files_to_merge)} new files")
            else:
                logger.info("No new files to merge")

            # Clean up upload branch
            runner.delete_branch(branch_name)

            return {
                "status": "selective_merge_completed",
                "has_conflicts": True,
                "has_differences": True,
                "merged_files": files_to_merge,
                "conflict_files": analysis.modified_files,
                "conflict_branch": conflict_branch_name,
                "deleted_files": analysis.deleted_files,
                "message": f"Merged {len(files_to_merge)} new files. {len(analysis.modified_files)} modified files isolated for review in '{conflict_branch_name}'",
            }

        except Exception as e:
            # Cleanup on error
            try:
                runner.checkout("master")
                runner.run(["branch", "-D", conflict_branch_name], check=False)
                runner.run(["branch", "-D", branch_name], check=False)
            except:
                pass
            raise RuntimeError(f"Selective merge failed: {e}") from e

    def auto_merge_if_safe(
        self, branch_name: str, analysis: MergeAnalysis
    ) -> dict[str, Any]:
        """Automatically merge if only new files, otherwise return conflict info."""
        logger.info(f"Checking if auto-merge is safe for branch '{branch_name}'")

        if not analysis.has_conflicts:
            logger.info("No conflicts detected, proceeding with auto-merge")
            return self._perform_auto_merge(branch_name, analysis.new_files)
        else:
            logger.warning(
                f"Conflicts detected in branch '{branch_name}', returning conflict response"
            )
            return self._create_conflict_response(branch_name, analysis)

    def _perform_auto_merge(
        self, branch_name: str, new_files: list[str]
    ) -> dict[str, Any]:
        """Perform automatic merge for new files only."""
        logger.info(
            f"Performing auto-merge for branch '{branch_name}' with {len(new_files)} new files"
        )

        merge_message = f"Merge batch upload branch '{branch_name}' into master - {len(new_files)} new files added"
        logger.debug(f"Merge message: {merge_message}")

        try:
            subprocess.run(
                [
                    "git",
                    "merge",
                    branch_name,
                    "--no-ff",
                    "-m",
                    merge_message,
                ],
                cwd=self.project_path,
                check=True,
            )
            logger.info(
                f"Successfully auto-merged {len(new_files)} new files from branch '{branch_name}'"
            )

            return {
                "status": "merged_successfully",
                "has_conflicts": False,
                "has_differences": True,
                "new_files": new_files,
                "modified_files": [],
                "deleted_files": [],
                "message": f"Successfully merged {len(new_files)} new files",
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Auto-merge failed for branch '{branch_name}': {e}")
            raise RuntimeError(f"Auto-merge failed: {e}") from e

    def _create_conflict_response(
        self, branch_name: str, analysis: MergeAnalysis
    ) -> dict[str, Any]:
        """Create response for conflicts that need review."""
        logger.info(f"Creating conflict response for branch '{branch_name}'")
        logger.info(
            f"Conflict summary - Modified: {analysis.modified_files}, Deleted: {analysis.deleted_files}"
        )

        # Get summary stats
        try:
            detailed_diff = subprocess.run(
                ["git", "diff", f"master...{branch_name}", "--stat"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            logger.debug(f"Generated diff stats for branch '{branch_name}'")
        except Exception as e:
            logger.error(f"Failed to generate diff stats: {e}")
            detailed_diff = subprocess.CompletedProcess([], 0, "", "")

        logger.warning(
            f"Conflicts detected in branch '{branch_name}' - modified files: {analysis.modified_files}"
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

    def delete_branch_localy(self, branch_name: str):
        self.run(["branch", "-D", branch_name], check=False)

    def delete_branch_on_remote(self, branch_name: str):
        self.run(["push", "origin", "--delete", branch_name], check=False)

    def delete_branch(self, branch_name: str):
        self.delete_branch_localy(branch_name)
        self.delete_branch_on_remote(branch_name)

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
