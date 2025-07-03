import os

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.status import HTTP_400_BAD_REQUEST

from core.logging import get_rotating_logger

# Logger for validation exceptions
log_dir = os.path.join(os.path.dirname(__file__), "../logs/exception_handlers")
validation_logger = get_rotating_logger(
    logger_name="validation_exception_handler",
    log_dir=log_dir,
    log_filename="validation.log",
)

# Logger for rate limit exceptions
rate_limit_logger = get_rotating_logger(
    logger_name="rate_limit_exception_handler",
    log_dir=log_dir,
    log_filename="rate_limit.log",
)


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle validation errors raised by FastAPI and returns a JSON response with error details."""
    if isinstance(exc, RequestValidationError):
        client_ip = request.client.host if request.client is not None else "unknown"
        path = request.url.path
        validation_logger.warning(
            f"[ValidationError] IP: {client_ip} Path: {path} - Details: {exc.errors()}"
        )
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid request data."},
        )
    raise exc


async def rate_limit_exception_handler(request: Request, exc: Exception) -> Response:
    """Handle rate limit exceptions and log details before delegating to the default handler."""
    if isinstance(exc, RateLimitExceeded):
        client_ip = request.client.host if request.client is not None else "unknown"
        path = request.url.path
        rate_limit_logger.warning(
            f"[RateLimitExceeded] IP: {client_ip} Path: {path} - Details: {exc!s}"
        )
        return _rate_limit_exceeded_handler(request, exc)
    raise exc