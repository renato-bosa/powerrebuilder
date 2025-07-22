"""Logging configuration for the PowerBuilder pipeline.

This module provides a comprehensive logging utility that supports:
- Structured logging with JSON and text formatters
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File and console output with configurable handlers
- Context-aware logging with extra fields
- Pipeline-specific logging methods
- Performance and progress tracking
"""

import contextlib
import json
import logging
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Re-export common logging levels for convenience
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Available log output formats."""

    TEXT = "text"
    JSON = "json"
    SIMPLE = "simple"


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "getMessage",
            ]:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored text formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class PipelineLogger:
    """Enhanced logger for pipeline operations with context support."""

    def __init__(self, logger: logging.Logger):
        """Initialize pipeline logger wrapper.

        Args:
            logger: The underlying Python logger
        """
        self._logger = logger
        self._context: dict[str, Any] = {}
        self._stage: str | None = None
        self._start_times: dict[str, float] = {}

    def _log_with_context(self, level: int, msg: str, *args, **kwargs):
        """Log message with current context."""
        extra = kwargs.get("extra", {})
        extra.update(self._context)
        if self._stage:
            extra["stage"] = self._stage
        kwargs["extra"] = extra
        self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with context."""
        self._log_with_context(DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info message with context."""
        self._log_with_context(INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with context."""
        self._log_with_context(WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message with context."""
        self._log_with_context(ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with context."""
        self._log_with_context(CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log exception with traceback."""
        kwargs["exc_info"] = kwargs.get("exc_info", True)
        self.error(msg, *args, **kwargs)

    def set_context(self, **kwargs):
        """Set persistent context fields for all subsequent logs.

        Args:
            **kwargs: Context fields to add
        """
        self._context.update(kwargs)

    def clear_context(self):
        """Clear all context fields."""
        self._context.clear()

    @contextlib.contextmanager
    def context(self, **kwargs):
        """Context manager for temporary context fields.

        Args:
            **kwargs: Context fields to add temporarily
        """
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield
        finally:
            self._context = old_context

    def stage_start(self, stage_name: str, **kwargs):
        """Log the start of a pipeline stage.

        Args:
            stage_name: Name of the stage
            **kwargs: Additional context fields
        """
        self._stage = stage_name
        self._start_times[stage_name] = time.time()
        self.info(f"Starting stage: {stage_name}", extra=kwargs)

    def stage_end(self, stage_name: str, success: bool = True, **kwargs):
        """Log the end of a pipeline stage.

        Args:
            stage_name: Name of the stage
            success: Whether the stage completed successfully
            **kwargs: Additional context fields
        """
        duration = None
        if stage_name in self._start_times:
            duration = time.time() - self._start_times[stage_name]
            del self._start_times[stage_name]
            kwargs["duration_seconds"] = duration

        level = INFO if success else ERROR
        status = "completed" if success else "failed"
        self._log_with_context(level, f"Stage {stage_name} {status}", extra=kwargs)
        self._stage = None

    def progress(self, current: int, total: int, message: str = "", **kwargs):
        """Log progress information.

        Args:
            current: Current progress value
            total: Total value
            message: Optional progress message
            **kwargs: Additional context fields
        """
        percentage = (current / total * 100) if total > 0 else 0
        kwargs.update(
            {
                "progress_current": current,
                "progress_total": total,
                "progress_percentage": percentage,
            }
        )
        msg = f"Progress: {current}/{total} ({percentage:.1f}%)"
        if message:
            msg += f" - {message}"
        self.info(msg, extra=kwargs)

    def metrics(self, **metrics):
        """Log metrics/statistics.

        Args:
            **metrics: Metric key-value pairs
        """
        self.info("Metrics", extra={"metrics": metrics})


def setup_logging(
    level: int | str = INFO,
    log_file: str | Path | None = None,
    log_format: LogFormat = LogFormat.TEXT,
    console: bool = True,
    file_mode: str = "a",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """Set up logging configuration for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_format: Output format (TEXT, JSON, SIMPLE)
        console: Whether to log to console
        file_mode: File opening mode ('a' for append, 'w' for write)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Set up formatters
    if log_format == LogFormat.JSON:
        formatter = StructuredFormatter()
    elif log_format == LogFormat.SIMPLE:
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    elif console and hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
        formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        from logging.handlers import RotatingFileHandler

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            str(log_path), mode=file_mode, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(WARNING)
    logging.getLogger("requests").setLevel(WARNING)
    logging.getLogger("httpx").setLevel(WARNING)


def get_logger(name: str) -> PipelineLogger:
    """Get a pipeline-aware logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        PipelineLogger instance with enhanced functionality
    """
    return PipelineLogger(logging.getLogger(name))


def configure_pipeline_logging(
    pipeline_name: str,
    output_dir: str | Path | None = None,
    verbose: bool = False,
) -> None:
    """Configure logging specifically for pipeline operations.

    Args:
        pipeline_name: Name of the pipeline
        output_dir: Optional output directory for log files
        verbose: Enable verbose (DEBUG) logging
    """
    level = DEBUG if verbose else INFO

    # Determine log file path
    log_file = None
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = output_path / f"{pipeline_name}_{timestamp}.log"

    # Set up logging
    setup_logging(
        level=level,
        log_file=log_file,
        log_format=LogFormat.TEXT,
        console=True,
    )

    # Log initial configuration
    logger = get_logger(__name__)
    logger.info(f"Pipeline logging configured for: {pipeline_name}")
    if log_file:
        logger.info(f"Log file: {log_file}")


# Convenience function for backward compatibility
def get_simple_logger(name: str) -> logging.Logger:
    """Get a standard Python logger (for backward compatibility).

    Args:
        name: Logger name

    Returns:
        Standard Python logger
    """
    return logging.getLogger(name)
