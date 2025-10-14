"""Unified ELAN file validation service.

This module provides comprehensive ELAN file validation with both
basic FastAPI dependency support and advanced health checking capabilities.
"""

import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile

from app.core.centralized_logging import get_logger
from app.core.config import ELAN_MAX_FILE_SIZE_MB, ELAN_MAX_BATCH_SIZE_MB
from app.utils.elan_processor import ElanFileCoordinator

logger = get_logger()


class ElanValidationError(Exception):
    """Custom exception for ELAN validation errors."""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        details: Optional[List[str]] = None,
    ):
        super().__init__(message)
        self.filename = filename
        self.details = details or []


class UnifiedElanValidator:
    """Unified ELAN file validator with comprehensive validation capabilities."""

    # Configuration from environment variables
    MAX_FILE_SIZE = ELAN_MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
    MAX_TOTAL_SIZE = ELAN_MAX_BATCH_SIZE_MB * 1024 * 1024  # Convert MB to bytes
    DANGEROUS_MIME_TYPES = [
        "application/javascript",
        "text/javascript",
        "application/x-executable",
        "application/x-msdownload",
        "text/html",
    ]

    @staticmethod
    def validate_single_file_basic(file: UploadFile) -> None:
        """Basic validation for a single uploaded file.

        Raises:
            HTTPException: If validation fails (for FastAPI compatibility)
        """
        # Check filename
        if not file.filename or not file.filename.lower().endswith(".eaf"):
            raise HTTPException(status_code=400, detail="Only .eaf files are allowed")

        # Check file size
        if file.size and file.size > UnifiedElanValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {ELAN_MAX_FILE_SIZE_MB}MB per file",
            )

        # Check dangerous MIME types
        if (
            file.content_type
            and file.content_type in UnifiedElanValidator.DANGEROUS_MIME_TYPES
        ):
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file.content_type}' is not allowed for security reasons",
            )

    @staticmethod
    def validate_multiple_files_basic(files: List[UploadFile]) -> None:
        """Basic validation for multiple files.

        Raises:
            HTTPException: If validation fails (for FastAPI compatibility)
        """
        if not files:
            raise HTTPException(status_code=400, detail="At least one file is required")

        # Check total size
        total_size = sum(file.size or 0 for file in files)
        if total_size > UnifiedElanValidator.MAX_TOTAL_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Total upload size too large. Maximum is {ELAN_MAX_BATCH_SIZE_MB}MB",
            )

        # Validate each file
        for file in files:
            UnifiedElanValidator.validate_single_file_basic(file)

    @staticmethod
    async def validate_elan_files_comprehensive(
        files: List[UploadFile],
    ) -> Dict[str, Any]:
        """Comprehensive validation with parsing and health checks.

        Returns:
            Dict containing validation results with healthy/unhealthy files

        Raises:
            ElanValidationError: If critical validation fails
        """
        logger.info(f"Starting comprehensive validation of {len(files)} ELAN files")

        validation_results = {
            "healthy_files": [],
            "unhealthy_files": [],
            "total_files": len(files),
            "validation_errors": [],
            "parsed_data": {},  # Store parsed data for healthy files
        }

        for file in files:
            if not file.filename:
                continue

            try:
                # Basic validation first
                UnifiedElanValidator.validate_single_file_basic(file)

                # Reset file position and read content
                await file.seek(0)
                file_content = await file.read()
                await file.seek(0)  # Reset for potential future use

                # Validate content without temp files
                validation_result = await UnifiedElanValidator._validate_file_content(
                    file.filename, file_content
                )

                if validation_result["is_healthy"]:
                    validation_results["healthy_files"].append(file.filename)
                    validation_results["parsed_data"][file.filename] = (
                        validation_result["parsed_data"]
                    )
                    logger.debug(f"✅ {file.filename}: Healthy")
                else:
                    validation_results["unhealthy_files"].append(file.filename)
                    validation_results["validation_errors"].extend(
                        [
                            f"{file.filename}: {error}"
                            for error in validation_result["errors"]
                        ]
                    )
                    logger.warning(
                        f"❌ {file.filename}: Unhealthy - {validation_result['errors']}"
                    )

            except HTTPException as e:
                # Convert HTTPException to validation error
                validation_results["unhealthy_files"].append(file.filename)
                validation_results["validation_errors"].append(
                    f"{file.filename}: {e.detail}"
                )
                logger.error(f"Validation error for {file.filename}: {e.detail}")
            except Exception as e:
                validation_results["unhealthy_files"].append(file.filename)
                validation_results["validation_errors"].append(
                    f"{file.filename}: {str(e)}"
                )
                logger.error(f"Unexpected validation error for {file.filename}: {e}")

        # Check if any files passed validation
        if not validation_results["healthy_files"]:
            raise ElanValidationError(
                "No healthy ELAN files found",
                details=validation_results["validation_errors"],
            )

        logger.info(
            f"Validation complete: {len(validation_results['healthy_files'])} healthy, "
            f"{len(validation_results['unhealthy_files'])} unhealthy"
        )

        return validation_results

    @staticmethod
    async def _validate_file_content(filename: str, content: bytes) -> Dict[str, Any]:
        """Validate ELAN file content without using temporary files.

        Args:
            filename: Name of the file being validated
            content: File content as bytes

        Returns:
            Dict with validation result and parsed data if healthy
        """
        result = {"is_healthy": False, "errors": [], "parsed_data": None}

        try:
            # 1. Basic XML Structure Validation
            try:
                ET.fromstring(content)
            except ET.ParseError as e:
                result["errors"].append(f"Invalid XML structure: {e}")
                return result

            # 2. ELAN Format Validation using in-memory processing
            try:
                # Create temporary file for ElanFileCoordinator (it expects file path)
                temp_path = f"/tmp/elan_validation_{filename}"
                Path(temp_path).parent.mkdir(parents=True, exist_ok=True)

                try:
                    with open(temp_path, "wb") as temp_file:
                        temp_file.write(content)

                    # Use ElanFileCoordinator for comprehensive parsing
                    coordinator = ElanFileCoordinator(temp_path)
                    parsed_data = coordinator.process_complete()

                    # Validate ELAN structure
                    if not UnifiedElanValidator._validate_elan_structure(parsed_data):
                        result["errors"].append(
                            "Invalid ELAN structure: missing required components"
                        )
                        return result

                    # Store parsed data for later use
                    result["parsed_data"] = parsed_data
                    result["is_healthy"] = True

                finally:
                    # Always cleanup temp file
                    Path(temp_path).unlink(missing_ok=True)

            except Exception as e:
                result["errors"].append(f"ELAN parsing failed: {e}")
                return result

        except Exception as e:
            result["errors"].append(f"Unexpected validation error: {e}")
            return result

        return result

    @staticmethod
    def _validate_elan_structure(parsed_data: Dict[str, Any]) -> bool:
        """Validate that parsed ELAN data has required structure.

        Args:
            parsed_data: Output from ElanFileCoordinator.process_complete()

        Returns:
            bool: True if structure is valid
        """
        try:
            # Check required top-level keys
            required_keys = ["file_info", "tiers", "time_slots", "metadata"]
            for key in required_keys:
                if key not in parsed_data:
                    logger.error(f"Missing required key in ELAN data: {key}")
                    return False

            # Validate file_info structure
            file_info = parsed_data["file_info"]
            if not isinstance(file_info, dict) or "filename" not in file_info:
                logger.error("Invalid file_info structure")
                return False

            # Validate tiers structure
            tiers = parsed_data["tiers"]
            if not isinstance(tiers, list):
                logger.error("Tiers must be a list")
                return False

            # Validate each tier has required fields
            for tier in tiers:
                if not isinstance(tier, dict):
                    logger.error("Each tier must be a dictionary")
                    return False

                required_tier_fields = ["tier_id", "annotations"]
                for field in required_tier_fields:
                    if field not in tier:
                        logger.error(f"Tier missing required field: {field}")
                        return False

            # Validate time_slots structure
            time_slots = parsed_data["time_slots"]
            if not isinstance(time_slots, dict):
                logger.error("Time slots must be a dictionary")
                return False

            # Validate metadata structure
            metadata = parsed_data["metadata"]
            if not isinstance(metadata, dict):
                logger.error("Metadata must be a dictionary")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating ELAN structure: {e}")
            return False


