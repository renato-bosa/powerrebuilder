"""Error recovery utilities for the pipeline.

This module provides retry mechanisms, error collection, and recovery strategies
for the PowerBuilder conversion pipeline.
"""

import functools
import json
import logging
import shutil
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, TypeVar

import psutil

from src.core.exceptions import (
    BaseError,
    ExtractError,
    LibraryCorruptedError,
    ResourceLimitError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class RecoveryStrategy(Protocol):
    """Protocol for recovery strategies."""

    def can_recover(self, error: BaseError) -> bool:
        """Check if this strategy can handle the error."""
        ...

    def recover(self, error: BaseError, context: dict[str, Any]) -> Any:
        """Attempt to recover from the error."""
        ...


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ) -> None:
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        Args:
            attempt: Attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base**attempt), self.max_delay
        )

        if self.jitter:
            import random

            # Add 0-25% jitter
            delay *= 1 + random.random() * 0.25

        return delay


class RecoveryContext:
    """Context information for recovery operations."""

    def __init__(self) -> None:
        """Initialize recovery context."""
        self.checkpoints: dict[str, Any] = {}
        self.error_history: list[BaseError] = []
        self.recovery_attempts: int = 0
        self.start_time: datetime = datetime.now()
        self.metadata: dict[str, Any] = {}

    def add_checkpoint(self, name: str, data: Any) -> None:
        """Add a recovery checkpoint.

        Args:
            name: Checkpoint name
            data: Checkpoint data
        """
        self.checkpoints[name] = {
            "timestamp": datetime.now(),
            "data": data,
        }

    def get_checkpoint(self, name: str) -> Any:
        """Get checkpoint data.

        Args:
            name: Checkpoint name

        Returns:
            Checkpoint data or None
        """
        checkpoint = self.checkpoints.get(name)
        return checkpoint["data"] if checkpoint else None

    def add_error(self, error: BaseError) -> None:
        """Add error to history.

        Args:
            error: Error to add
        """
        self.error_history.append(error)

    def save_to_file(self, filepath: Path) -> None:
        """Save context to file for persistence.

        Args:
            filepath: Path to save context
        """
        data = {
            "checkpoints": {
                name: {
                    "timestamp": cp["timestamp"].isoformat(),
                    "data": cp["data"],
                }
                for name, cp in self.checkpoints.items()
            },
            "error_history": [
                {
                    "type": type(e).__name__,
                    "message": str(e),
                    "error_code": getattr(e, "error_code", None),
                }
                for e in self.error_history
            ],
            "recovery_attempts": self.recovery_attempts,
            "start_time": self.start_time.isoformat(),
            "metadata": self.metadata,
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: Path) -> "RecoveryContext":
        """Load context from file.

        Args:
            filepath: Path to load context from

        Returns:
            Loaded context
        """
        context = cls()

        if filepath.exists():
            with filepath.open() as f:
                data = json.load(f)

            # Restore checkpoints
            for name, cp in data.get("checkpoints", {}).items():
                context.checkpoints[name] = {
                    "timestamp": datetime.fromisoformat(cp["timestamp"]),
                    "data": cp["data"],
                }

            context.recovery_attempts = data.get("recovery_attempts", 0)
            context.start_time = datetime.fromisoformat(
                data.get("start_time", datetime.now().isoformat())
            )
            context.metadata = data.get("metadata", {})

        return context


