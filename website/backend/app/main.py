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

# Import API routers
from app.api.v1.git import router as git_router

app = FastAPI(
    title="ELANORA - ELAN Collaboration Platform",
    description="API for collaborative ELAN annotation projects",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

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
app.include_router(git_router, prefix=f"{API_V1_PREFIX}/git", tags=["git"])


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
