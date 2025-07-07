from core.config import (
    BACKEND_HOST,
    FRONTEND_HOST,
)
from core.exception_handler import (
    rate_limit_exception_handler,
    validation_exception_handler,
)
from core.limiter import limiter
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from middleware.csrf import CSRFMiddleware
from middleware.security_headers import SecurityHeadersMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# API version prefix constant
API_V1_PREFIX = "/api/v1"

# Add the CSRF middleware
app.add_middleware(CSRFMiddleware)

# Add your own security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_HOST],
    allow_credentials=True,  # Allow cookies (essential for HTTP-only cookies)
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers (including cookies)
)

# GZip middleware configuration (for compression)
app.add_middleware(GZipMiddleware, minimum_size=500)

# TrustedHostMiddleware configuration
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[BACKEND_HOST, "localhost", "127.0.0.1"],
)
