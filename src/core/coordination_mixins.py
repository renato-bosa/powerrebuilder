"""Reusable mixins for coordinator classes.

This module provides mixins that extract common functionality from coordinator classes
to reduce duplication and make refactoring easier.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any


class StatisticsTracker:
    """Mixin for tracking statistics across coordinators."""

    def __init__(self) -> None:
        """Initialize statistics tracking."""
        self._stats: dict[str, Any] = self._create_default_stats()

    def _create_default_stats(self) -> dict[str, Any]:
        """Create default statistics dictionary.

        Override this method to customize stats for specific coordinators.
        """
        return {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get current statistics.

        Returns:
                    Copy of current statistics
        """
        return self._stats.copy()

    def reset_statistics(self) -> None:
        """Reset statistics to default values."""
        self._stats = self._create_default_stats()

    def increment_stat(self, key: str, amount: int = 1) -> None:
        """Increment a statistical counter.

        Args:
                    key: Statistic key to increment
                    amount: Amount to increment by (default: 1)
        """
        if key in self._stats and isinstance(self._stats[key], int | float):
            self._stats[key] += amount

    def add_error(self, error: str | Exception, context: str | None = None) -> None:
        """Add an error to statistics.

        Args:
            error: Error message or exception
            context: Optional context information
        """
        error_info = {
            "message": str(error),
            "type": type(error).__name__ if isinstance(error, Exception) else "error",
            "timestamp": datetime.now().isoformat(),
        }
        if context:
            error_info["context"] = context
        self._stats["errors"].append(error_info)
        self.increment_stat("failed")

    def add_warning(self, warning: str, context: str | None = None) -> None:
        """Add a warning to statistics.

        Args:
                    warning: Warning message
                    context: Optional context information
        """
        warning_info = {"message": warning, "timestamp": datetime.now().isoformat()}
        if context:
            warning_info["context"] = context
        self._stats["warnings"].append(warning_info)

    def finalize_stats(self) -> None:
        """Finalize statistics (set end time, calculate rates, etc.)."""
        self._stats["end_time"] = datetime.now().isoformat()

        # Calculate success rate
        total = self._stats.get("total_files", 0) or self._stats.get(
            "successful", 0
        ) + self._stats.get("failed", 0)
        if total > 0:
            self._stats["success_rate"] = (
                self._stats.get("successful", 0) / total
            ) * 100
        else:
            self._stats["success_rate"] = 0.0


class ProgressTracker:
    """Mixin for progress tracking and reporting."""

    def __init__(self) -> None:
        """Initialize progress tracking."""
        self._progress_callback: Callable[[str, float], None] | None = None
        self._current_operation: str | None = None
        self._total_steps: int = 0
        self._current_step: int = 0

    def set_progress_callback(
        self, callback: Callable[[str, float], None] | None
    ) -> None:
        """Set progress callback function.

        Args:
                    callback: Function that takes (message, progress_percentage)
        """
        self._progress_callback = callback

    def start_operation(self, operation: str, total_steps: int = 100) -> None:
        """Start a new operation for progress tracking.

        Args:
                    operation: Operation description
                    total_steps: Total number of steps in operation
        """
        self._current_operation = operation
        self._total_steps = total_steps
        self._current_step = 0
        self._report_progress(operation, 0)

    def update_progress(self, step: int, message: str | None = None) -> None:
        """Update progress for current operation.

        Args:
                    step: Current step number
                    message: Optional progress message
        """
        self._current_step = step
        percentage = (step / self._total_steps * 100) if self._total_steps > 0 else 0
        msg = message or self._current_operation or "Processing"
        self._report_progress(msg, percentage)

    def increment_progress(self, message: str | None = None) -> None:
        """Increment progress by one step.

        Args:
                    message: Optional progress message
        """
        self._current_step += 1
        self.update_progress(self._current_step, message)

    def complete_operation(self) -> None:
        """Mark current operation as complete."""
        if self._current_operation:
            self._report_progress(f"{self._current_operation} complete", 100)
            self._current_operation = None
            self._total_steps = 0
            self._current_step = 0

    def _report_progress(self, message: str, percentage: float) -> None:
        """Report progress to callback if available.

        Args:
                    message: Progress message
                    percentage: Progress percentage (0-100)
        """
        if self._progress_callback:
            try:
                self._progress_callback(message, percentage)
            except Exception as e:
                # Log but don't fail on progress callback errors
                if hasattr(self, "logger"):
                    getattr(self, "logger").debug("Progress callback error: %s", e)


