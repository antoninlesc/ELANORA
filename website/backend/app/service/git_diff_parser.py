import re
from typing import Any

from app.core.centralized_logging import get_logger

logger = get_logger()


class GitDiffParser:
    """Parses Git diff output into structured data."""

    def parse_git_diff_output(self, diff_output: str, filename: str) -> dict[str, Any]:
        """Parse git diff output to extract detailed change information."""
        try:
            return self._parse_diff_lines(diff_output, filename)
        except Exception as e:
            logger.error(f"Error parsing git diff: {e}")
            return {
                "filename": filename,
                "added_lines": [],
                "removed_lines": [],
                "modified_sections": [],
                "total_additions": 0,
                "total_deletions": 0,
                "hunks": [],
                "summary": f"Error parsing diff: {e!s}",
                "diff_raw": diff_output,
                "error": str(e),
            }

    def _parse_diff_lines(self, diff_output: str, filename: str) -> dict[str, Any]:
        """Parse the diff line by line."""
        lines = diff_output.split("\n")
        changes = self._initialize_changes_dict(filename, diff_output)

        current_hunk = None
        line_number_old = 0
        line_number_new = 0

        for line in lines:
            if line.startswith("@@"):
                current_hunk, line_number_old, line_number_new = (
                    self._parse_hunk_header(line, changes)
                )
            elif line.startswith("+") and not line.startswith("+++"):
                line_number_new = self._process_addition(
                    line, line_number_new, changes, current_hunk
                )
            elif line.startswith("-") and not line.startswith("---"):
                line_number_old = self._process_deletion(
                    line, line_number_old, changes, current_hunk
                )
            elif line.startswith(" "):
                line_number_old, line_number_new = self._process_context(
                    line, line_number_old, line_number_new, current_hunk
                )

        changes["summary"] = self._create_summary(changes)
        return changes

    def _initialize_changes_dict(self, filename: str, diff_output: str) -> dict:
        """Initialize the changes dictionary."""
        return {
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

    def _parse_hunk_header(self, line: str, changes: dict) -> tuple:
        """Parse hunk header and return hunk info."""
        hunk_match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)", line)
        if hunk_match:
            line_number_old = int(hunk_match.group(1))
            line_number_new = int(hunk_match.group(3))

            current_hunk = {
                "old_start": line_number_old,
                "new_start": line_number_new,
                "old_count": int(hunk_match.group(2)) if hunk_match.group(2) else 1,
                "new_count": int(hunk_match.group(4)) if hunk_match.group(4) else 1,
                "context": hunk_match.group(5).strip() if hunk_match.group(5) else "",
                "changes": [],
            }
            changes["hunks"].append(current_hunk)
            return current_hunk, line_number_old, line_number_new
        return None, 0, 0

    def _process_addition(
        self, line: str, line_number_new: int, changes: dict, current_hunk: dict | None
    ) -> int:
        """Process an added line in the diff."""
        content = line[1:]
        line_number_new += 1
        changes["added_lines"].append(
            {"line_number": line_number_new, "content": content}
        )
        changes["total_additions"] += 1
        if current_hunk is not None:
            current_hunk["changes"].append(
                {"type": "addition", "line_number": line_number_new, "content": content}
            )
        return line_number_new

    def _process_deletion(
        self, line: str, line_number_old: int, changes: dict, current_hunk: dict | None
    ) -> int:
        """Process a deleted line in the diff."""
        content = line[1:]
        line_number_old += 1
        changes["removed_lines"].append(
            {"line_number": line_number_old, "content": content}
        )
        changes["total_deletions"] += 1
        if current_hunk is not None:
            current_hunk["changes"].append(
                {"type": "deletion", "line_number": line_number_old, "content": content}
            )
        return line_number_old

    def _process_context(
        self,
        line: str,
        line_number_old: int,
        line_number_new: int,
        current_hunk: dict | None,
    ) -> tuple[int, int]:
        """Process a context (unchanged) line in the diff."""
        content = line[1:]
        line_number_old += 1
        line_number_new += 1
        if current_hunk is not None:
            current_hunk["changes"].append(
                {
                    "type": "context",
                    "line_number_old": line_number_old,
                    "line_number_new": line_number_new,
                    "content": content,
                }
            )
        return line_number_old, line_number_new

    def _create_summary(self, changes: dict) -> str:
        """Create a summary of the changes."""
        return (
            f"Added {changes['total_additions']} lines, "
            f"removed {changes['total_deletions']} lines."
        )
