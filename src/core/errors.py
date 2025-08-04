"""Standardized error handling patterns for the PowerRebuilder pipeline.

This module provides:
- Error context management
- Structured error recovery strategies
- Error aggregation and reporting
- Integration with logging and monitoring
- User-friendly error formatting
"""

import gc
import logging
import time
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, TypeVar

from .exceptions import SimeFinchError

T = TypeVar("T")

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Error recovery strategies."""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    FAIL = "fail"
    CONTINUE = "continue"


@dataclass
class ErrorContext:
    """Context information for an error."""

    stage: str
    operation: str
    file_path: Path | None = None
    line_number: int | None = None
    column_number: int | None = None
    additional_info: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stage": self.stage,
            "operation": self.operation,
            "file_path": str(self.file_path) if self.file_path else None,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "additional_info": self.additional_info,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""

    error_type: str
    message: str
    severity: ErrorSeverity
    context: ErrorContext
    stack_trace: str | None = None
    recovery_attempted: bool = False
    recovery_strategy: RecoveryStrategy | None = None
    recovery_successful: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context.to_dict(),
            "stack_trace": self.stack_trace,
            "recovery_attempted": self.recovery_attempted,
            "recovery_strategy": self.recovery_strategy.value
            if self.recovery_strategy
            else None,
            "recovery_successful": self.recovery_successful,
        }


class IErrorHandler(Protocol):
    """Interface for error handlers."""

    def handle(self, error: Exception, context: ErrorContext) -> Any:
        """Handle an error with given context."""
        ...

    def can_handle(self, error: Exception) -> bool:
        """Check if this handler can handle the error."""
        ...


class IErrorRecovery(Protocol):
    """Interface for error recovery strategies."""

    def attempt_recovery(self, error: Exception, context: ErrorContext) -> Any:
        """Attempt to recover from an error."""
        ...

    def get_strategy(self) -> RecoveryStrategy:
        """Get the recovery strategy type."""
        ...


class BaseErrorHandler(ABC):
    """Base class for error handlers."""

    def __init__(self, severity: ErrorSeverity = ErrorSeverity.ERROR) -> None:
        """Initialize error handler.

        Args:
            severity: Default severity level
        """
        self.severity = severity
        self.error_records: list[ErrorRecord] = []

    @abstractmethod
    def handle(self, error: Exception, context: ErrorContext) -> Any:
        """Handle an error with given context."""

    @abstractmethod
    def can_handle(self, error: Exception) -> bool:
        """Check if this handler can handle the error."""

    def record_error(
        self,
        error: Exception,
        context: ErrorContext,
        severity: ErrorSeverity | None = None,
    ) -> ErrorRecord:
        """Record an error occurrence."""
        record = ErrorRecord(
            error_type=type(error).__name__,
            message=str(error),
            severity=severity or self.severity,
            context=context,
            stack_trace=traceback.format_exc()
            if severity != ErrorSeverity.INFO
            else None,
        )
        self.error_records.append(record)
        return record


class RetryHandler(BaseErrorHandler):
    """Error handler that implements retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> None:
        """Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries
            backoff_factor: Factor to multiply delay by after each retry
            severity: Default severity level
        """
        super().__init__(severity)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor

    def handle(self, error: Exception, context: ErrorContext) -> Any:
        """Handle error with retry logic."""
        record = self.record_error(error, context)
        record.recovery_strategy = RecoveryStrategy.RETRY
        record.recovery_attempted = True

        # Log the retry attempt
        logger.warning(
            "Error in %s: %s. Will retry up to %d times.",
            context.operation,
            str(error),
            self.max_retries,
        )

        # Retry logic would be implemented by the caller
        return None

    def can_handle(self, error: Exception) -> bool:
        """Check if error is retryable."""
        # Network errors, temporary file locks, etc.
        retryable_errors = (OSError, IOError, ConnectionError, TimeoutError)
        return isinstance(error, retryable_errors)


