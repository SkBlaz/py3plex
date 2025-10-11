"""
Logging configuration for py3plex.

This module provides centralized logging configuration for the py3plex library.
"""

import logging
from typing import Optional


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a logger for py3plex modules.

    Args:
        name: Logger name. If None, returns the root py3plex logger.
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance

    Example:
        >>> from py3plex.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing network...")
    """
    if name is None:
        name = "py3plex"
    elif not name.startswith("py3plex"):
        name = f"py3plex.{name}"

    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger


def setup_logging(
    level: int = logging.INFO, format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for py3plex with custom settings.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)

    Returns:
        Root py3plex logger

    Example:
        >>> from py3plex.logging_config import setup_logging
        >>> logger = setup_logging(level=logging.DEBUG)
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=level, format=format_string, datefmt="%Y-%m-%d %H:%M:%S")

    logger = logging.getLogger("py3plex")
    return logger
