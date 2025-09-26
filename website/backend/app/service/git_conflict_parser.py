import re
from pathlib import Path
from typing import Any

from app.core.centralized_logging import get_logger

logger = get_logger()


class GitConflictParser:
    """Parse Git conflict files into efficient structured data."""

    def __init__(self):
        """Initialize the GitConflictParser with conflict marker patterns."""
        self.conflict_marker_pattern = re.compile(r"^<{7} |^={7}$|^>{7} ", re.MULTILINE)

    def parse_conflict_file(
        self, file_path: Path, branch_info: dict[str, str]
    ) -> dict[str, Any]:
        """Parse conflict file efficiently - store only essential data."""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                raw_content = f.read()

            return self._create_efficient_conflict_data(
                raw_content, branch_info, str(file_path)
            )

        except Exception as e:
            logger.error(f"Error parsing conflict file {file_path}: {e}")
            return self._create_fallback_structure(str(file_path), branch_info)

    def _create_efficient_conflict_data(
        self, raw_content: str, branch_info: dict[str, str], filename: str
    ) -> dict[str, Any]:
        """Create efficient conflict data structure - no full file content."""
        lines = raw_content.split("\n")
        conflict_sections = []

        # Parse conflict sections
        current_line = 0
        section_id = 0

        while current_line < len(lines):
            if lines[current_line].startswith("<<<<<<< "):
                conflict_data, end_line = self._parse_conflict_block_efficient(
                    lines, current_line, section_id, branch_info
                )
                if conflict_data:
                    conflict_sections.append(conflict_data)
                    section_id += 1
                current_line = end_line
            else:
                current_line += 1

        # File metadata (lightweight)
        file_stats = self._get_file_stats(raw_content, conflict_sections)

        return {
            "conflict_metadata": {
                "current_branch": branch_info.get("current_branch", "master"),
                "incoming_branch": branch_info.get("incoming_branch", "unknown"),
                "total_conflicts": len(conflict_sections),
                "file_type": self._get_file_type(filename),
                "file_stats": file_stats,
            },
            "merge_data": {
                "conflict_sections": conflict_sections,
                "has_conflicts": len(conflict_sections) > 0,
                "is_resolvable": len(conflict_sections) > 0,
                "resolution_strategies": self._get_resolution_strategies(
                    conflict_sections
                ),
            },
            # Store file path for live content retrieval when needed
            "file_path": filename,
            "content_source": "file_system",  # Indicates content should be read from disk
            "resolution_options": {
                "can_auto_resolve": self._can_auto_resolve_conflicts(conflict_sections),
                "has_binary_conflict": False,  # We only handle text files
                "preview_available": len(conflict_sections) > 0,
                "suggested_strategy": self._suggest_strategy(conflict_sections),
            },
        }

    def _parse_conflict_block_efficient(
        self,
        lines: list[str],
        start_line: int,
        section_id: int,
        branch_info: dict[str, str],
    ) -> tuple:
        """Parse conflict block but store only essential parts."""
        current_lines = []
        incoming_lines = []
        base_lines = []

        line = start_line + 1  # Skip <<<<<<< line

        # Read current content (until =======)
        while line < len(lines) and not lines[line].startswith("======="):
            current_lines.append(lines[line])
            line += 1

        if line >= len(lines):
            return None, line

        line += 1  # Skip ======= line

        # Check for 3-way merge (|||||||)
        if line < len(lines) and lines[line].startswith("||||||| "):
            line += 1  # Skip ||||||| line
            while line < len(lines) and not lines[line].startswith("======="):
                base_lines.append(lines[line])
                line += 1
            line += 1  # Skip second ======= line

        # Read incoming content (until >>>>>>>)
        while line < len(lines) and not lines[line].startswith(">>>>>>> "):
            incoming_lines.append(lines[line])
            line += 1

        end_line = line + 1 if line < len(lines) else line

        # Store only essential content - truncate if too long
        return {
            "section_id": section_id,
            "line_range": {"start": start_line + 1, "end": end_line},
            # Store content excerpts (not full content)
            "current_excerpt": self._create_content_excerpt(current_lines),
            "incoming_excerpt": self._create_content_excerpt(incoming_lines),
            "base_excerpt": self._create_content_excerpt(base_lines)
            if base_lines
            else None,
            # Store metadata about the conflict
            "content_stats": {
                "current_lines": len(current_lines),
                "incoming_lines": len(incoming_lines),
                "base_lines": len(base_lines) if base_lines else 0,
                "current_chars": sum(len(line) for line in current_lines),
                "incoming_chars": sum(len(line) for line in incoming_lines),
            },
            "conflict_type": self._classify_conflict_type(
                current_lines, incoming_lines
            ),
            "complexity": self._assess_complexity(current_lines, incoming_lines),
            "auto_resolvable": self._is_auto_resolvable(current_lines, incoming_lines),
            "suggested_resolution": self._suggest_resolution(
                current_lines, incoming_lines
            ),
            # Context information (just line numbers, not content)
            "context_info": {
                "has_before_context": start_line > 0,
                "has_after_context": end_line < len(lines),
                "context_lines_before": min(3, start_line),
                "context_lines_after": min(3, len(lines) - end_line),
            },
        }, end_line

    def _create_content_excerpt(
        self, lines: list[str], max_lines: int = 10, max_chars: int = 500
    ) -> dict[str, Any]:
        """Create a content excerpt instead of storing full content."""
        if not lines:
            return {"content": "", "is_truncated": False, "total_lines": 0}

        # Truncate if too long
        truncated_lines = lines[:max_lines]
        content = "\n".join(truncated_lines)

        # Truncate by character count if still too long
        if len(content) > max_chars:
            content = content[:max_chars] + "..."
            is_truncated = True
        else:
            is_truncated = len(lines) > max_lines

        return {
            "content": content,
            "is_truncated": is_truncated,
            "total_lines": len(lines),
            "total_chars": sum(len(line) for line in lines),
        }

    def _get_file_stats(
        self, raw_content: str, conflict_sections: list[dict]
    ) -> dict[str, Any]:
        """Get lightweight file statistics."""
        lines = raw_content.split("\n")

        return {
            "total_lines": len(lines),
            "total_chars": len(raw_content),
            "conflict_lines": sum(
                section["line_range"]["end"] - section["line_range"]["start"] + 1
                for section in conflict_sections
            ),
            "clean_lines": len(lines)
            - sum(
                section["line_range"]["end"] - section["line_range"]["start"] + 1
                for section in conflict_sections
            ),
            "has_large_conflicts": any(
                section["content_stats"]["current_lines"] > 20
                or section["content_stats"]["incoming_lines"] > 20
                for section in conflict_sections
            ),
        }

    def _assess_complexity(
        self, current_lines: list[str], incoming_lines: list[str]
    ) -> str:
        """Assess conflict complexity."""
        if len(current_lines) <= 1 and len(incoming_lines) <= 1:
            return "simple"
        elif len(current_lines) <= 5 and len(incoming_lines) <= 5:
            return "moderate"
        else:
            return "complex"

    def _can_auto_resolve_conflicts(self, conflict_sections: list[dict]) -> bool:
        """Check if all conflicts can be auto-resolved."""
        return all(
            section.get("auto_resolvable", False)
            and section.get("complexity") == "simple"
            for section in conflict_sections
        )

    def _suggest_strategy(self, conflict_sections: list[dict]) -> str:
        """Suggest resolution strategy based on conflict analysis."""
        if not conflict_sections:
            return "no_conflicts"

        if (
            len(conflict_sections) == 1
            and conflict_sections[0].get("complexity") == "simple"
        ):
            return "section_by_section"
        elif all(s.get("auto_resolvable") for s in conflict_sections):
            return "auto_resolve"
        else:
            return "manual_review"

    def _get_resolution_strategies(self, conflict_sections: list[dict]) -> list[str]:
        """Get available resolution strategies."""
        strategies = ["accept_current", "accept_incoming", "manual"]

        if conflict_sections:
            strategies.append("section_by_section")

        if self._can_auto_resolve_conflicts(conflict_sections):
            strategies.append("auto_resolve")

        return strategies
