"""I/O operations for PowerBuilder extraction.

This module consolidates functionality from:
- io.py: Resource utility functions for image processing
- progress.py: Progress tracking implementations
"""

import struct
import time
from typing import Any

from tqdm.auto import tqdm


# ============================================================================
# Resource Utilities (from io.py)
# ============================================================================


def get_bmp_size(data: bytes) -> tuple[int, int] | None:
    """Extract dimensions from BMP data.

    Args:
        data: BMP file data

    Returns:
        Tuple of (width, height) or None if invalid
    """
    if len(data) < 26:
        return None

    # Check BMP signature
    if data[:2] != b"BM":
        return None

    try:
        # BMP header structure:
        # Offset 18: width (4 bytes, little-endian)
        # Offset 22: height (4 bytes, little-endian)
        width = struct.unpack("<I", data[18:22])[0]
        height = struct.unpack("<I", data[22:26])[0]

        # Validate dimensions
        if width > 0 and height > 0 and width < 10000 and height < 10000:
            return (width, height)
    except struct.error:
        pass

    return None


def get_ico_size(data: bytes) -> tuple[int, int] | None:
    """Extract dimensions from ICO data.

    Args:
        data: ICO file data

    Returns:
        Tuple of (width, height) or None if invalid
    """
    if len(data) < 22:
        return None

    try:
        # ICO header structure:
        # Offset 0-2: Reserved (always 0)
        # Offset 2-4: Type (1 for icon)
        # Offset 4-6: Number of images
        if struct.unpack("<HH", data[0:4]) != (0, 1):
            return None

        # Get first image dimensions
        # Icon directory entry starts at offset 6
        # Offset 6: Width (0 means 256)
        # Offset 7: Height (0 means 256)
        width = data[6]
        height = data[7]

        # 0 means 256 in ICO format
        if width == 0:
            width = 256
        if height == 0:
            height = 256

        return (width, height)
    except (struct.error, IndexError):
        pass

    return None


def get_image_format(data: bytes) -> str | None:
    """Detect image format from data.

    Args:
        data: Image file data

    Returns:
        Format string ('BMP', 'ICO', 'PNG', 'JPEG') or None
    """
    if len(data) < 4:
        return None

    # Check common image signatures
    if data[:2] == b"BM":
        return "BMP"
    if data[:4] == b"\x00\x00\x01\x00":
        return "ICO"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if data[:3] == b"\xff\xd8\xff":
        return "JPEG"
    if data[:4] == b"GIF8":
        return "GIF"

    return None


def estimate_resource_size(data: bytes, resource_type: str) -> dict[str, Any]:
    """Estimate resource size and metadata.

    Args:
        data: Resource data
        resource_type: Type of resource

    Returns:
        Dictionary with size information
    """
    info = {"size": len(data), "type": resource_type}

    if resource_type == "image":
        format_type = get_image_format(data)
        if format_type:
            info["format"] = format_type

            if format_type == "BMP":
                dimensions = get_bmp_size(data)
                if dimensions:
                    info["width"], info["height"] = dimensions
            elif format_type == "ICO":
                dimensions = get_ico_size(data)
                if dimensions:
                    info["width"], info["height"] = dimensions

    return info


# ============================================================================
# Progress Tracking (from progress.py)
# ============================================================================


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

    def update(self, value: int, _item_name: str | None = None) -> None:
        """Update the progress. 'value' is the new absolute progress value."""
        # Default implementation: just track the value
        self.current_value = value
        self.last_update_time = time.time()
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
        # Base implementation: reset state and clear any references
        self.current_value = 0
        self.total = None
        self.description = None
        # Clear any kwargs that might hold references
        self.kwargs.clear()

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

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.close()
        return False  # Do not suppress exceptions


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

    def update(self, value: int, item_name: str | None = None) -> None:
        """Update the progress bar to a new absolute value.
        The "value" parameter here represents the new count of items processed.
        """
        if self.pbar:
            increment = value - self.pbar.n
            self.pbar.update(increment)

            if self.show_item_name_on_update and item_name:
                self.pbar.set_postfix_str(f"Current: {item_name[:30]}", refresh=True)
            elif not self.show_item_name_on_update:  # Clear postfix if no item name:
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
        # self.current_value = self.pbar.n # Sync if needed, but
        # BaseProgressTracker.current_value is not used by TqdmProgressTracker

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

    def update(self, value: int, _item_name: str | None = None) -> None:
        # Do nothing
        self.current_value = value  # Still update internal state for completeness

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