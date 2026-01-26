"""XSINT Logging Utilities.

Simple logging utilities for the XSINT application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from kiss.config import get_config


def setup_logger(
    name: str = "xsint", log_level: Optional[str] = None, log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger for XSINT.

    Args:
        name: Logger name
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Determine log level
    if log_level is None:
        try:
            config = get_config()
            log_level = config.log_level
        except Exception:
            log_level = "INFO"

    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        try:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            # If file logging fails, continue with console only
            pass
    else:
        try:
            config = get_config()
            log_file_path = Path(config.logs_dir) / "xsint.log"
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    return logger


def get_logger(name: str = "xsint") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Configure default logger
default_logger = setup_logger()
