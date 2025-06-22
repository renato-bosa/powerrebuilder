from typing import Any

from tqdm.auto import tqdm  # Use tqdm.auto for flexible environment (CLI, notebook)
from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET


class BaseProgressTracker:
    """Base class for progress tracking implementations."""

    def __init__(
        self, total: int | None = None, description: str | None = None, unit: str = "it", **kwargs: Any, ) -> None:
        

        self.total = total
        self.description = description
        self.unit = unit
        self.current_value = 0
        self.kwargs = kwargs  # Store unused kwargs for potential use by subclasses

    def update(self, value: int, item_name: str | None = None) -> None:


        

        """Update the progress. 'value' is the new absolute progress value."""
        # Default implementation: just track the value
        self.current_value = value
        # Subclasses should override to provide visual feedback

    def increment(self, amount: int = 1, item_name: str | None = None) -> None:


        

        """Increment progress by a certain amount."""
        self.current_value += amount
        self.update(self.current_value, item_name)

    def finish(self) -> None:


        

        """Mark progress as finished."""
        # Default implementation: set progress to total if available
        if self.total is not None:
            self.current_value = self.total
        # Subclasses should override to provide visual feedback

    def close(self) -> None:


        

        """Close any underlying resources (like tqdm progress bar)."""
        # Base implementation can be a no-op

    def __enter__(self) -> None:
        

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        

        self.close()
        return False  # Do not suppress exceptions


class TqdmProgressTracker(BaseProgressTracker):
    """Progress tracker using tqdm for visual output."""

    def __init__(
        self, total: int | None = None, description: str | None = None, unit: str = "it", show_item_name_on_update: bool = False, **kwargs: Any, ) -> None:
        

        super().__init__(total=total, description=description, unit=unit, **kwargs)
        self.show_item_name_on_update = show_item_name_on_update
        self.pbar = tqdm(
            total=self.total, desc=self.description, unit=self.unit, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]", disable=self.kwargs.get("disable", False), # Use stored kwargs
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

    def __init__(
        self, total: int | None = None, description: str | None = None, unit: str = "it", **kwargs: Any, ) -> None:
        

        super().__init__(total=total, description=description, unit=unit, **kwargs)
        # No setup needed

    def update(self, value: int, item_name: str | None = None) -> None:
        

        # Do nothing
        self.current_value = value  # Still update internal state for completeness

    def finish(self) -> None:


        

        """No-op finish method."""

    def close(self) -> None:


        

        """No-op close method."""


# Alias for easier default usage.
# Users can explicitly import TqdmProgressTracker or SilentProgressTracker if needed.
ProgressTracker = TqdmProgressTracker