class FallbackHandler(BaseErrorHandler):
    """Error handler that implements fallback strategies."""

    def __init__(
        self,
        fallback_map: dict[type[Exception], Callable],
        severity: ErrorSeverity = ErrorSeverity.WARNING,
    ) -> None:
        """Initialize fallback handler.

        Args:
            fallback_map: Map of error types to fallback functions
            severity: Default severity level
        """
        super().__init__(severity)
        self.fallback_map = fallback_map

    def handle(self, error: Exception, context: ErrorContext) -> Any:
        """Handle error with fallback strategy."""
        record = self.record_error(error, context)
        record.recovery_strategy = RecoveryStrategy.FALLBACK
        record.recovery_attempted = True

        # Find appropriate fallback
        for error_type, fallback_func in self.fallback_map.items():
            if isinstance(error, error_type):
                try:
                    result = fallback_func(error, context)
                    record.recovery_successful = True
                    logger.info(
                        "Successfully used fallback for %s in %s",
                        type(error).__name__,
                        context.operation,
                    )
                    return result
                except Exception as e:
                    logger.error(
                        "Fallback failed for %s: %s", context.operation, str(e)
                    )
                    record.recovery_successful = False
                    raise

        return None

    def can_handle(self, error: Exception) -> bool:
        """Check if error has a fallback."""
        return any(isinstance(error, error_type) for error_type in self.fallback_map)


class ErrorCollector:
    """Collects errors during operations without immediately failing."""

    def __init__(
        self, max_errors: int = 100, fail_fast: bool = False, stage: str = "unknown"
    ) -> None:
        """Initialize error collector.

        Args:
            max_errors: Maximum errors to collect before failing
            fail_fast: Whether to fail on first error
            stage: Pipeline stage name
        """
        self.max_errors = max_errors
        self.fail_fast = fail_fast
        self.stage = stage
        self.errors: list[ErrorRecord] = []
        self._critical_error: Exception | None = None

    def add_error(
        self,
        error: Exception,
        context: ErrorContext | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> None:
        """Add an error to the collection."""
        if context is None:
            context = ErrorContext(stage=self.stage, operation="unknown")

        record = ErrorRecord(
            error_type=type(error).__name__,
            message=str(error),
            severity=severity,
            context=context,
            stack_trace=traceback.format_exc()
            if severity != ErrorSeverity.INFO
            else None,
        )

        self.errors.append(record)

        # Check if we should fail
        if severity == ErrorSeverity.CRITICAL:
            self._critical_error = error

        if self.fail_fast or len(self.errors) >= self.max_errors:
            self.raise_if_errors()

    def add_warning(self, message: str, context: ErrorContext | None = None) -> None:
        """Add a warning to the collection."""
        if context is None:
            context = ErrorContext(stage=self.stage, operation="unknown")

        record = ErrorRecord(
            error_type="Warning",
            message=message,
            severity=ErrorSeverity.WARNING,
            context=context,
        )
        self.errors.append(record)

    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return any(
            e.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
            for e in self.errors
        )

    def has_critical_errors(self) -> bool:
        """Check if any critical errors were collected."""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)

    def get_error_count(self) -> int:
        """Get count of actual errors (not warnings)."""
        return sum(
            1
            for e in self.errors
            if e.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
        )

    def get_warning_count(self) -> int:
        """Get count of warnings."""
        return sum(1 for e in self.errors if e.severity == ErrorSeverity.WARNING)

    def raise_if_errors(self) -> None:
        """Raise an exception if errors were collected."""
        if self._critical_error:
            raise self._critical_error

        error_count = self.get_error_count()
        if error_count > 0:
            msg = f"{self.stage}: {error_count} errors occurred"
            if error_count == 1 and self.errors:
                # Include the single error message
                error = next(
                    e
                    for e in self.errors
                    if e.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
                )
                msg = f"{msg}: {error.message}"
            raise SimeFinchError(msg)

    def get_summary(self) -> dict[str, Any]:
        """Get error summary."""
        return {
            "stage": self.stage,
            "total_errors": self.get_error_count(),
            "total_warnings": self.get_warning_count(),
            "errors_by_type": self._group_by_type(),
            "errors_by_severity": self._group_by_severity(),
            "has_critical": self.has_critical_errors(),
        }

    def _group_by_type(self) -> dict[str, int]:
        """Group errors by type."""
        result = {}
        for error in self.errors:
            result[error.error_type] = result.get(error.error_type, 0) + 1
        return result

    def _group_by_severity(self) -> dict[str, int]:
        """Group errors by severity."""
        result = {}
        for error in self.errors:
            severity = error.severity.value
            result[severity] = result.get(severity, 0) + 1
        return result

    def format_errors(self) -> str:
        """Format errors for display."""
        if not self.errors:
            return "No errors"

        lines = [f"\n{self.stage} Errors ({len(self.errors)} total):"]

        # Group by file if available
        by_file = {}
        no_file = []

        for error in self.errors:
            if error.context.file_path:
                file_key = str(error.context.file_path)
                if file_key not in by_file:
                    by_file[file_key] = []
                by_file[file_key].append(error)
            else:
                no_file.append(error)

        # Format errors by file
        for file_path, file_errors in sorted(by_file.items()):
            lines.append(f"\n  {file_path}:")
            for error in file_errors:
                lines.append(self._format_error(error, indent=4))

        # Format errors without file
        if no_file:
            lines.append("\n  General errors:")
            for error in no_file:
                lines.append(self._format_error(error, indent=4))

        return "\n".join(lines)

    def _format_error(self, error: ErrorRecord, indent: int = 0) -> str:
        """Format a single error."""
        prefix = " " * indent

        # Build position info
        pos_parts = []
        if error.context.line_number:
            if error.context.column_number:
                pos_parts.append(
                    f"line {error.context.line_number}:{error.context.column_number}"
                )
            else:
                pos_parts.append(f"line {error.context.line_number}")

        position = f" ({', '.join(pos_parts)})" if pos_parts else ""

        # Build severity indicator
        severity_map = {
            ErrorSeverity.WARNING: "⚠",
            ErrorSeverity.ERROR: "✗",
            ErrorSeverity.CRITICAL: "⛔",
        }
        severity_icon = severity_map.get(error.severity, "•")

        return f"{prefix}{severity_icon} {error.error_type}{position}: {error.message}"