def retry_with_backoff(
    config: RetryConfig | None = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[F], F]:
    """Decorator for retrying functions with exponential backoff.

    Args:
        config: Retry configuration (uses defaults if None)
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry with (exception, attempt)

    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts - 1:
                        # Last attempt, re-raise
                        raise

                    # Calculate delay
                    delay = config.get_delay(attempt)

                    logger.warning(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.1fs",
                        attempt + 1,
                        config.max_attempts,
                        func.__name__,
                        str(e),
                        delay,
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt)

                    # Wait before retry
                    time.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic error")

        return wrapper  # type: ignore

    return decorator


class FileCorruptionRecovery:
    """Recovery strategy for file corruption errors."""

    def __init__(self, backup_dir: Path | None = None) -> None:
        """Initialize file corruption recovery.

        Args:
            backup_dir: Directory for backup files
        """
        self.backup_dir = backup_dir or Path.home() / ".powerrebuilder" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def can_recover(self, error: BaseError) -> bool:
        """Check if this strategy can handle the error."""
        return isinstance(error, (LibraryCorruptedError, ExtractError))

    def recover(self, error: BaseError, context: dict[str, Any]) -> Any:
        """Attempt to recover from file corruption.

        Args:
            error: The error to recover from
            context: Recovery context with file_path, output_dir, etc.

        Returns:
            Recovery result or raises error
        """
        file_path = context.get("file_path")
        if not file_path:
            raise ValueError("No file_path in recovery context")

        file_path = Path(file_path)

        # Try backup first
        backup_path = self._find_backup(file_path)
        if backup_path and backup_path.exists():
            logger.info("Using backup file: %s", backup_path)
            context["file_path"] = backup_path
            context["using_backup"] = True
            return backup_path

        # No backup available, try repair
        if isinstance(error, LibraryCorruptedError):
            logger.info("Attempting to repair corrupted library: %s", file_path)
            repaired_path = self._repair_library(file_path)
            if repaired_path:
                context["file_path"] = repaired_path
                context["was_repaired"] = True
                return repaired_path

        raise error

    def _find_backup(self, file_path: Path) -> Path | None:
        """Find backup file if available.

        Args:
            file_path: Original file path

        Returns:
            Backup path or None
        """
        # Look for .bak file
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        if backup_path.exists():
            return backup_path

        # Look in backup directory
        backup_name = (
            f"{file_path.stem}_{file_path.stat().st_mtime:.0f}{file_path.suffix}"
        )
        backup_path = self.backup_dir / backup_name
        if backup_path.exists():
            return backup_path

        return None

    def _repair_library(self, file_path: Path) -> Path | None:
        """Attempt to repair a corrupted library.

        Args:
            file_path: Path to corrupted library

        Returns:
            Path to repaired file or None
        """
        # This would implement actual repair logic
        # For now, just return None
        return None

    def create_backup(self, file_path: Path) -> Path:
        """Create a backup of a file.

        Args:
            file_path: File to backup

        Returns:
            Path to backup file
        """
        file_path = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        logger.info("Created backup: %s", backup_path)

        return backup_path


class ResourceLimitRecovery:
    """Recovery strategy for resource limit errors."""

    def __init__(self) -> None:
        """Initialize resource limit recovery."""
        self.reduced_limits: dict[str, Any] = {}

    def can_recover(self, error: BaseError) -> bool:
        """Check if this strategy can handle the error."""
        return isinstance(error, ResourceLimitError)

    def recover(self, error: BaseError, context: dict[str, Any]) -> Any:
        """Attempt to recover from resource limits.

        Args:
            error: The error to recover from
            context: Recovery context

        Returns:
            Recovery result or raises error
        """
        if not isinstance(error, ResourceLimitError):
            raise error

        resource = error.resource
        current_limit = error.limit
        requested = error.requested

        logger.info(
            "Resource limit hit for %s: requested=%d, limit=%d",
            resource,
            requested,
            current_limit,
        )

        # Try different strategies based on resource type
        if resource == "memory":
            return self._handle_memory_limit(error, context)
        if resource == "file_size":
            return self._handle_file_size_limit(error, context)
        if resource == "time":
            return self._handle_time_limit(error, context)
        # Unknown resource type
        raise error

    def _handle_memory_limit(
        self, error: ResourceLimitError, context: dict[str, Any]
    ) -> Any:
        """Handle memory limit errors.

        Args:
            error: Memory limit error
            context: Recovery context

        Returns:
            Recovery strategy or raises error
        """
        # Check current memory usage
        memory_info = psutil.virtual_memory()
        available_mb = memory_info.available / (1024 * 1024)

        logger.info("Available memory: %.1f MB", available_mb)

        # If we have enough memory, increase limit
        if available_mb > error.requested / (1024 * 1024) * 1.5:
            new_limit = int(error.requested * 1.2)  # 20% buffer
            context["memory_limit"] = new_limit
            logger.info("Increasing memory limit to %d bytes", new_limit)
            return {"action": "increase_limit", "new_limit": new_limit}

        # Otherwise, try chunking
        if "chunk_size" in context:
            # Reduce chunk size
            new_chunk_size = context["chunk_size"] // 2
            if new_chunk_size < 1024:  # 1KB minimum
                raise error

            context["chunk_size"] = new_chunk_size
            logger.info("Reducing chunk size to %d bytes", new_chunk_size)
            return {"action": "reduce_chunk_size", "new_size": new_chunk_size}

        # Enable streaming if possible
        if not context.get("streaming", False):
            context["streaming"] = True
            logger.info("Enabling streaming mode")
            return {"action": "enable_streaming"}

        raise error

    def _handle_file_size_limit(
        self, error: ResourceLimitError, context: dict[str, Any]
    ) -> Any:
        """Handle file size limit errors.

        Args:
            error: File size limit error
            context: Recovery context

        Returns:
            Recovery strategy or raises error
        """
        # Check disk space
        output_dir = context.get("output_dir", Path.cwd())
        stat = shutil.disk_usage(output_dir)
        available_mb = stat.free / (1024 * 1024)

        logger.info("Available disk space: %.1f MB", available_mb)

        # If we have space, increase limit
        if available_mb > error.requested / (1024 * 1024) * 2:
            new_limit = int(error.requested * 1.1)  # 10% buffer
            context["file_size_limit"] = new_limit
            logger.info("Increasing file size limit to %d bytes", new_limit)
            return {"action": "increase_limit", "new_limit": new_limit}

        # Try compression
        if not context.get("compress_output", False):
            context["compress_output"] = True
            logger.info("Enabling output compression")
            return {"action": "enable_compression"}

        raise error

    def _handle_time_limit(
        self, error: ResourceLimitError, context: dict[str, Any]
    ) -> Any:
        """Handle time limit errors.

        Args:
            error: Time limit error
            context: Recovery context

        Returns:
            Recovery strategy or raises error
        """
        # For time limits, we can try to optimize or increase limit
        current_limit = error.limit

        # Increase time limit by 50%
        new_limit = int(current_limit * 1.5)
        context["time_limit"] = new_limit
        logger.info("Increasing time limit to %d seconds", new_limit)

        # Also enable any performance optimizations
        context["optimize_performance"] = True

        return {"action": "increase_time_limit", "new_limit": new_limit}


class CheckpointRecovery:
    """Recovery using checkpoints for long-running operations."""

    def __init__(self, checkpoint_dir: Path | None = None) -> None:
        """Initialize checkpoint recovery.

        Args:
            checkpoint_dir: Directory for checkpoint files
        """
        self.checkpoint_dir = checkpoint_dir or Path.cwd() / ".checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        operation_id: str,
        state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Create a checkpoint for an operation.

        Args:
            operation_id: Unique identifier for the operation
            state: Current state to checkpoint
            metadata: Optional metadata about the checkpoint

        Returns:
            Path to checkpoint file
        """
        checkpoint_data = {
            "operation_id": operation_id,
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "metadata": metadata or {},
        }

        checkpoint_file = self.checkpoint_dir / f"{operation_id}.checkpoint"
        with checkpoint_file.open("w") as f:
            json.dump(checkpoint_data, f, indent=2)

        logger.debug("Created checkpoint for %s", operation_id)
        return checkpoint_file

    def load_checkpoint(self, operation_id: str) -> dict[str, Any] | None:
        """Load checkpoint for an operation.

        Args:
            operation_id: Operation identifier

        Returns:
            Checkpoint data or None
        """
        checkpoint_file = self.checkpoint_dir / f"{operation_id}.checkpoint"

        if not checkpoint_file.exists():
            return None

        try:
            with checkpoint_file.open() as f:
                data = json.load(f)

            logger.info(
                "Loaded checkpoint for %s from %s", operation_id, data["timestamp"]
            )
            return data
        except Exception as e:
            logger.warning("Failed to load checkpoint %s: %s", operation_id, e)
            return None

    def remove_checkpoint(self, operation_id: str) -> None:
        """Remove checkpoint after successful completion.

        Args:
            operation_id: Operation identifier
        """
        checkpoint_file = self.checkpoint_dir / f"{operation_id}.checkpoint"

        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.debug("Removed checkpoint for %s", operation_id)

    def cleanup_old_checkpoints(self, max_age_days: int = 7) -> None:
        """Clean up old checkpoint files.

        Args:
            max_age_days: Maximum age of checkpoints to keep
        """
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

        for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint"):
            if checkpoint_file.stat().st_mtime < cutoff_time:
                checkpoint_file.unlink()
                logger.debug("Removed old checkpoint: %s", checkpoint_file)