# FastAPI dependency functions for backward compatibility
def validate_elan_file(file: UploadFile) -> UploadFile:
    """FastAPI dependency for validating single ELAN file."""
    UnifiedElanValidator.validate_single_file_basic(file)
    return file


def validate_multiple_elan_files(files: List[UploadFile]) -> List[UploadFile]:
    """FastAPI dependency for validating multiple ELAN files."""
    UnifiedElanValidator.validate_multiple_files_basic(files)
    return files


async def validate_elan_file_content(file: UploadFile) -> UploadFile:
    """FastAPI dependency for comprehensive ELAN file content validation."""
    try:
        # Read and validate content
        await file.seek(0)
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        validation_result = await UnifiedElanValidator._validate_file_content(
            file.filename or "unknown", content
        )

        if not validation_result["is_healthy"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ELAN file: {'; '.join(validation_result['errors'])}",
            )

        return file

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")


# Service-level functions for comprehensive validation
class ElanFileValidator:
    """High-level interface for ELAN file validation."""

    @staticmethod
    async def validate_files_for_project_init(
        files: List[UploadFile],
    ) -> Dict[str, Any]:
        """Validate ELAN files for project initialization with strict requirements.

        Raises:
            ElanValidationError: If validation fails

        Returns:
            Dict with validation results and parsed data
        """
        if not files:
            raise ElanValidationError("No files provided for validation")

        # Filter to only ELAN files
        elan_files = [
            f for f in files if f.filename and f.filename.lower().endswith(".eaf")
        ]

        if not elan_files:
            raise ElanValidationError("No ELAN files (.eaf) found in uploaded files")

        logger.info(
            f"Validating {len(elan_files)} ELAN files for project initialization"
        )

        # Comprehensive validation
        validation_results = (
            await UnifiedElanValidator.validate_elan_files_comprehensive(elan_files)
        )

        # For project init, we want ALL files to be healthy
        if validation_results["unhealthy_files"]:
            error_msg = (
                f"Project initialization failed: {len(validation_results['unhealthy_files'])} "
                f"unhealthy ELAN files found. All files must be valid."
            )
            raise ElanValidationError(
                error_msg, details=validation_results["validation_errors"]
            )

        logger.info(
            f"All {len(elan_files)} ELAN files are healthy and ready for project initialization"
        )
        return validation_results
