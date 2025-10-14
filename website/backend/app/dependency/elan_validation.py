"""FastAPI dependencies for ELAN file validation.

This module provides FastAPI dependency functions that use the unified
ELAN validation service for consistent validation across the application.
"""

from typing import List
from fastapi import UploadFile
from app.service.elan_validation_unified import (
    validate_elan_file,
    validate_multiple_elan_files,
    validate_elan_file_content,
)

# Re-export the dependency functions for backward compatibility
__all__ = [
    "validate_elan_file",
    "validate_multiple_elan_files",
    "validate_elan_file_content",
]
