"""
Logger Service - Centralized logging with rotating file handler.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

try:
    from platformdirs import user_log_dir
except ImportError:
    # Fallback if platformdirs not installed
    def user_log_dir(appname: str, appauthor: str) -> str:
        return str(Path.home() / ".local" / "share" / appname / "logs")


class Logger:
    """Centralized logger with file and console output."""

    _instance: Optional[logging.Logger] = None
    _initialized: bool = False

    @classmethod
    def get_logger(cls, name: str = "py3plex_gui") -> logging.Logger:
        """Get or create the application logger."""
        if cls._instance is None:
            cls._instance = cls._setup_logger(name)
        return cls._instance

    @classmethod
    def _setup_logger(cls, name: str) -> logging.Logger:
        """Set up logger with file and console handlers."""
        if cls._initialized:
            return logging.getLogger(name)

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Create logs directory
        log_dir = Path(user_log_dir("py3plex", "SkBlaz"))
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "gui.log"

        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._initialized = True
        logger.info(f"Logger initialized. Log file: {log_file}")

        return logger


# Convenience functions
def get_logger(name: str = "py3plex_gui") -> logging.Logger:
    """Get the application logger."""
    return Logger.get_logger(name)


def debug(msg: str) -> None:
    """Log debug message."""
    get_logger().debug(msg)


def info(msg: str) -> None:
    """Log info message."""
    get_logger().info(msg)


def warning(msg: str) -> None:
    """Log warning message."""
    get_logger().warning(msg)


def error(msg: str, exc_info: bool = False) -> None:
    """Log error message."""
    get_logger().error(msg, exc_info=exc_info)
