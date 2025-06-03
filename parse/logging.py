"""PowerBuilder parser logging configuration.

This module provides logging configuration for the PowerBuilder parser.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from pythonjsonlogger import jsonlogger

# Define logger for the parse package
logger = logging.getLogger("parse")

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_JSON_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(funcName)s %(lineno)d %(pathname)s"

# Log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Module name

    Returns:
        Logger instance
    """
    return logging.getLogger(f"parse.{name}")


def configure_logging(
    log_file: str | Path | None = None,
    log_level: str = "INFO",
    json_format: bool = False,
    log_format: str | None = None,
    include_context: bool = True,
    context: dict[str, str] | None = None,
) -> None:
    """Configure logging for the PowerBuilder parser.

    Args:
        log_file: Optional log file path
        log_level: Log level (default: INFO)
        json_format: Whether to use JSON format (default: False)
        log_format: Custom log format string
        include_context: Whether to include file/line context in logs
        context: Additional context fields to include in all logs
    """
    # Normalize log level
    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)

    # Set up root logger for the parse package
    root_logger = logging.getLogger("parse")
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Determine log format
    if log_format:
        format_str = log_format
    elif json_format:
        format_str = (
            DEFAULT_JSON_FORMAT
            if include_context
            else DEFAULT_JSON_FORMAT.split(" %(filename)s")[0]
        )
    else:
        format_str = DEFAULT_LOG_FORMAT
        if include_context:
            format_str += " (%(filename)s:%(lineno)d)"

    # Create formatter
    if json_format:
        formatter = jsonlogger.JsonFormatter(format_str)
    else:
        formatter = logging.Formatter(format_str)

    # Add console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # Add file handler if specified
    if log_file:
        file_path = Path(log_file)
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Add a filter to include context in all log records
    if context:

        class ContextFilter(logging.Filter):
            def filter(self, record) -> bool:
                for key, value in context.items():
                    setattr(record, key, value)
                return True

        context_filter = ContextFilter()
        root_logger.addFilter(context_filter)

    # Log configuration
    root_logger.debug(
        f"Logging configured: level={log_level}, json={json_format}, "
        f"file={log_file if log_file else 'None'}",
    )