class FileProcessor:
    """Mixin for common file processing operations."""

    def collect_files(
        self, input_path: Path, patterns: str | list[str], recursive: bool = True
    ) -> list[Path]:
        """Collect files matching patterns from input path.

        Args:
                    input_path: Directory to search
                    patterns: File pattern(s) to match
                    recursive: Whether to search recursively

        Returns:
                    List of matching file paths
        """
        if isinstance(patterns, str):
            patterns = [patterns]

            files = []

            # Handle single file input
        if input_path.is_file():
            for pattern in patterns:
                if input_path.match(pattern):
                    files.append(input_path)
                    break
            return files

        # Handle directory input
        for pattern in patterns:
            if recursive:
                files.extend(input_path.rglob(pattern))
            else:
                files.extend(input_path.glob(pattern))

        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for f in files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)

        return unique_files

    def process_files_batch(
        self,
        files: list[Path],
        processor: Callable[[Path], bool],
        batch_size: int = 100,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> tuple[int, int]:
        """Process files in batches.

        Args:
                    files: List of files to process
                    processor: Function to process each file (returns success boolean)
                    batch_size: Number of files per batch
                    progress_callback: Optional callback for progress updates

        Returns:
                    Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        total = len(files)

        for i in range(0, total, batch_size):
            batch = files[i : i + batch_size]

            for j, file_path in enumerate(batch):
                try:
                    if processor(file_path):
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    if hasattr(self, "logger"):
                        getattr(self, "logger").error("Failed to process %s: %s", file_path, e)

                if progress_callback:
                    progress_callback(i + j + 1, total)

        return successful, failed

    def ensure_output_structure(
        self, output_dir: Path, subdirs: list[str] | None = None
    ) -> None:
        """Ensure output directory structure exists.

        Args:
                    output_dir: Base output directory
                    subdirs: Optional list of subdirectories to create
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        if subdirs:
            for subdir in subdirs:
                (output_dir / subdir).mkdir(parents=True, exist_ok=True)

    def preserve_directory_structure(
        self,
        source_file: Path,
        source_root: Path,
        target_root: Path,
        new_extension: str | None = None,
    ) -> Path:
        """Calculate target path preserving directory structure.

        Args:
                    source_file: Source file path
                    source_root: Root directory of source
                    target_root: Root directory of target
                    new_extension: Optional new file extension

        Returns:
                    Target file path with preserved structure
        """
        try:
            relative_path = source_file.relative_to(source_root)
        except ValueError:
            # File is not under source_root, use just the filename
            relative_path = Path(source_file.name)

        target_path = target_root / relative_path

        if new_extension:
            target_path = target_path.with_suffix(new_extension)

        return target_path


class DualInitMixin:
    """Mixin for dual constructor pattern (simple vs DI).

    DEPRECATED: This pattern should be refactored to use proper dependency injection.
    Kept for backward compatibility during transition.
    """

    def _is_di_mode(self, *args) -> bool:
        """Detect if using dependency injection mode.

        Args:
                    *args: Constructor arguments

        Returns:
                    True if DI mode detected
        """
        # Check if first argument is not a string/Path (indicating DI mode)
        if args and len(args) > 0:
            first_arg = args[0]
            return not isinstance(first_arg, str | Path | type(None))
        return False

    def _validate_simple_args(self, required: list[str], **kwargs) -> None:
        """Validate required arguments for simple mode.

        Args:
                    required: List of required argument names
                    **kwargs: Arguments to validate

        Raises:
                    ValueError: If required arguments are missing
        """
        missing = [arg for arg in required if kwargs.get(arg) is None]
        if missing:
            raise ValueError(f"Missing required arguments for simple mode: {missing}")

    def _validate_di_services(self, required: list[str], **kwargs) -> None:
        """Validate required services for DI mode.

        Args:
                    required: List of required service names
                    **kwargs: Services to validate

        Raises:
                    ValueError: If required services are missing
        """
        missing = [svc for svc in required if kwargs.get(svc) is None]
        if missing:
            raise ValueError(f"Missing required services for DI mode: {missing}")


class CoordinatorMixin(
    StatisticsTracker, ProgressTracker, FileProcessor, DualInitMixin
):
    """Combined mixin providing all common coordinator functionality.

    This mixin combines all the individual mixins and provides additional
    coordinator-specific functionality.
    """

    def __init__(self) -> None:
        """Initialize all mixins."""
        StatisticsTracker.__init__(self)
        ProgressTracker.__init__(self)
        # FileProcessor and DualInitMixin don't need initialization

        # Set up logging if not already present
        if not hasattr(self, "logger"):
            self.logger = logging.getLogger(self.__class__.__name__)

    def validate_paths(
        self, input_path: Path | None = None, output_path: Path | None = None
    ) -> bool:
        """Validate input and output paths.

        Args:
                    input_path: Input path to validate
                    output_path: Output path to validate

        Returns:
                    True if paths are valid
        """
        # Use instance paths if not provided
        input_path = input_path or getattr(self, "input_path", None)
        output_path = output_path or getattr(self, "output_path", None)

        if not input_path:
            self.logger.error("No input path specified")
            return False

        if not output_path:
            self.logger.error("No output path specified")
            return False

        # Convert to Path objects if needed
        input_path = (
            Path(input_path) if not isinstance(input_path, Path) else input_path
        )
        output_path = (
            Path(output_path) if not isinstance(output_path, Path) else output_path
        )

        # Check input exists
        if not input_path.exists():
            self.logger.error("Input path does not exist: %s", input_path)
            return False

        # Try to create output directory
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error("Cannot create output directory %s: %s", output_path, e)
            return False

        return True

    def log_summary(self) -> None:
        """Log processing summary from statistics."""
        stats = self.get_statistics()

        self.logger.info("=" * 60)
        self.logger.info("Processing Summary:")
        self.logger.info("  Total files: %s", stats.get("total_files", 0))
        self.logger.info("  Successful: %s", stats.get("successful", 0))
        self.logger.info("  Failed: %s", stats.get("failed", 0))

        if "success_rate" in stats:
            self.logger.info("  Success rate: %.1f%%", stats["success_rate"])

        if stats.get("errors"):
            self.logger.warning("  Errors encountered: %s", len(stats["errors"]))
            for i, error in enumerate(stats["errors"][:5]):  # Show first 5 errors
                self.logger.warning(
                    "    %s. %s", i + 1, error.get("message", "Unknown error")
                )
            if len(stats["errors"]) > 5:
                self.logger.warning(
                    "    ... and %s more errors", len(stats["errors"]) - 5
                )

        self.logger.info("=" * 60)

    def write_report(
        self,
        output_dir: Path | None = None,
        filename: str = "processing_report.json",
    ) -> None:
        """Write processing report to file.

        Args:
                    output_dir: Directory to write report (uses instance output_dir if not provided)
                    filename: Report filename
        """
        output_dir = (
            output_dir
            or getattr(self, "output_dir", None)
            or getattr(self, "output_path", None)
        )
        if not output_dir:
            self.logger.warning("No output directory available for report")
            return

        output_dir = (
            Path(output_dir) if not isinstance(output_dir, Path) else output_dir
        )
        report_path = output_dir / filename

        try:
            self.finalize_stats()
            stats = self.get_statistics()

            # Add metadata
            stats["report_generated"] = datetime.now().isoformat()
            stats["coordinator"] = self.__class__.__name__

            with report_path.open("w") as f:
                json.dump(stats, f, indent=2, default=str)

            self.logger.info("Processing report written to: %s", report_path)
        except Exception as e:
            self.logger.error("Failed to write report: %s", e)


class ServiceValidationMixin:
    """Mixin for validating injected services in DI mode."""

    def validate_service(self, service: Any, interface: Any, name: str) -> bool:
        """Validate that a service implements required interface.

        Args:
                    service: Service instance to validate
                    interface: Expected interface/protocol
                    name: Service name for error messages

        Returns:
                    True if valid
        """
        if service is None:
            if hasattr(self, "logger"):
                getattr(self, "logger").error("Service '%s' is None", name)
            return False

        # Check for required methods if interface is available
        if interface and hasattr(interface, "__abstractmethods__"):
            missing = []
            for method in interface.__abstractmethods__:
                if not hasattr(service, method):
                    missing.append(method)

            if missing:
                if hasattr(self, "logger"):
                    getattr(self, "logger").error(
                        "Service '%s' missing required methods: %s", name, missing
                    )
                return False

        return True

    def validate_all_services(self, services: dict[str, tuple[Any, Any]]) -> bool:
        """Validate all services.

        Args:
                    services: Dict mapping service name to (service, interface) tuple

        Returns:
                    True if all services are valid
        """
        all_valid = True
        for name, (service, interface) in services.items():
            if not self.validate_service(service, interface, name):
                all_valid = False
        return all_valid
