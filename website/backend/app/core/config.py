import os

from core.load_env import load_env

# Load environment variables
load_env()

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Mail configuration
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "")

# Get the frontend host from the environment variables
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "http://localhost:3000")
BACKEND_HOST = os.getenv("BACKEND_HOST", "http://localhost:8010")

if not FRONTEND_HOST or not BACKEND_HOST:
    raise ValueError(
        "FRONTEND_HOST and BACKEND_HOST environment variables must be set."
    )


# Get JWT secret key from environment variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Get JWT algorithm from environment variables
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Get JWT expiration times from environment variables
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Cookie name constants
ACCESS_TOKEN_COOKIE_NAME = "elanora_session"  # noqa: S105
REFRESH_TOKEN_COOKIE_NAME = "elanora_refresh"  # noqa: S105
REFRESH_TOKEN_PATH = "/api/v1/auth/refresh"  # noqa: S105
CSRF_TOKEN_NAME = "elanora_csrf"  # noqa: S105

# ELAN Projects configuration
ELAN_PROJECTS_BASE_PATH = os.getenv("ELAN_PROJECTS_BASE_PATH", "projects")
ELAN_MAX_FILE_SIZE_MB = int(os.getenv("ELAN_MAX_FILE_SIZE_MB", "50"))
ELAN_MAX_BATCH_SIZE_MB = int(os.getenv("ELAN_MAX_BATCH_SIZE_MB", "500"))

# Vite configuration
VITE_API_URL = os.getenv("VITE_API_URL", "http://localhost:8010/api/v1")
