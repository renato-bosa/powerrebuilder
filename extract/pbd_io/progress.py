import sys
import time
from typing import Any, TextIO

from tqdm.auto import tqdm  # Use tqdm.auto for flexible environment (CLI, notebook)

# PowerBuilder source file extensions
SOURCE_EXTENSIONS = [
    ".srd", ".srs", ".srw", ".sru", ".srf", ".srm", ".srx", ".srj", ".srp", ".srq", ".sra",
]

# PowerBuilder resource file extensions
RESOURCE_EXTENSIONS = [
    ".bmp", ".jpg", ".jpeg", ".gif", ".png", ".ico", ".cur", ".wav", ".mp3", ".bin",
]


class BaseProgressTracker:
    """Base class for progress tracking implementations."""
    def __init__(self,
                 total: int | None = None,
                 description: str | None = None,
                 unit: str = "it",
                 **kwargs: Any) -> None:
        self.total = total
        self.description = description
        self.unit = unit
        self.current_value = 0
        self.kwargs = kwargs  # Store unused kwargs for potential use by subclasses

    def update(self, value: int, item_name: str | None = None) -> None:
        """Update the progress. 'value' is the new absolute progress value."""
        raise NotImplementedError

    def increment(self, amount: int = 1, item_name: str | None = None) -> None:
        """Increment progress by a certain amount."""
        self.current_value += amount
        self.update(self.current_value, item_name)

    def finish(self) -> None:
        """Mark progress as finished."""
        raise NotImplementedError

    def close(self) -> None:
        """Close any underlying resources (like tqdm progress bar)."""
        # Base implementation can be a no-op
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # Do not suppress exceptions


class TqdmProgressTracker(BaseProgressTracker):
    """Progress tracker using tqdm for visual output."""
    def __init__(self,
                 total: int | None = None,
                 description: str | None = None,
                 unit: str = "it",
                 show_item_name_on_update: bool = False,
                 **kwargs: Any) -> None:
        super().__init__(total=total, description=description, unit=unit, **kwargs)
        self.show_item_name_on_update = show_item_name_on_update
        self.pbar = tqdm(
            total=self.total,
            desc=self.description,
            unit=self.unit,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]",
            disable=self.kwargs.get('disable', False),  # Use stored kwargs
        )
        # self.start_time = time.time() # tqdm handles its own timing
        # self.items_processed = 0 # tqdm.n tracks this
        # self.bytes_processed = 0 # Not directly handled by this base tqdm wrapper

    def update(self, value: int, item_name: str | None = None) -> None:
        """Update the progress bar to a new absolute value.
        The 'value' parameter here represents the new count of items processed.
        """
        if self.pbar:
            increment = value - self.pbar.n
            self.pbar.update(increment)

            if self.show_item_name_on_update and item_name:
                self.pbar.set_postfix_str(f"Current: {item_name[:30]}", refresh=True)
            elif self.pbar.postfix:  # Clear postfix if no item name
                 self.pbar.set_postfix_str("")

    def increment(self, amount: int = 1, item_name: str | None = None) -> None:
        """Increment progress by a certain amount."""
        if self.pbar:
            self.pbar.update(amount)
            if self.show_item_name_on_update and item_name:
                self.pbar.set_postfix_str(f"Current: {item_name[:30]}", refresh=True)
            elif self.pbar.postfix:
                 self.pbar.set_postfix_str("")
        # Note: No call to super().increment() as tqdm handles the count internally.
        # self.current_value = self.pbar.n # Sync if needed, but BaseProgressTracker.current_value is not used by TqdmProgressTracker

    def finish(self) -> None:
        if self.pbar:
            if self.total is not None and self.pbar.n < self.total:
                self.pbar.update(self.total - self.pbar.n)
            self.pbar.set_postfix_str("Done.", refresh=True)
            # Closing is handled by self.close() or __exit__

    def close(self) -> None:
        if self.pbar:
            self.pbar.close()
            self.pbar = None  # type: ignore


class SilentProgressTracker(BaseProgressTracker):
    """A progress tracker that does nothing, for silent/headless runs."""
    def __init__(self,
                 total: int | None = None,
                 description: str | None = None,
                 unit: str = "it",
                 **kwargs: Any) -> None:
        super().__init__(total=total, description=description, unit=unit, **kwargs)
        # No setup needed

    def update(self, value: int, item_name: str | None = None) -> None:
        # Do nothing
        self.current_value = value  # Still update internal state for completeness

    def finish(self) -> None:
        # Do nothing
        pass

    def close(self) -> None:
        # Do nothing
        pass


# Alias for easier default usage.
# Users can explicitly import TqdmProgressTracker or SilentProgressTracker if needed.
ProgressTracker = TqdmProgressTracker


