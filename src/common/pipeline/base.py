"""Common pipeline utilities and base classes.

This module provides base classes and utilities for pipeline stages
to reduce code duplication across coordinators.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class ProgressTracker(Protocol):
    """Protocol for progress tracking objects."""
    
    def update(self, n: int = 1, description: str | None = None) -> None:
        """Update progress incrementally by n items."""
        ...
        
    def set_progress(self, value: int, description: str | None = None) -> None:
        """Set progress to an absolute value."""
        ...
        
    def finish(self) -> None:
        """Finish progress tracking."""
        ...
    
    def increment(self) -> None:
        """Increment progress by one item."""
        ...
    
    def __enter__(self) -> "ProgressTracker":
        """Enter context manager."""
        ...
    
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager."""
        ...


class PipelineStage(ABC):
    """Base class for all pipeline stages (coordinators).

    Provides common functionality for:
    - Directory handling
    - Progress tracking
    - Error handling
    - Summary generation
    """

    def __init__(self, stage_name: str) -> None:
        """Initialize pipeline stage.

        Args:
            stage_name: Name of this pipeline stage (e.g., 'extract', 'parse')
        """
        self.stage_name = stage_name
        self.logger = logging.getLogger(f"{__name__}.{stage_name}")

    def ensure_directory(self, path: Path) -> Path:
        """Ensure directory exists, creating if necessary.

        Args:
            path: Directory path

        Returns:
            The path object for chaining
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    @abstractmethod
    def process_file(self, input_file: Path, output_dir: Path) -> dict[str, Any]:
        """Process a single file.

        Args:
            input_file: Input file path
            output_dir: Output directory path

        Returns:
            Dictionary with processing results

        Raises:
            Exception: If processing fails
        """

    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        pattern: str = "*",
        *,
        recursive: bool = True,
        progress: bool = True,
    ) -> dict[str, Any]:
        """Process all matching files in a directory.

        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            pattern: File pattern to match (e.g., "*.pbd")
            recursive: Whether to search recursively
            progress: Whether to show progress

        Returns:
            Summary dictionary with processing results
        """
        # Ensure paths are Path objects
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)

        # Ensure output directory exists
        self.ensure_directory(output_dir)

        # Find files
        if recursive:
            files = list(input_dir.rglob(pattern))
        else:
            files = list(input_dir.glob(pattern))

        # Initialize summary
        summary = PipelineSummary(self.stage_name, input_dir, output_dir)

        # Get progress tracker
        tracker = self._get_progress_tracker(len(files), enabled=progress)

        # Process files
        with tracker:
            for file_path in files:
                try:
                    # Process file
                    result = self.process_file(file_path, output_dir)
                    summary.add_success(file_path, result)

                except Exception as e:
                    self.logger.exception("Failed to process %s", file_path)
                    summary.add_failure(file_path, str(e))

                finally:
                    if hasattr(tracker, "increment"):
                        tracker.increment()
                    else:
                        tracker.update(1)  # For compatibility

        return summary.generate()

    def _get_progress_tracker(self, total: int, *, enabled: bool = True) -> ProgressTracker:
        """Get appropriate progress tracker.

        Args:
            total: Total number of items
            enabled: Whether progress tracking is enabled

        Returns:
            Progress tracker instance
        """
        try:
            from src.extract.pbd.progress import (
                SilentProgressTracker,
                TqdmProgressTracker,
            )

            if enabled and total > 0:
                return TqdmProgressTracker(
                    total=total,
                    description=f"{self.stage_name.capitalize()} progress",
                )
            return SilentProgressTracker(
                total=total,
                description=f"{self.stage_name.capitalize()} progress",
            )
        except ImportError:
            # Fallback to no-op progress tracker
            return NoOpProgressTracker()

    def save_summary(self, summary: dict[str, Any], output_dir: Path) -> Path:
        """Save processing summary to JSON file.

        Args:
            summary: Summary dictionary
            output_dir: Output directory

        Returns:
            Path to saved summary file
        """
        summary_file = output_dir / f"{self.stage_name}_summary.json"

        with summary_file.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        self.logger.info("Saved %s summary to %s", self.stage_name, summary_file)
        return summary_file


class PipelineSummary:
    """Standardized summary generation for pipeline stages."""

    def __init__(self, stage_name: str, input_dir: Path, output_dir: Path) -> None:
        """Initialize summary.

        Args:
            stage_name: Name of pipeline stage
            input_dir: Input directory
            output_dir: Output directory
        """
        self.stage_name = stage_name
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.start_time = datetime.now(UTC)
        self.success_count = 0
        self.failure_count = 0
        self.results: list[dict[str, Any]] = []
        self.errors: list[dict[str, str]] = []

    def add_success(
        self,
        file_path: Path,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Record successful processing.

        Args:
            file_path: File that was processed
            result: Optional result data
        """
        self.success_count += 1

        if result:
            self.results.append(
                {
                    "file": str(file_path),
                    "status": "success",
                    **result,
                },
            )

    def add_failure(self, file_path: Path, error: str) -> None:
        """Record processing failure.

        Args:
            file_path: File that failed
            error: Error message
        """
        self.failure_count += 1
        self.errors.append(
            {
                "file": str(file_path),
                "error": error,
            },
        )

    def generate(self) -> dict[str, Any]:
        """Generate final summary.

        Returns:
            Summary dictionary
        """
        duration = (datetime.now(UTC) - self.start_time).total_seconds()

        return {
            "stage": self.stage_name,
            "processed_at": self.start_time.isoformat(),
            "duration_seconds": duration,
            "input_directory": str(self.input_dir),
            "output_directory": str(self.output_dir),
            "statistics": {
                "total_files": self.success_count + self.failure_count,
                "successful": self.success_count,
                "failed": self.failure_count,
                "success_rate": (
                    self.success_count / (self.success_count + self.failure_count)
                    if (self.success_count + self.failure_count) > 0
                    else 0.0
                ),
            },
            "results": self.results if self.results else None,
            "errors": self.errors if self.errors else None,
        }


class NoOpProgressTracker:
    """No-operation progress tracker for when tqdm is not available."""

    def __enter__(self) -> "NoOpProgressTracker":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """No-op exit."""

    def update(self, n: int = 1, description: str | None = None) -> None:
        """No-op update."""

    def set_progress(self, value: int, description: str | None = None) -> None:
        """No-op set progress."""

    def set_total(self, total: int) -> None:
        """No-op set total."""

    def set_description(self, desc: str) -> None:
        """No-op set description."""

    def close(self) -> None:
        """No-op close."""

    def finish(self) -> None:
        """No-op finish."""
    
    def increment(self) -> None:
        """No-op increment."""
