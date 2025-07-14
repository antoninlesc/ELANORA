"""Example usage of the centralized logging system.

This file demonstrates different ways to use the centralized logging system
in your ELANORA application.
"""

import os
import sys

# Add the app directory to Python path so we can import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.centralized_logging import get_directory_logger, get_logger

# Method 1: Auto-detection (Recommended)
logger = get_logger()  # Automatically detects module name

# Method 2: Manual module name
custom_logger = get_logger("elanora.examples.custom")

# Method 3: Directory-wide logging
# All files in the 'api' directory can use this same logger
api_logger = get_directory_logger("api", "elanora.api")


def example_function():
    """Demonstrate auto-detected logging."""
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    try:
        # Some operation that might fail
        _ = 10 / 0  # Intentional division by zero for demonstration
    except ZeroDivisionError:
        logger.error("Division by zero occurred", exc_info=True)


def custom_example():
    """Demonstrate custom logger name."""
    custom_logger.info("Using custom logger name")


def api_example():
    """Demonstrate directory-wide logging."""
    api_logger.info("API operation started")
    api_logger.warning("API rate limit approaching")


# Method 4: Structured logging with extra data
def structured_logging_example():
    """Demonstrate structured logging with additional context."""
    logger.info(
        "User action performed",
        extra={
            "user_id": "12345",
            "action": "login",
            "ip_address": "192.168.1.100",
            "success": True,
        },
    )


if __name__ == "__main__":
    example_function()
    custom_example()
    api_example()
    structured_logging_example()
