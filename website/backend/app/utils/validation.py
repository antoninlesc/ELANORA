"""Validation utilities for data processing."""

from decimal import Decimal
from typing import Any

from app.core.centralized_logging import get_logger

logger = get_logger()


class ValidationUtils:
    """Common validation functions."""

    @staticmethod
    def is_valid_string(value: Any, min_length: int = 1) -> bool:
        result = isinstance(value, str) and len(value.strip()) >= min_length
        logger.debug(
            f"is_valid_string: value='{value}' min_length={min_length} result={result}"
        )
        return result

    @staticmethod
    def is_valid_time_range(start_time: Decimal, end_time: Decimal) -> bool:
        result = (
            isinstance(start_time, Decimal)
            and isinstance(end_time, Decimal)
            and start_time >= 0
            and end_time >= start_time
        )
        logger.debug(
            f"is_valid_time_range: start={start_time} end={end_time} result={result}"
        )
        return result

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        if not filename:
            logger.error("sanitize_filename: empty filename")
            raise ValueError("Filename cannot be empty")
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, "_")
        logger.info(
            f"sanitize_filename: original='{filename}' sanitized='{sanitized.strip()}'"
        )
        return sanitized.strip()

    @staticmethod
    def validate_user_id(user_id: Any) -> int:
        if not isinstance(user_id, int) or user_id <= 0:
            logger.error(f"validate_user_id: invalid user_id={user_id}")
            raise ValueError("User ID must be a positive integer")
        logger.debug(f"validate_user_id: user_id={user_id} is valid")
        return user_id
