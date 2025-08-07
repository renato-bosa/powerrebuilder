"""Base coordinator interface for all pipeline stages."""

import json
import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager, suppress
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.coordination_mixins import CoordinatorMixin
from src.core.exceptions import CoordinatorError

# Try to import ResourceMonitor (correct class name), but make it optional
try:
    from src.core.resource_limits import ResourceMonitor as ResourceLimiter
except ImportError:
    ResourceLimiter = None  # type: ignore

logger = logging.getLogger(__name__)


class BaseCoordinator(ABC):
    """Base coordinator interface for all pipeline stages.

    Provides common functionality for all coordinators including:
    - Statistics tracking
    - Progress reporting
    - Error handling
    - File management
    - Validation
    """

    def __init__(self, input_path: Path, output_path: Path) -> None:
        """Initialize base coordinator.

        Args:
            input_path: Path to input directory/file
            output_path: Path to output directory
        """
        self.input_path = input_path
        self.output_path = output_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self._statistics: dict[str, Any] = {
            "files_processed": 0,
            "files_failed": 0,
            "errors": [],
            "warnings": [],
        }

    @abstractmethod
    def process(self) -> dict[str, Any]:
        """Process input files and produce output.

        Returns:
            Dictionary containing processing statistics
        """

    @abstractmethod
    def validate_inputs(self) -> bool:
        """Validate input requirements for the stage.

        Returns:
            True if inputs are valid, False otherwise
        """

    def get_statistics(self) -> dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary containing current statistics
        """
        return self._statistics.copy()

    def add_error(self, error: str | Exception, context: str | None = None) -> None:
        """Add an error to statistics.

        Args:
            error: Error message or exception
            context: Optional context information (file path or other context)
        """
        error_info = {"message": str(error)}
        if context:
            error_info["context"] = context
        self._statistics["errors"].append(error_info)
        self._statistics["files_failed"] += 1

    def add_warning(self, warning: str, context: str | None = None) -> None:
        """Add a warning to statistics.

        Args:
            warning: Warning message
            context: Optional context information (file path or other context)
        """
        warning_info = {"message": warning}
        if context:
            warning_info["context"] = context
        self._statistics["warnings"].append(warning_info)

    def increment_processed(self) -> None:
        """Increment the processed files counter."""
        self._statistics["files_processed"] += 1
        # Also update the 'successful' counter for compatibility
        if "successful" in self._statistics:
            self._statistics["successful"] += 1

    def ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_path.mkdir(parents=True, exist_ok=True)

    def get_input_files(self, pattern: str = "*") -> list[Path]:
        """Get list of input files matching pattern.

        Args:
            pattern: Glob pattern for file matching

        Returns:
            List of matching file paths
        """
        if self.input_path.is_file():
            return [self.input_path] if self.input_path.match(pattern) else []
        return list(self.input_path.glob(pattern))

    @contextmanager
    def resource_context(self, memory_limit_mb: int = 1024):
        """Context manager for resource-limited execution.

        Args:
            memory_limit_mb: Memory limit in megabytes

        Yields:
            ResourceLimiter instance or None if not available
        """
        # TODO: Implement resource limiting with ResourceLimiter
        # For now, always yield None regardless of ResourceLimiter availability
        yield None

    def handle_error(self, error: Exception, context: str | None = None) -> None:
        """Handle errors with consistent logging and tracking.

        Args:
            error: The exception that occurred
            context: Optional context information
        """
        error_msg = f"{type(error).__name__}: {str(error)}"
        if context:
            error_msg = f"{context}: {error_msg}"

        self.logger.error(error_msg)
        self.add_error(error, context)

    def validate_file_access(self, file_path: Path) -> bool:
        """Validate that a file can be accessed safely.

        Args:
            file_path: Path to validate

        Returns:
            True if file is accessible, False otherwise
        """
        try:
            # Check if file exists
            if not file_path.exists():
                self.logger.error("File does not exist: %s", file_path)
                return False

            # Check if it's a regular file
            if not file_path.is_file():
                self.logger.error("Not a regular file: %s", file_path)
                return False

            # Check read permissions
            if not os.access(file_path, os.R_OK):
                self.logger.error("No read permission for file: %s", file_path)
                return False

            return True

        except Exception as e:
            self.logger.error("Error validating file access for %s: %s", file_path, e)
            return False


class EnhancedCoordinator(BaseCoordinator, CoordinatorMixin):
    """Enhanced base coordinator with mixin functionality.

    This class combines the abstract BaseCoordinator with the CoordinatorMixin
    to provide a rich set of functionality for pipeline coordinators.

    Subclasses should inherit from this instead of BaseCoordinator to get
    all the mixin functionality automatically.
    """

    def __init__(
        self,
        input_path: str | Path,
        output_path: str | Path,
        enable_checkpointing: bool = False,
        checkpoint_interval: int = 100,
    ) -> None:
        """Initialize enhanced coordinator.

        Args:
            input_path: Path to input directory/file
            output_path: Path to output directory
            enable_checkpointing: Whether to enable checkpoint/recovery
            checkpoint_interval: Number of files between checkpoints
        """
        # Convert to Path objects
        input_path = Path(input_path) if isinstance(input_path, str) else input_path
        output_path = Path(output_path) if isinstance(output_path, str) else output_path

        # Initialize base class
        BaseCoordinator.__init__(self, input_path, output_path)

        # Initialize mixin
        CoordinatorMixin.__init__(self)

        # Checkpoint settings
        self.enable_checkpointing = enable_checkpointing
        self.checkpoint_interval = checkpoint_interval
        self._checkpoint_file = self.output_path / ".checkpoint.json"
        self._processed_files: set[str] = set()

    def validate_inputs(self) -> bool:
        """Validate input requirements for the stage.

        Returns:
            True if inputs are valid, False otherwise
        """
        return self.validate_paths(self.input_path, self.output_path)

    def run(
        self, progress_callback: Callable[[str, float], None] | None = None
    ) -> dict[str, Any]:
        """Run the coordinator with optional progress tracking.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Processing statistics
        """
        self.set_progress_callback(progress_callback)

        try:
            # Load checkpoint if enabled
            self.load_checkpoint()

            # Validate inputs
            if not self.validate_inputs():
                raise CoordinatorError("Input validation failed")

            # Start timing
            start_time = datetime.now()

            # Run processing
            self.logger.info("Starting %s processing", self.__class__.__name__)
            self.logger.info("Input: %s", self.input_path)
            self.logger.info("Output: %s", self.output_path)

            result = self.process()

            # Save final checkpoint
            if self.enable_checkpointing:
                self.save_checkpoint()

            # Finalize statistics
            self.finalize_stats()

            # Log summary
            self.log_summary()

            # Write report
            self.write_report()

            # Add timing info
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            result["duration_seconds"] = duration

            # Clean up checkpoint file on successful completion
            if self.enable_checkpointing and self._checkpoint_file.exists():
                try:
                    self._checkpoint_file.unlink()
                except Exception:
                    pass  # Not critical if cleanup fails

            return result

        except Exception as e:
            self.logger.error("Processing failed: %s", e)
            self.add_error(str(e))
            # Save checkpoint on failure for recovery
            if self.enable_checkpointing:
                self.save_checkpoint()
            raise

    def process_file_with_error_handling(
        self,
        file_path: Path,
        processor: Callable[[Path], Any],
        error_context: str | None = None,
    ) -> bool:
        """Process a single file with error handling.

        Args:
            file_path: File to process
            processor: Function to process the file
            error_context: Optional context for error messages

        Returns:
            True if successful, False otherwise
        """
        try:
            processor(file_path)
            self.increment_stat("successful")
            self.increment_processed()  # Also update base counter
            return True
        except Exception as e:
            context = error_context or f"processing {file_path.name}"
            self.logger.error("Error %s: %s", context, e)
            self.add_error(str(e), str(file_path))
            return False

    def load_checkpoint(self) -> None:
        """Load checkpoint data if it exists."""
        if not self.enable_checkpointing:
            return

        if self._checkpoint_file.exists():
            try:
                with self._checkpoint_file.open("r") as f:
                    checkpoint_data = json.load(f)
                    self._processed_files = set(
                        checkpoint_data.get("processed_files", [])
                    )
                    # Restore statistics
                    if "statistics" in checkpoint_data:
                        self._statistics.update(checkpoint_data["statistics"])
                self.logger.info(
                    "Loaded checkpoint with %d processed files",
                    len(self._processed_files),
                )
            except Exception as e:
                self.logger.warning("Failed to load checkpoint: %s", e)

    def save_checkpoint(self) -> None:
        """Save checkpoint data."""
        if not self.enable_checkpointing:
            return

        try:
            checkpoint_data = {
                "processed_files": list(self._processed_files),
                "statistics": self.get_statistics(),
                "timestamp": datetime.now().isoformat(),
            }
            with self._checkpoint_file.open("w") as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            self.logger.warning("Failed to save checkpoint: %s", e)

    def should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped based on checkpoint.

        Args:
            file_path: File to check

        Returns:
            True if file should be skipped
        """
        if not self.enable_checkpointing:
            return False
        return str(file_path) in self._processed_files

    def mark_file_processed(self, file_path: Path) -> None:
        """Mark a file as processed for checkpointing.

        Args:
            file_path: File that was processed
        """
        if self.enable_checkpointing:
            self._processed_files.add(str(file_path))
            # Save checkpoint at intervals
            if len(self._processed_files) % self.checkpoint_interval == 0:
                self.save_checkpoint()

    def get_pipeline_config(self) -> dict[str, Any]:
        """Get configuration for pipeline integration.

        Returns:
            Dictionary with pipeline configuration
        """
        return {
            "stage": self.__class__.__name__.replace("Coordinator", "").lower(),
            "input_path": str(self.input_path),
            "output_path": str(self.output_path),
            "enable_checkpointing": self.enable_checkpointing,
            "supports_parallel": getattr(self, "supports_parallel", False),
            "supports_streaming": getattr(self, "supports_streaming", False),
        }

    def prepare_for_pipeline(self) -> None:
        """Prepare coordinator for pipeline execution."""
        # Ensure output directory exists
        self.ensure_output_dir()

        # Load checkpoint if resuming
        if self.enable_checkpointing:
            self.load_checkpoint()

        # Validate inputs
        if not self.validate_inputs():
            raise CoordinatorError("Pipeline preparation failed: invalid inputs")

    def cleanup_after_pipeline(self) -> None:
        """Clean up after pipeline execution."""
        # Save final statistics
        self.finalize_stats()

        # Write report
        self.write_report()

        # Clean up checkpoint on success
        if self.enable_checkpointing and self._checkpoint_file.exists():
            with suppress(Exception):
                self._checkpoint_file.unlink()