class ErrorManager:
    """Central error management for the pipeline."""

    def __init__(self) -> None:
        """Initialize error manager."""
        self.handlers: list[BaseErrorHandler] = []
        self.collectors: dict[str, ErrorCollector] = {}
        self.global_errors: list[ErrorRecord] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default error handlers."""
        # Retry handler for transient errors
        self.handlers.append(RetryHandler())

        # Fallback handlers for common scenarios
        fallbacks = {
            UnicodeDecodeError: lambda e, ctx: self._handle_encoding_error(e, ctx),
            MemoryError: lambda e, ctx: self._handle_memory_error(e, ctx),
            FileNotFoundError: lambda e, ctx: self._handle_file_not_found(e, ctx),
        }
        self.handlers.append(FallbackHandler(fallbacks))

    def register_handler(self, handler: BaseErrorHandler) -> None:
        """Register an error handler."""
        self.handlers.append(handler)

    def get_collector(self, stage: str, **kwargs) -> ErrorCollector:
        """Get or create error collector for a stage."""
        if stage not in self.collectors:
            self.collectors[stage] = ErrorCollector(stage=stage, **kwargs)
        return self.collectors[stage]

    def handle_error(
        self, error: Exception, context: ErrorContext, raise_on_fail: bool = True
    ) -> Any | None:
        """Handle an error using registered handlers."""
        # Try each handler
        for handler in self.handlers:
            if handler.can_handle(error):
                try:
                    result = handler.handle(error, context)
                    if result is not None:
                        return result
                    return result
                except Exception as e:
                    logger.error("Handler failed: %s", str(e))

        # Record as global error if no handler succeeded
        record = ErrorRecord(
            error_type=type(error).__name__,
            message=str(error),
            severity=ErrorSeverity.ERROR,
            context=context,
            stack_trace=traceback.format_exc(),
        )
        self.global_errors.append(record)

        if raise_on_fail:
            raise

        return None

    @contextmanager
    def error_context(
        self, stage: str, operation: str, file_path: Path | None = None, **kwargs
    ):
        """Context manager for error handling."""
        context = ErrorContext(
            stage=stage,
            operation=operation,
            file_path=file_path,
            additional_info=kwargs,
        )

        try:
            yield context
        except Exception as e:
            # Try to handle the error
            result = self.handle_error(e, context, raise_on_fail=False)
            if result is None:
                # Re-raise if not handled
                raise

    def get_error_report(self) -> dict[str, Any]:
        """Get comprehensive error report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_errors": sum(c.get_error_count() for c in self.collectors.values()),
            "total_warnings": sum(
                c.get_warning_count() for c in self.collectors.values()
            ),
            "stages": {},
        }

        # Add stage summaries
        for stage, collector in self.collectors.items():
            report["stages"][stage] = collector.get_summary()

        # Add global errors
        report["global_errors"] = len(self.global_errors)

        return report

    def format_report(self) -> str:
        """Format error report for display."""
        lines = ["Error Report", "=" * 50]

        # Summary
        total_errors = sum(c.get_error_count() for c in self.collectors.values())
        total_warnings = sum(c.get_warning_count() for c in self.collectors.values())

        lines.append(f"\nTotal Errors: {total_errors}")
        lines.append(f"Total Warnings: {total_warnings}")

        # Stage details
        for collector in self.collectors.values():
            if collector.errors:
                lines.append(collector.format_errors())

        # Global errors
        if self.global_errors:
            lines.append(f"\nGlobal Errors ({len(self.global_errors)}):")
            for error in self.global_errors:
                lines.append(f"  • {error.error_type}: {error.message}")

        return "\n".join(lines)

    # Fallback handlers

    def _handle_encoding_error(
        self, error: UnicodeDecodeError, context: ErrorContext
    ) -> str:
        """Handle encoding errors with fallback."""
        logger.warning("Encoding error in %s, using fallback", context.operation)
        # Return replacement character or empty string
        return "�" * (error.end - error.start)

    def _handle_memory_error(self, _error: MemoryError, context: ErrorContext) -> None:
        """Handle memory errors."""
        logger.error("Memory error in %s, attempting cleanup", context.operation)
        # Force garbage collection
        gc.collect()
        # Could implement more sophisticated recovery
        raise

    def _handle_file_not_found(
        self, error: FileNotFoundError, context: ErrorContext
    ) -> None:
        """Handle file not found errors."""
        logger.error("File not found in %s: %s", context.operation, error.filename)
        # Could return default or empty result depending on context
        raise