class NetworkRetryStrategy:
    """Recovery strategy for network-related errors."""

    def __init__(self) -> None:
        """Initialize network retry strategy."""
        self.retry_config = RetryConfig(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=120.0,
        )

    def should_retry(self, error: Exception) -> bool:
        """Check if error is retryable.

        Args:
            error: The error to check

        Returns:
            True if retryable
        """
        # Common network error indicators
        network_errors = [
            "connection",
            "timeout",
            "network",
            "refused",
            "reset",
            "broken pipe",
        ]

        error_str = str(error).lower()
        return any(indicator in error_str for indicator in network_errors)


class RecoveryManager:
    """Central manager for recovery strategies."""

    def __init__(self) -> None:
        """Initialize recovery manager."""
        self.strategies: list[RecoveryStrategy] = []
        self.context = RecoveryContext()

        # Register default strategies
        self.register_strategy(FileCorruptionRecovery())
        self.register_strategy(ResourceLimitRecovery())

    def register_strategy(self, strategy: RecoveryStrategy) -> None:
        """Register a recovery strategy.

        Args:
            strategy: Strategy to register
        """
        self.strategies.append(strategy)

    def attempt_recovery(self, error: BaseError, context: dict[str, Any]) -> Any:
        """Attempt to recover from an error.

        Args:
            error: The error to recover from
            context: Context information

        Returns:
            Recovery result or re-raises error
        """
        self.context.add_error(error)
        self.context.recovery_attempts += 1

        # Try each strategy
        for strategy in self.strategies:
            if strategy.can_recover(error):
                try:
                    logger.info(
                        "Attempting recovery with %s",
                        type(strategy).__name__,
                    )
                    result = strategy.recover(error, context)
                    logger.info("Recovery successful")
                    return result
                except Exception as e:
                    logger.warning(
                        "Recovery strategy %s failed: %s",
                        type(strategy).__name__,
                        e,
                    )
                    continue

        # No strategy worked
        logger.error("All recovery strategies failed")
        raise error


