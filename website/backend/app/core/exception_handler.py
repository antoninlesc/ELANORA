import os
import uuid

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.status import HTTP_400_BAD_REQUEST

from core.logging import get_rotating_logger

# Try to import config, but don't fail if it's not available
try:
    from core.config import EXCEPTION_LOG_DIR, EXCEPTION_LOG_LEVEL

    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


def get_exception_logger(logger_name: str, log_filename: str):
    """Get a logger for exception handling with consistent configuration."""
    # Use config if available, fallback to environment variables
    if HAS_CONFIG:
        log_dir = EXCEPTION_LOG_DIR
        level = EXCEPTION_LOG_LEVEL
    else:
        log_dir = os.getenv("EXCEPTION_LOG_DIR", "app/logs/exceptions")
        level = os.getenv("EXCEPTION_LOG_LEVEL", "WARNING")

    return get_rotating_logger(
        logger_name=f"elanora.exceptions.{logger_name}",
        log_dir=log_dir,
        log_filename=log_filename,
        level=level,
    )


def get_client_info(request: Request) -> dict:
    """Extract client information from request for logging."""
    return {
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "method": request.method,
        "path": request.url.path,
        "query": str(request.query_params) if request.query_params else None,
        "correlation_id": getattr(request.state, "correlation_id", str(uuid.uuid4())),
    }


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle validation errors raised by FastAPI and returns a JSON response with error details."""
    if isinstance(exc, RequestValidationError):
        validation_logger = get_exception_logger("validation", "validation.log")
        client_info = get_client_info(request)

        # Log with structured information
        validation_logger.error(
            "Validation error occurred",
            extra={
                "event_type": "validation_error",
                "client_ip": client_info["client_ip"],
                "user_agent": client_info["user_agent"],
                "method": client_info["method"],
                "path": client_info["path"],
                "query": client_info["query"],
                "correlation_id": client_info["correlation_id"],
                "validation_errors": exc.errors(),
                "error_count": len(exc.errors()),
            },
        )

        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={
                "detail": "Invalid request data.",
                "correlation_id": client_info["correlation_id"],
            },
        )
    raise exc


async def rate_limit_exception_handler(request: Request, exc: Exception) -> Response:
    """Handle rate limit exceptions and log details before delegating to the default handler."""
    if isinstance(exc, RateLimitExceeded):
        rate_limit_logger = get_exception_logger("rate_limit", "rate_limit.log")
        client_info = get_client_info(request)

        # Log with structured information
        rate_limit_logger.warning(
            "Rate limit exceeded",
            extra={
                "event_type": "rate_limit_exceeded",
                "client_ip": client_info["client_ip"],
                "user_agent": client_info["user_agent"],
                "method": client_info["method"],
                "path": client_info["path"],
                "query": client_info["query"],
                "correlation_id": client_info["correlation_id"],
                "rate_limit_detail": str(exc),
            },
        )

        return _rate_limit_exceeded_handler(request, exc)
    raise exc


def add_general_exception_handler():
    """Create a general exception handler for unexpected errors."""
    general_logger = get_exception_logger("general", "general.log")

    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions with proper logging."""
        client_info = get_client_info(request)

        general_logger.error(
            "Unexpected error occurred",
            extra={
                "event_type": "unexpected_error",
                "client_ip": client_info["client_ip"],
                "user_agent": client_info["user_agent"],
                "method": client_info["method"],
                "path": client_info["path"],
                "query": client_info["query"],
                "correlation_id": client_info["correlation_id"],
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
            exc_info=True,  # Include full traceback
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error occurred.",
                "correlation_id": client_info["correlation_id"],
            },
        )

    return general_exception_handler
