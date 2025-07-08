import os

from core.load_env import load_env

# Load environment variables
load_env()

# Get the frontend host from the environment variables
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "http://localhost:3000")
BACKEND_HOST = os.getenv("BACKEND_HOST", "http://localhost:8010")

if not FRONTEND_HOST or not BACKEND_HOST:
    raise ValueError(
        "FRONTEND_HOST and BACKEND_HOST environment variables must be set."
    )


# Get secret key from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")

# Get JWT algorithm from environment variables
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Get JWT expiration times from environment variables
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CONSOLE_LOG_LEVEL = os.getenv("CONSOLE_LOG_LEVEL", LOG_LEVEL)
ROOT_LOG_LEVEL = os.getenv("ROOT_LOG_LEVEL", "WARNING")
EXCEPTION_LOG_LEVEL = os.getenv("EXCEPTION_LOG_LEVEL", "WARNING")
EXCEPTION_LOG_DIR = os.getenv("EXCEPTION_LOG_DIR", "app/logs/exceptions")
LOG_DIR = os.getenv("LOG_DIR", "app/logs")
APP_NAME = os.getenv("APP_NAME", "elanora")
