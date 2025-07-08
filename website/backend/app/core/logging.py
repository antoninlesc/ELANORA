import logging
import os
from logging.handlers import RotatingFileHandler

# Constants for default values
DEFAULT_MAX_BYTES = 20 * 1024 * 1024  # 20MB
DEFAULT_BACKUP_COUNT = 5


def get_rotating_logger(
    logger_name: str,
    log_dir: str,
    log_filename: str,
    level: str | None = None,
) -> logging.Logger:
    """Return a logger with a rotating file handler and console handler.

    Args:
        logger_name: Name of the logger
        log_dir: Directory where log files will be stored
        log_filename: Name of the log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance

    """
    # Get log level from environment or use provided/default
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Convert string level to logging constant
    numeric_level = getattr(logging, level, logging.INFO)

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger(logger_name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    logger.setLevel(numeric_level)

    # Create formatter with improved format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(module)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )  # File handler with rotation
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=DEFAULT_MAX_BYTES,
        backupCount=DEFAULT_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    logger.addHandler(file_handler)

    # Console handler (configurable level)
    console_level = os.getenv("CONSOLE_LOG_LEVEL", level).upper()
    console_numeric_level = getattr(logging, console_level, numeric_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(console_numeric_level)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger
