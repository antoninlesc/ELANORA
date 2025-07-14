from lxml import etree as lxml_etree
from app.core.centralized_logging import get_logger
from fastapi import HTTPException, UploadFile

logger = get_logger()


def validate_elan_file(file: UploadFile) -> UploadFile:
    """Validate uploaded ELAN file.

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

    logger.info(f"Debug MIME type for file: {file.filename} - {file.content_type}")

    # Check content type only if it's suspicious, best practice as it allows not-known types of eaf files
    if file.content_type:
        # Block obviously dangerous types
        dangerous_types = [
            "application/javascript",
            "text/javascript",
            "application/x-executable",
            "application/x-msdownload",
            "text/html",
        ]

        if file.content_type in dangerous_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file.content_type}' is not allowed for security reasons",
            )

    return file


def validate_multiple_elan_files(files: list[UploadFile]) -> list[UploadFile]:
    """Validate multiple ELAN files with no count limit.

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
    """Validate ELAN file content structure (advanced validation).

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

        # Parse XML using lxml for security and speed
        parser = lxml_etree.XMLParser(
            resolve_entities=False, no_network=True, recover=True
        )
        root = lxml_etree.fromstring(content, parser=parser)

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

    except lxml_etree.XMLSyntaxError as e:
        raise HTTPException(
            status_code=400, detail="Invalid ELAN file: XML parsing failed"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"File validation failed: {e!s}"
        ) from e
