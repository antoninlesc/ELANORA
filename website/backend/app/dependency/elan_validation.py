import xml.etree.ElementTree as ET
from fastapi import HTTPException, UploadFile
from typing import List


def validate_elan_file(file: UploadFile) -> UploadFile:
    """
    Validate uploaded ELAN file.

    Args:
        file: The uploaded file

    Returns:
        The validated file

    Raises:
        HTTPException: If file validation fails
    """
    # Check file extension
    if not file.filename or not file.filename.endswith(".eaf"):
        raise HTTPException(status_code=400, detail="Only .eaf files are allowed")

    # Check file size (max 50MB per file - generous for ELAN files)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="File too large. Maximum size is 50MB per file"
        )

    # Check MIME type (optional)
    allowed_types = [
        "application/xml",
        "text/xml",
        "application/octet-stream",
        "text/plain",
    ]
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
        )

    return file


def validate_multiple_elan_files(files: List[UploadFile]) -> List[UploadFile]:
    """
    Validate multiple ELAN files with no count limit.

    Args:
        files: List of uploaded files

    Returns:
        List of validated files

    Raises:
        HTTPException: If validation fails
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    # Calculate total size instead of limiting count
    total_size = sum(file.size or 0 for file in files)
    max_total_size = 500 * 1024 * 1024  # 500MB total for batch upload

    if total_size > max_total_size:
        raise HTTPException(
            status_code=400,
            detail=f"Total upload size too large. Maximum is {max_total_size // (1024 * 1024)}MB",
        )

    # Validate each file individually
    validated_files = []
    for file in files:
        validated_files.append(validate_elan_file(file))

    return validated_files


async def validate_elan_file_content(file: UploadFile) -> UploadFile:
    """
    Validate ELAN file content structure (advanced validation).

    Args:
        file: The uploaded file

    Returns:
        The validated file with reset file pointer

    Raises:
        HTTPException: If file content validation fails
    """
    try:
        # Read file content
        content = await file.read()

        # Reset file pointer for later use
        file.file.seek(0)

        # Parse XML
        root = ET.fromstring(content)

        # Check if it's a valid ELAN file
        if root.tag != "ANNOTATION_DOCUMENT":
            raise HTTPException(
                status_code=400,
                detail="Invalid ELAN file: missing ANNOTATION_DOCUMENT root element",
            )

        # Check for required elements
        header = root.find("HEADER")
        if header is None:
            raise HTTPException(
                status_code=400, detail="Invalid ELAN file: missing HEADER element"
            )

        time_order = root.find("TIME_ORDER")
        if time_order is None:
            raise HTTPException(
                status_code=400, detail="Invalid ELAN file: missing TIME_ORDER element"
            )

        return file

    except ET.ParseError:
        raise HTTPException(
            status_code=400, detail="Invalid ELAN file: XML parsing failed"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")
