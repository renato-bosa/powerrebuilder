"""Progress adapter to bridge pipeline progress tracking with stage-specific interfaces."""

from collections.abc import Callable
from pathlib import Path

from src.common.pipeline.progress import ProgressCallback
from src.contracts.interfaces import IProgressReporter


class PipelineProgressAdapter(IProgressReporter):
    """Adapter to bridge PipelineProgress callbacks to IProgressReporter interface."""

    def __init__(self, progress_callback: ProgressCallback | None = None) -> None:
        """Initialize the adapter.

        Args:
            progress_callback: Callback function for progress updates
        """
        self.progress_callback = progress_callback
        self._current_file: Path | None = None
        self._total_entries = 0
        self._completed_entries = 0

    def start_file(self, file_path: Path, total_entries: int) -> None:
        """Start processing a new file.

        Args:
            file_path: File being processed
            total_entries: Total number of entries to extract
        """
        self._current_file = file_path
        self._total_entries = total_entries
        self._completed_entries = 0

        if self.progress_callback:
            self.progress_callback(0, total_entries, f"Starting {file_path.name}")

    def update_progress(self, completed_entries: int) -> None:
        """Update extraction progress.

        Args:
            completed_entries: Number of entries completed
        """
        self._completed_entries = completed_entries

        if self.progress_callback and self._current_file:
            message = f"Extracting {self._current_file.name}: {completed_entries}/{self._total_entries}"
            self.progress_callback(completed_entries, self._total_entries, message)

    def report_error(self, error: str) -> None:
        """Report an extraction error.

        Args:
            error: Error message
        """
        if self.progress_callback and self._current_file:
            message = f"Error in {self._current_file.name}: {error}"
            self.progress_callback(
                self._completed_entries, self._total_entries, message
            )

    def finish_file(self) -> None:
        """Finish processing the current file."""
        if self.progress_callback and self._current_file:
            message = f"Completed {self._current_file.name}"
            self.progress_callback(self._total_entries, self._total_entries, message)

        self._current_file = None
        self._total_entries = 0
        self._completed_entries = 0

    # Compatibility methods for different naming conventions
    def report_file_start(self, file_path: str) -> None:
        """Start processing a file (string path variant)."""
        self.start_file(Path(file_path), 0)

    def report_file_complete(self, file_path: str) -> None:
        """Complete processing a file (string path variant)."""
        self.finish_file()

    def set_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Set the progress callback.

        Args:
            callback: Progress callback function
        """
        self.progress_callback = callback


def create_progress_callback_adapter(
    callback: Callable[[int, int, str], None] | None,
) -> PipelineProgressAdapter | None:
    """Create a progress adapter from a simple callback function.

    Args:
        callback: Progress callback function (current, total, message)

    Returns:
        Progress adapter or None if no callback provided
    """
    if callback is None:
        return None

    return PipelineProgressAdapter(callback)
