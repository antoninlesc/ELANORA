# Import API routers
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.git import router as git_router
from app.api.v1.tier import router as tier_router
from app.api.v1.user import router as user_router
from app.core.centralized_logging import get_logger
from app.core.config import BACKEND_HOST, ENVIRONMENT, FRONTEND_HOST
from app.core.exception_handler import (
    add_general_exception_handler,
    rate_limit_exception_handler,
    validation_exception_handler,
)
from app.core.limiter import limiter
from app.middleware.csrf import CSRFMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Get logger (this will automatically call setup_application_logging)
logger = get_logger()

app = FastAPI(
    title="ELANORA - ELAN Collaboration Platform",
    description="API for collaborative ELAN annotation projects",
    version="1.0.0",
    # Disable documentation for production
    docs_url="/docs" if ENVIRONMENT != "server" else None,
    redoc_url="/redoc" if ENVIRONMENT != "server" else None,
    openapi_url="/openapi.json" if ENVIRONMENT != "server" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, add_general_exception_handler())

# API version prefix constant
API_V1_PREFIX = "/api/v1"

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_HOST],
    allow_credentials=True,  # Allow cookies (essential for HTTP-only cookies)
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers (including cookies)
)

# Add the CSRF middleware
app.add_middleware(CSRFMiddleware)

# Add your own security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# GZip middleware configuration (for compression)
app.add_middleware(GZipMiddleware, minimum_size=500)

# TrustedHostMiddleware configuration
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[BACKEND_HOST, "localhost", "127.0.0.1"],
)

# Include API routers
app.include_router(git_router, prefix=f"{API_V1_PREFIX}/git", tags=["GIT"])
app.include_router(user_router, prefix=f"{API_V1_PREFIX}/user", tags=["USER"])
app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["AUTHENTICATION"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint for API health check."""
    return {
        "message": "ELANORA API is running",
        "version": "1.0.0",
        "status": "healthy",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
