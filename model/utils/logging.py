"""Logging configuration for PowerBuilder tools.

This module provides structured logging configuration.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def configure_logging(
    *,
    verbose: bool = False,
    log_file: Path | None = None,
    json_format: bool = False,
) -> None:
    """Configure logging for the tools.

    Args:
        verbose: Whether to enable debug logging
        log_file: Optional file to write logs to
        json_format: Whether to output logs in JSON format
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Create formatter
    if json_format:
        formatter = logging.Formatter(
            '{"time":"%(asctime)s", "level":"%(levelname)s", '
            '"logger":"%(name)s", "message":"%(message)s"}',
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if requested
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