# Global error manager instance
_error_manager = ErrorManager()


def get_error_manager() -> ErrorManager:
    """Get global error manager instance."""
    return _error_manager


@contextmanager
def error_handler(
    stage: str,
    operation: str,
    file_path: Path | None = None,
    collector: ErrorCollector | None = None,
    **kwargs,
):
    """Context manager for standardized error handling.

    Args:
        stage: Pipeline stage name
        operation: Operation being performed
        file_path: Optional file being processed
        collector: Optional error collector to use
        **kwargs: Additional context information

    Example:
        with error_handler("parse", "parsing source file", file_path=Path("test.sru")) as ctx:
            # Do parsing
            pass
    """
    context = ErrorContext(
        stage=stage, operation=operation, file_path=file_path, additional_info=kwargs
    )

    try:
        yield context
    except Exception as e:
        if collector:
            # Add to collector
            collector.add_error(e, context)
            # Re-raise if critical
            if isinstance(e, SystemExit | KeyboardInterrupt):
                raise
        else:
            # Use global error manager
            get_error_manager().handle_error(e, context)


def with_retry[T](
    func: Callable[..., T],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> T:
    """Execute function with retry logic.

    Args:
        func: Function to execute
        max_retries: Maximum retry attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Exceptions to retry on

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    last_error = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_error = e

            if attempt < max_retries:
                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1,
                    max_retries + 1,
                    str(e),
                    current_delay,
                )
                time.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error("All %d attempts failed", max_retries + 1)

    raise last_error


def format_exception_chain(exc: Exception, include_traceback: bool = False) -> str:
    """Format exception chain for display.

    Args:
        exc: Exception to format
        include_traceback: Whether to include full traceback

    Returns:
        Formatted exception chain
    """
    lines = []
    current = exc

    while current is not None:
        if isinstance(current, SimeFinchError):
            # Use custom formatting
            lines.append(f"{type(current).__name__}: {current}")
        else:
            lines.append(f"{type(current).__name__}: {str(current)}")

        # Get cause
        if hasattr(current, "__cause__") and current.__cause__ is not None:
            lines.append("  Caused by:")
            current = current.__cause__
        elif hasattr(current, "__context__") and current.__context__ is not None:
            lines.append("  During handling of:")
            current = current.__context__
        else:
            break

    result = "\n".join(lines)

    if include_traceback:
        result += "\n\nTraceback:\n" + traceback.format_exc()

    return result