# Global recovery manager instance
_recovery_manager: RecoveryManager | None = None


def get_recovery_manager() -> RecoveryManager:
    """Get the global recovery manager instance.

    Returns:
        Recovery manager instance
    """
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager


def with_recovery(
    operation_id: str,
    checkpoint_interval: int | None = None,
) -> Callable[[F], F]:
    """Decorator to add recovery capabilities to a function.

    Args:
        operation_id: Unique identifier for the operation
        checkpoint_interval: Optional interval for automatic checkpoints

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            manager = get_recovery_manager()
            checkpoint_recovery = CheckpointRecovery()

            # Check for existing checkpoint
            checkpoint_data = checkpoint_recovery.load_checkpoint(operation_id)
            if checkpoint_data:
                logger.info("Resuming from checkpoint")
                # Merge checkpoint state into kwargs
                kwargs["_checkpoint_state"] = checkpoint_data["state"]

            try:
                result = func(*args, **kwargs)
                # Success - remove checkpoint
                checkpoint_recovery.remove_checkpoint(operation_id)
                return result
            except BaseError as e:
                # Try recovery
                recovery_context = {
                    "operation_id": operation_id,
                    "args": args,
                    "kwargs": kwargs,
                }

                try:
                    recovery_result = manager.attempt_recovery(e, recovery_context)
                    # Retry with recovery result
                    if "retry" in recovery_context:
                        return wrapper(*args, **kwargs)
                    return recovery_result
                except Exception:
                    # Recovery failed, re-raise original
                    raise e

        return wrapper  # type: ignore

    return decorator


class PipelineCheckpoint:
    """Checkpoint manager specifically for pipeline operations."""

    def __init__(self, checkpoint_dir: Path) -> None:
        """Initialize pipeline checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "pipeline_checkpoint.json"

    def save(
        self,
        stage: str,
        processed_files: list[str],
        failed_files: list[str],
        state: dict[str, Any],
    ) -> None:
        """Save pipeline checkpoint.

        Args:
            stage: Current pipeline stage
            processed_files: List of successfully processed files
            failed_files: List of failed files
            state: Additional state information
        """
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "state": state,
        }

        with self.checkpoint_file.open("w") as f:
            json.dump(checkpoint_data, f, indent=2)

        logger.info(
            "Saved checkpoint at stage %s: %d processed, %d failed",
            stage,
            len(processed_files),
            len(failed_files),
        )

    def load(self) -> dict[str, Any] | None:
        """Load pipeline checkpoint.

        Returns:
            Checkpoint data or None if no checkpoint exists
        """
        if not self.checkpoint_file.exists():
            return None

        try:
            with self.checkpoint_file.open() as f:
                data = json.load(f)

            # Check if checkpoint is recent (within 30 minutes by default)
            timestamp = datetime.fromisoformat(data["timestamp"])
            age = datetime.now() - timestamp

            if age.total_seconds() > 1800:  # 30 minutes
                logger.warning(
                    "Checkpoint is %.1f minutes old, may be stale",
                    age.total_seconds() / 60,
                )

            return data
        except Exception as e:
            logger.error("Failed to load checkpoint: %s", e)
            return None

    def clear(self) -> None:
        """Clear/remove the checkpoint file."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            logger.info("Cleared pipeline checkpoint")

    def update_stage(self, stage: str, **kwargs: Any) -> None:
        """Update checkpoint with new stage information.

        Args:
            stage: New stage name
            **kwargs: Additional data to merge into state
        """
        data = self.load() or {
            "processed_files": [],
            "failed_files": [],
            "state": {},
        }

        data["stage"] = stage
        data["timestamp"] = datetime.now().isoformat()
        data["state"].update(kwargs)

        with self.checkpoint_file.open("w") as f:
            json.dump(data, f, indent=2)


def create_recovery_checkpoint(
    operation: str,
    data: dict[str, Any],
    checkpoint_dir: Path | None = None,
) -> Path:
    """Create a recovery checkpoint for an operation.

    Args:
        operation: Operation name/identifier
        data: Data to checkpoint
        checkpoint_dir: Optional checkpoint directory

    Returns:
        Path to checkpoint file
    """
    if checkpoint_dir is None:
        checkpoint_dir = Path.cwd() / ".checkpoints"

    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = (
        checkpoint_dir / f"{operation}_{datetime.now():%Y%m%d_%H%M%S}.checkpoint"
    )

    checkpoint_data = {
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }

    with checkpoint_file.open("w") as f:
        json.dump(checkpoint_data, f, indent=2)

    logger.info("Created recovery checkpoint: %s", checkpoint_file)
    return checkpoint_file
