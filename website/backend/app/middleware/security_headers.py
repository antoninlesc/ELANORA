from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds common security headers to HTTP responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process the incoming request and add security headers to the response."""
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
        else:
            # Regular strict CSP for other routes
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        return response