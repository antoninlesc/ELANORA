import logging
import os
from logging.handlers import RotatingFileHandler


def get_rotating_logger(
    logger_name: str,
    log_dir: str,
    log_filename: str,
) -> logging.Logger:
    """Return a logger with a rotating file handler and console handler.

    Build a logger with a rotating file handler and console handler, then return it.
    """
    max_bytes = 20 * 1024 * 1024
    backup_count = 5
    level = logging.INFO

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )

    # Prevent duplicate handlers if called multiple times
    if not any(
        isinstance(h, RotatingFileHandler)
        and getattr(h, "baseFilename", None) == log_path
        for h in logger.handlers
    ):
        file_handler = RotatingFileHandler(
            log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger
