"""Validation utilities for data processing."""

from decimal import Decimal
from typing import Any


class ValidationUtils:
    """Common validation functions."""

    @staticmethod
    def is_valid_string(value: Any, min_length: int = 1) -> bool:
        """Check if value is a valid non-empty string."""
        return isinstance(value, str) and len(value.strip()) >= min_length

    @staticmethod
    def is_valid_time_range(start_time: Decimal, end_time: Decimal) -> bool:
        """Check if time range is valid."""
        return (
            isinstance(start_time, Decimal)
            and isinstance(end_time, Decimal)
            and start_time >= 0
            and end_time >= start_time
        )

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Remove path separators and invalid characters
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, "_")

        return sanitized.strip()

    @staticmethod
    def validate_user_id(user_id: Any) -> int:
        """Validate and convert user ID."""
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("User ID must be a positive integer")
        return user_id