class SimpleDICoordinator(EnhancedCoordinator):
    """Base coordinator supporting both simple and DI construction patterns.

    This class provides a template for coordinators that need to support
    both simple construction (for backward compatibility) and dependency
    injection patterns.

    DEPRECATED: New coordinators should use proper DI exclusively.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize coordinator with dual pattern support.

        Subclasses should override _init_simple and _init_with_services methods.
        """
        # Detect which pattern is being used
        if self._is_di_mode(*args):
            self._init_with_services(*args, **kwargs)
        else:
            self._init_simple(*args, **kwargs)

    def _is_di_mode(self, *args) -> bool:
        """Detect if constructor is being called with DI pattern.

        Override this method in subclasses to implement custom detection logic.

        Args:
            *args: Constructor arguments

        Returns:
            True if DI mode, False for simple mode
        """
        # Default implementation: check if first arg is not a string/Path
        if not args:
            return False
        return not isinstance(args[0], (str, Path))

    def _init_simple(self, *args, **kwargs) -> None:
        """Initialize with simple constructor pattern.

        This is a template method that subclasses should override to handle
        simple construction patterns (typically with file paths).

        Args:
            *args: Positional arguments (typically input_path, output_path)
            **kwargs: Keyword arguments
        """
        # Default implementation for backward compatibility
        if len(args) >= 2:
            input_path = Path(args[0]) if isinstance(args[0], str) else args[0]
            output_path = Path(args[1]) if isinstance(args[1], str) else args[1]
        else:
            input_path = kwargs.get("input_path")
            output_path = kwargs.get("output_path")
            if input_path:
                input_path = (
                    Path(input_path) if isinstance(input_path, str) else input_path
                )
            if output_path:
                output_path = (
                    Path(output_path) if isinstance(output_path, str) else output_path
                )

        if not input_path or not output_path:
            raise ValueError("SimpleDICoordinator requires input_path and output_path")

        # Initialize parent with paths
        super().__init__(input_path, output_path)

    def _init_with_services(self, *args, **kwargs) -> None:
        """Initialize with dependency injection pattern.

        This is a template method that subclasses should override to handle
        dependency injection construction patterns.

        Args:
            *args: Service instances
            **kwargs: Additional configuration including input_path and output_path
        """
        # Extract paths from kwargs for DI mode
        input_path = kwargs.get("input_path")
        output_path = kwargs.get("output_path")

        if not input_path or not output_path:
            # Try to get from positional args if they're paths
            for arg in args:
                if isinstance(arg, (str, Path)):
                    if not input_path:
                        input_path = arg
                    elif not output_path:
                        output_path = arg
                        break

        if not input_path or not output_path:
            raise ValueError("DI mode requires input_path and output_path in kwargs")

        input_path = Path(input_path) if isinstance(input_path, str) else input_path
        output_path = Path(output_path) if isinstance(output_path, str) else output_path

        # Initialize parent with paths
        super().__init__(input_path, output_path)
