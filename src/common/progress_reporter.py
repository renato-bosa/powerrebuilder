"""Enhanced progress reporting with rich console output and performance monitoring.

This module provides comprehensive progress reporting capabilities with:
- Rich progress bars with multiple metrics
- Real-time system monitoring
- Hierarchical progress tracking
- Performance analytics
- ETA and throughput calculations
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import psutil
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

logger = logging.getLogger(__name__)


@dataclass
class ProgressMetrics:
    """Container for progress metrics and performance data."""

    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    items_processed: int = 0
    items_total: int = 0
    bytes_processed: int = 0
    bytes_total: int = 0
    errors_count: int = 0
    warnings_count: int = 0

    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def items_per_second(self) -> float:
        """Get processing rate in items per second."""
        duration = self.duration
        return self.items_processed / duration if duration > 0 else 0

    @property
    def bytes_per_second(self) -> float:
        """Get processing rate in bytes per second."""
        duration = self.duration
        return self.bytes_processed / duration if duration > 0 else 0

    @property
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        return (
            (self.items_processed / self.items_total * 100)
            if self.items_total > 0
            else 0
        )

    @property
    def estimated_time_remaining(self) -> float:
        """Get estimated time remaining in seconds."""
        if self.items_processed == 0 or self.items_total == 0:
            return 0

        rate = self.items_per_second
        remaining_items = self.items_total - self.items_processed
        return remaining_items / rate if rate > 0 else 0


@dataclass
class SystemMetrics:
    """Container for system performance metrics."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_io_read_bytes: int = 0
    disk_io_write_bytes: int = 0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    process_count: int = 0
    thread_count: int = 0

    @classmethod
    def capture(cls) -> "SystemMetrics":
        """Capture current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()

            return cls(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_io_read_bytes=disk_io.read_bytes if disk_io else 0,
                disk_io_write_bytes=disk_io.write_bytes if disk_io else 0,
                network_bytes_sent=network_io.bytes_sent if network_io else 0,
                network_bytes_recv=network_io.bytes_recv if network_io else 0,
                process_count=len(psutil.pids()),
                thread_count=psutil.Process().num_threads(),
            )
        except Exception as e:
            logger.warning("Failed to capture system metrics: %s", e)
            return cls()


class EnhancedProgressReporter:
    """Enhanced progress reporter with rich console output and system monitoring."""

    def __init__(
        self,
        console: Console | None = None,
        refresh_rate: float = 0.1,
        show_system_metrics: bool = True,
        track_performance: bool = True,
    ) -> None:
        """Initialize the progress reporter.

        Args:
            console: Rich console instance (creates new if None)
            refresh_rate: Progress bar refresh rate in seconds
            show_system_metrics: Whether to show system performance metrics
            track_performance: Whether to track detailed performance metrics
        """
        self.console = console or Console()
        self.refresh_rate = refresh_rate
        self.show_system_metrics = show_system_metrics
        self.track_performance = track_performance

        # Progress tracking
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            TextColumn("•"),
            TransferSpeedColumn(),
            refresh_per_second=1 / refresh_rate,
            console=self.console,
        )

        # Metrics tracking
        self.metrics = ProgressMetrics()
        self.system_metrics = SystemMetrics()
        self.task_metrics: dict[TaskID, ProgressMetrics] = {}

        # Layout components
        self._live: Live | None = None
        self._main_task: TaskID | None = None

    def start(self, description: str = "Processing", total: int = 100) -> TaskID:
        """Start progress reporting.

        Args:
            description: Task description
            total: Total number of items to process

        Returns:
            Task ID for updates
        """
        self.metrics.items_total = total
        self.metrics.start_time = time.time()

        # Create main task
        self._main_task = self.progress.add_task(
            f"[bold green]{description}",
            total=total,
        )

        # Start live display
        layout = self._create_layout()
        self._live = Live(layout, refresh_per_second=1 / self.refresh_rate)
        self._live.start()

        logger.info("Started progress reporting: %s (total: %d)", description, total)
        return self._main_task

    def stop(self) -> ProgressMetrics:
        """Stop progress reporting and return final metrics.

        Returns:
            Final progress metrics
        """
        self.metrics.end_time = time.time()

        if self._live:
            self._live.stop()
            self._live = None

        logger.info(
            "Progress reporting completed: %d/%d items (%.1f%%) in %.2f seconds",
            self.metrics.items_processed,
            self.metrics.items_total,
            self.metrics.completion_percentage,
            self.metrics.duration,
        )

        return self.metrics

    def update(
        self,
        task_id: TaskID | None = None,
        advance: int = 1,
        description: str | None = None,
        bytes_processed: int = 0,
        error: bool = False,
        warning: bool = False,
    ) -> None:
        """Update progress.

        Args:
            task_id: Task ID to update (uses main task if None)
            advance: Number of items to advance
            description: Optional new description
            bytes_processed: Number of bytes processed
            error: Whether this update represents an error
            warning: Whether this update represents a warning
        """
        task_id = task_id or self._main_task
        if not task_id:
            return

        # Update metrics
        self.metrics.items_processed += advance
        self.metrics.bytes_processed += bytes_processed

        if error:
            self.metrics.errors_count += 1
        if warning:
            self.metrics.warnings_count += 1

        # Update progress bar
        update_kwargs = {"advance": advance}
        if description:
            update_kwargs["description"] = f"[bold green]{description}"

        self.progress.update(task_id, **update_kwargs)

        # Update system metrics if enabled
        if self.show_system_metrics:
            self.system_metrics = SystemMetrics.capture()

    def add_subtask(self, description: str, total: int) -> TaskID:
        """Add a subtask.

        Args:
            description: Subtask description
            total: Total items for subtask

        Returns:
            Task ID for the subtask
        """
        task_id = self.progress.add_task(
            f"[cyan]{description}",
            total=total,
        )

        # Track metrics for this subtask
        self.task_metrics[task_id] = ProgressMetrics(
            items_total=total,
            start_time=time.time(),
        )

        return task_id

    def complete_subtask(self, task_id: TaskID) -> ProgressMetrics:
        """Complete a subtask and return its metrics.

        Args:
            task_id: Task ID to complete

        Returns:
            Final metrics for the subtask
        """
        if task_id in self.task_metrics:
            task_metrics = self.task_metrics[task_id]
            task_metrics.end_time = time.time()

            # Update progress to 100%
            self.progress.update(
                task_id,
                completed=task_metrics.items_total,
                description="[green]✓ Completed",
            )

            return task_metrics

        return ProgressMetrics()

    @contextmanager
    def subtask(self, description: str, total: int):
        """Context manager for subtasks.

        Args:
            description: Subtask description
            total: Total items for subtask

        Yields:
            Task ID for the subtask
        """
        task_id = self.add_subtask(description, total)
        try:
            yield task_id
        finally:
            self.complete_subtask(task_id)

    def _create_layout(self) -> Table:
        """Create the layout for the progress display.

        Returns:
            Rich table layout
        """
        layout = Table.grid()

        # Add progress bars
        layout.add_row(self.progress)

        # Add system metrics if enabled
        if self.show_system_metrics:
            system_panel = self._create_system_panel()
            layout.add_row(system_panel)

        # Add performance metrics if enabled
        if self.track_performance:
            perf_panel = self._create_performance_panel()
            layout.add_row(perf_panel)

        return layout

    def _create_system_panel(self) -> Panel:
        """Create system metrics panel.

        Returns:
            Rich panel with system metrics
        """
        table = Table.grid(padding=(0, 2))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("CPU Usage", f"{self.system_metrics.cpu_percent:.1f}%")
        table.add_row("Memory Usage", f"{self.system_metrics.memory_percent:.1f}%")
        table.add_row("Processes", str(self.system_metrics.process_count))
        table.add_row("Threads", str(self.system_metrics.thread_count))

        return Panel(table, title="System Metrics", border_style="dim")

    def _create_performance_panel(self) -> Panel:
        """Create performance metrics panel.

        Returns:
            Rich panel with performance metrics
        """
        table = Table.grid(padding=(0, 2))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        # Format throughput
        throughput_items = f"{self.metrics.items_per_second:.2f} items/sec"
        throughput_bytes = f"{self.metrics.bytes_per_second / 1024 / 1024:.2f} MB/sec"

        # Format ETA
        eta_seconds = self.metrics.estimated_time_remaining
        eta_formatted = (
            f"{eta_seconds // 60:.0f}m {eta_seconds % 60:.0f}s"
            if eta_seconds > 60
            else f"{eta_seconds:.1f}s"
        )

        table.add_row("Items/sec", throughput_items)
        table.add_row("Throughput", throughput_bytes)
        table.add_row("ETA", eta_formatted)
        table.add_row("Errors", str(self.metrics.errors_count))
        table.add_row("Warnings", str(self.metrics.warnings_count))

        return Panel(table, title="Performance", border_style="dim")

    def get_summary(self) -> dict[str, Any]:
        """Get comprehensive summary of progress and performance.

        Returns:
            Dictionary with summary information
        """
        return {
            "progress": {
                "items_processed": self.metrics.items_processed,
                "items_total": self.metrics.items_total,
                "completion_percentage": self.metrics.completion_percentage,
                "bytes_processed": self.metrics.bytes_processed,
                "bytes_total": self.metrics.bytes_total,
            },
            "performance": {
                "duration_seconds": self.metrics.duration,
                "items_per_second": self.metrics.items_per_second,
                "bytes_per_second": self.metrics.bytes_per_second,
                "estimated_time_remaining": self.metrics.estimated_time_remaining,
            },
            "quality": {
                "errors_count": self.metrics.errors_count,
                "warnings_count": self.metrics.warnings_count,
                "success_rate": (
                    self.metrics.items_processed - self.metrics.errors_count
                )
                / self.metrics.items_processed
                * 100
                if self.metrics.items_processed > 0
                else 0,
            },
            "system": {
                "cpu_percent": self.system_metrics.cpu_percent,
                "memory_percent": self.system_metrics.memory_percent,
                "process_count": self.system_metrics.process_count,
                "thread_count": self.system_metrics.thread_count,
            },
        }


# Convenience functions for common use cases
def create_progress_reporter(
    description: str = "Processing", total: int = 100, **kwargs
) -> EnhancedProgressReporter:
    """Create and start a progress reporter.

    Args:
        description: Task description
        total: Total items to process
        **kwargs: Additional arguments for EnhancedProgressReporter

    Returns:
        Started progress reporter
    """
    reporter = EnhancedProgressReporter(**kwargs)
    reporter.start(description, total)
    return reporter


@contextmanager
def progress_context(description: str = "Processing", total: int = 100, **kwargs):
    """Context manager for progress reporting.

    Args:
        description: Task description
        total: Total items to process
        **kwargs: Additional arguments for EnhancedProgressReporter

    Yields:
        Progress reporter instance
    """
    reporter = EnhancedProgressReporter(**kwargs)
    reporter.start(description, total)
    try:
        yield reporter
    finally:
        reporter.stop()