class ProgressTracker:
    """Tracks and displays progress for long-running operations.

    Provides real-time feedback during PBL/PBD extraction including:
    - Percentage completion
    - Visual progress bar
    - Files processed
    - Estimated time remaining
    """

    def __init__(self, total: int, description: str = "Processing", file: TextIO | None = sys.stdout, bar_length: int = 50, unit: str = "items") -> None:
        """Initialize a progress tracker.

        Args:
            total: Total number of items to process
            description: Description of the operation
            file: Output stream (e.g., sys.stdout). If None, output is suppressed.
            bar_length: Length of the progress bar in characters
            unit: Unit name for the items being processed
        """
        self.total = total
        self.description = description
        self.file: TextIO | None = file
        self.bar_length = bar_length
        self.unit = unit
        self.start_time = time.time()
        self.last_update_time = 0
        self.processed = 0
        self.last_printed_length = 0
        self.update_interval = 0.2  # seconds between updates to avoid excessive printing
        self.file_size = None
        self.bytes_processed = 0

    def update(self, progress: int, item_name: str = "", bytes_processed: int | None = None) -> None:
        """Update the progress and redraw the progress bar.

        Args:
            progress: Number of items processed
            item_name: Name of the current item being processed
            bytes_processed: Optional number of bytes processed for this increment
        """
        self.processed = progress

        # Throttle updates to avoid too frequent redraws
        current_time = time.time()
        if (current_time - self.last_update_time < self.update_interval) and progress < self.total:
            return

        self.last_update_time = current_time

        # Calculate percentage and bar
        percentage = min(100, (self.processed * 100) // self.total if self.total > 0 else 100)
        filled_length = int(self.bar_length * self.processed // self.total) if self.total > 0 else self.bar_length
        bar = '█' * filled_length + '░' * (self.bar_length - filled_length)

        # Calculate time information
        elapsed = current_time - self.start_time
        if progress > 0 and progress < self.total:
            remaining = (elapsed / progress) * (self.total - progress)
            time_info = f"ETA: {self._format_time(remaining)} | Elapsed: {self._format_time(elapsed)}"
        else:
            time_info = f"Elapsed: {self._format_time(elapsed)}"

        # Format the progress message
        if item_name:
            progress_message = f"\r{self.description}: [{bar}] {percentage}% | {self.processed}/{self.total} | {item_name} | {time_info}"
        else:
            progress_message = f"\r{self.description}: [{bar}] {percentage}% | {self.processed}/{self.total} | {time_info}"

        if not self.file:
            return

        # Clear previous line and print new progress
        if self.last_printed_length > len(progress_message):
            self.file.write(' ' * self.last_printed_length + '\r')

        self.file.write(progress_message)
        self.file.flush()
        self.last_printed_length = len(progress_message)

        # Print newline when done
        if self.processed >= self.total:
            self.file.write('\n')

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to a human-readable string.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (e.g., "3m 45s" or "1h 23m")
        """
        if seconds < 1:
            return "0s"

        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)

        if h > 0:
            return f"{h}h {m}m"
        if m > 0:
            return f"{m}m {s}s"
        return f"{s}s"

    def _format_byte_rate(self, bytes_per_sec: float) -> str:
        """Format bytes per second to a human-readable string.

        Args:
            bytes_per_sec: Bytes per second

        Returns:
            Formatted byte rate string (e.g., "1.2 MB/s")
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = bytes_per_sec
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}/s"

    def _format_size(self, num_bytes: int) -> str:
        """Format byte size to a human-readable string (e.g., 1.2 MB)."""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(num_bytes)
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.1f} {units[unit_index]}"

    def increment(self, item_name: str = "", bytes_processed: int | None = None) -> None:
        """Increment progress by 1 and update the display.

        Args:
            item_name: Name of the current item being processed
            bytes_processed: Optional number of bytes processed for this increment
        """
        self.update(self.processed + 1, item_name, bytes_processed)

    def finish(self, show_summary: bool = True) -> None:
        """Mark the progress as complete and display final stats.

        Args:
            show_summary: Whether to show a summary of the operation
        """
        self.update(self.total)  # Ensure bar is 100% full

        if not self.file:
            return

        if show_summary:
            elapsed = time.time() - self.start_time
            items_per_second = self.total / elapsed if elapsed > 0 else 0

            summary = f"{self.description} completed in {self._format_time(elapsed)} "
            summary += f"({items_per_second:.2f} {self.unit}/sec)"

            if self.file_size and self.bytes_processed > 0 and elapsed > 0:
                bytes_per_sec = self.bytes_processed / elapsed
                summary += f" | {self._format_byte_rate(bytes_per_sec)}"

                # Add percentage of original file size if we processed fewer bytes than the file size
                if self.bytes_processed < self.file_size:
                    percentage_processed = (self.bytes_processed / self.file_size) * 100
                    summary += f" | {self._format_size(self.bytes_processed)} of {self._format_size(self.file_size)} ({percentage_processed:.1f}%)"
                else:
                    summary += f" | {self._format_size(self.bytes_processed)} processed"

            self.file.write(summary + "\n")
            self.file.flush()
