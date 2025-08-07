import time
from typing import Any

from tqdm.auto import tqdm


class BaseProgressTracker:
    """Base class for progress tracking implementations."""

    def __init__(
        self,
        total: int | None = None,
        description: str | None = None,
        unit: str = "it",
        **kwargs: Any,
    ) -> None:
        self.total = total
        self.description = description
        self.unit = unit
        self.current_value = 0
        self.kwargs = kwargs  # Store unused kwargs for potential use by subclasses
        self.start_time = time.time()
        self.last_update_time = self.start_time

    def update(self, n: int = 1, description: str | None = None) -> None:
        """Update progress incrementally by n items."""
        self.current_value += n
        self.last_update_time = time.time()
        # Subclasses should override to provide visual feedback
    
    def set_progress(self, value: int, description: str | None = None) -> None:
        """Set progress to an absolute value."""
        # Default implementation: just track the value
        self.current_value = value
        self.last_update_time = time.time()
        # Subclasses should override to provide visual feedback

    def increment(self, amount: int = 1, item_name: str | None = None) -> None:
        """Increment progress by a certain amount."""
        self.update(amount, item_name)

    def finish(self) -> None:
        """Mark progress as finished."""
        # Default implementation: set progress to total if available
        if self.total is not None:
            self.current_value = self.total
        # Subclasses should override to provide visual feedback

    def set_total(self, total: int) -> None:
        """Set total number of items to process."""
        self.total = total
        
    def set_description(self, desc: str) -> None:
        """Set progress description."""
        self.description = desc

    def close(self) -> None:
        """Close any underlying resources (like tqdm progress bar)."""
        # Base implementation: reset state and clear any references
        self.current_value = 0
        self.total = None
        self.description = None
        # Clear any kwargs that might hold references
        self.kwargs.clear()
    
    # Backward compatibility methods for old interface
    def update_absolute(self, value: int, item_name: str | None = None) -> None:
        """Legacy method: Update progress to an absolute value.
        
        DEPRECATED: Use set_progress() instead.
        """
        self.set_progress(value, item_name)
    
    def update_legacy(self, value: int, item_name: str | None = None) -> None:
        """Legacy compatibility method for old update(value, item_name) signature.
        
        This method detects old-style usage and converts it to the new interface.
        DEPRECATED: Use update(n) or set_progress(value) instead.
        """
        # This is the old absolute update pattern
        self.set_progress(value, item_name)

    def get_elapsed_time(self) -> float:
        """Get elapsed time since tracker was created.

        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time

    def get_rate(self) -> float:
        """Get current processing rate.

        Returns:
            Items per second
        """
        elapsed = self.get_elapsed_time()
        if elapsed <= 0:
            return 0.0
        return self.current_value / elapsed

    def get_eta(self) -> float | None:
        """Calculate estimated time to completion.

        Returns:
            Estimated seconds remaining, or None if cannot be calculated
        """
        if self.total is None or self.current_value <= 0:
            return None

        elapsed = self.get_elapsed_time()
        if elapsed <= 0:
            return None

        rate = self.current_value / elapsed
        if rate <= 0:
            return None

        remaining_items = self.total - self.current_value
        return remaining_items / rate

    def get_eta_string(self) -> str:
        """Get formatted ETA string.

        Returns:
            Human-readable ETA string
        """
        eta = self.get_eta()
        if eta is None:
            return "N/A"

        if eta < 60:
            return f"{eta:.1f}s"
        if eta < 3600:
            minutes = int(eta // 60)
            seconds = int(eta % 60)
            return f"{minutes}m {seconds}s"
        hours = int(eta // 3600)
        minutes = int((eta % 3600) // 60)
        return f"{hours}h {minutes}m"

    def get_progress_percentage(self) -> float:
        """Get progress as percentage.

        Returns:
            Progress percentage (0-100)
        """
        if self.total is None or self.total <= 0:
            return 0.0
        return (self.current_value / self.total) * 100

    def __enter__(self) -> "BaseProgressTracker":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
        # Do not suppress exceptions


class TqdmProgressTracker(BaseProgressTracker):
    """Progress tracker using tqdm for visual output."""

    def __init__(
        self,
        total: int | None = None,
        description: str | None = None,
        unit: str = "it",
        show_item_name_on_update: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(total=total, description=description, unit=unit, **kwargs)
        self.show_item_name_on_update = show_item_name_on_update

        # Extract tqdm-specific kwargs
        unit_scale = kwargs.get("unit_scale", False)
        unit_divisor = kwargs.get("unit_divisor", 1000)

        self.pbar = tqdm(
            total=self.total,
            desc=self.description,
            unit=self.unit,
            unit_scale=unit_scale,
            unit_divisor=unit_divisor,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]",
            disable=self.kwargs.get("disable", False),  # Use stored kwargs
        )
        # self.start_time = time.time() # tqdm handles its own timing
        # self.items_processed = 0 # tqdm.n tracks this
        # self.bytes_processed = 0 # Not directly handled by this base tqdm wrapper

    def update(self, n: int = 1, description: str | None = None) -> None:
        """Update progress incrementally by n items."""
        if self.pbar:
            self.pbar.update(n)

            if self.show_item_name_on_update and description:
                self.pbar.set_postfix_str(f"Current: {description[:30]}", refresh=True)
            elif not self.show_item_name_on_update:  # Clear postfix if no item name:
                self.pbar.set_postfix_str("")
    
    def set_progress(self, value: int, description: str | None = None) -> None:
        """Set progress to an absolute value."""
        if self.pbar:
            increment = value - self.pbar.n
            self.pbar.update(increment)

            if self.show_item_name_on_update and description:
                self.pbar.set_postfix_str(f"Current: {description[:30]}", refresh=True)
            elif not self.show_item_name_on_update:  # Clear postfix if no description:
                self.pbar.set_postfix_str("")

    def increment(self, amount: int = 1, item_name: str | None = None) -> None:
        """Increment progress by a certain amount."""
        self.update(amount, item_name)
    
    def set_total(self, total: int) -> None:
        """Set total number of items to process."""
        self.total = total
        if self.pbar:
            self.pbar.total = total
            self.pbar.refresh()
    
    def set_description(self, desc: str) -> None:
        """Set progress description."""
        self.description = desc
        if self.pbar:
            self.pbar.set_description(desc, refresh=True)

    def finish(self) -> None:
        if self.pbar:
            if self.total is not None and self.pbar.n < self.total:
                self.pbar.update(self.total - self.pbar.n)
            self.pbar.set_postfix_str("Done.", refresh=True)
        # Closing is handled by self.close() or __exit__

    def close(self) -> None:
        if self.pbar:
            self.pbar.close()
            self.pbar = None


class SilentProgressTracker(BaseProgressTracker):
    """A progress tracker that does nothing, for silent/headless runs."""

    def __init__(
        self,
        total: int | None = None,
        description: str | None = None,
        unit: str = "it",
        **kwargs: Any,
    ) -> None:
        super().__init__(total=total, description=description, unit=unit, **kwargs)
        # No setup needed

    def update(self, n: int = 1, description: str | None = None) -> None:
        """Update progress incrementally by n items (no-op)."""
        self.current_value += n  # Still update internal state for completeness
        
    def set_progress(self, value: int, description: str | None = None) -> None:
        """Set progress to an absolute value (no-op)."""
        self.current_value = value  # Still update internal state for completeness
    
    def set_total(self, total: int) -> None:
        """Set total number of items to process (no-op)."""
        self.total = total
    
    def set_description(self, desc: str) -> None:
        """Set progress description (no-op)."""
        self.description = desc

    def finish(self) -> None:
        """No-op finish method."""
        # Call parent's finish to update internal state
        super().finish()

    def close(self) -> None:
        """No-op close method."""
        # Call parent's close to clean up state
        super().close()


# Alias for easier default usage.
# Users can explicitly import TqdmProgressTracker or SilentProgressTracker
# if needed.
ProgressTracker = TqdmProgressTracker
