"""Progress tracking utilities using Rich for beautiful terminal output."""

import time
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Protocol

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text


class ProgressCallback(Protocol):
    def __call__(self, current: int, total: int, message: str = "") -> None: ...


class TransferSpeedColumn(ProgressColumn):
    """Renders transfer speed for file operations."""

    def render(self, task: Task) -> Text:
        """Render the transfer speed."""
        speed = task.fields.get("speed", 0)
        if speed > 0:
            if speed > 1024 * 1024:
                return Text(f"{speed / 1024 / 1024:.1f} MB/s", style="bright_green")
            if speed > 1024:
                return Text(f"{speed / 1024:.1f} KB/s", style="green")
            return Text(f"{speed:.0f} B/s", style="yellow")
        return Text("", style="dim")


class PipelineProgress:
    """Progress tracker for the PowerBuilder pipeline."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the progress tracker.

        Args:
            console: Rich console instance (creates new if None)
        """
        self.console = console or Console()
        self.start_time = time.time()

        # Main pipeline progress
        self.pipeline_progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            expand=False,
        )

        # File extraction progress with transfer speed
        self.file_progress = Progress(
            TextColumn("[cyan]{task.description}"),
            BarColumn(bar_width=30),
            MofNCompleteColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=False,
        )

        # Individual file operations
        self.operation_progress = Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("{task.description}"),
            BarColumn(bar_width=20),
            TaskProgressColumn(),
            console=self.console,
            expand=False,
        )

        # Task IDs
        self.main_task_id: str | None = None
        self.file_task_id: str | None = None
        self.current_operation_id: str | None = None

    @contextmanager
    def pipeline_context(self, total_steps: int = 5) -> Generator["PipelineProgress"]:
        """Context manager for pipeline-wide progress tracking.

        Args:
            total_steps: Total number of pipeline steps

        Yields:
            PipelineProgress instance
        """
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        # Header
        header = Panel(
            "[bold blue]PowerBuilder Reverse Engineering Pipeline[/bold blue]",
            style="bold white on blue",
        )
        layout["header"].update(header)

        # Progress bars
        progress_table = Table.grid(expand=True)
        progress_table.add_column()
        progress_table.add_row(self.pipeline_progress)
        progress_table.add_row("")
        progress_table.add_row(self.file_progress)
        progress_table.add_row("")
        progress_table.add_row(self.operation_progress)

        layout["body"].update(
            Panel(progress_table, title="Progress", border_style="blue")
        )

        # Footer with stats
        layout["footer"].update(self._create_footer())

        self.main_task_id = self.pipeline_progress.add_task(
            "Pipeline Progress", total=total_steps
        )

        with Live(layout, console=self.console, refresh_per_second=10):
            try:
                yield self
            finally:
                # Final update
                layout["footer"].update(self._create_footer(final=True))
                self.console.print()

    def _create_footer(self, *, final: bool = False) -> Panel:
        """Create footer panel with statistics."""
        elapsed = time.time() - self.start_time
        elapsed_str = f"{elapsed:.1f}s"

        if elapsed > 60:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            elapsed_str = f"{minutes}m {seconds}s"

        status = "[green]✓ Complete[/green]" if final else "[yellow]⚡ Running[/yellow]"

        footer_text = f"{status} | Elapsed: {elapsed_str}"
        return Panel(footer_text, style="dim")

    def start_step(self, step_name: str, step_number: int) -> None:
        """Start a new pipeline step.

        Args:
            step_name: Name of the step
            step_number: Step number (1-based)
        """
        self.pipeline_progress.update(
            self.main_task_id,
            description=f"Step {step_number}: {step_name}",
            completed=step_number - 1,
        )

    def complete_step(self, step_number: int) -> None:
        """Mark a step as complete.

        Args:
            step_number: Step number (1-based)
        """
        self.pipeline_progress.update(self.main_task_id, completed=step_number)

    @contextmanager
    def file_extraction_context(self, total_files: int) -> Generator[str]:
        """Context manager for file extraction progress.

        Args:
            total_files: Total number of files to extract

        Yields:
            Task ID for updating progress
        """
        self.file_task_id = self.file_progress.add_task(
            "Extracting files", total=total_files, speed=0
        )
        try:
            yield self.file_task_id
        finally:
            self.file_progress.update(
                self.file_task_id, description="Extraction complete"
            )

    def update_file_progress(
        self, completed: int, current_file: str = "", speed: float = 0
    ) -> None:
        """Update file extraction progress.

        Args:
            completed: Number of files completed
            current_file: Name of current file being processed
            speed: Transfer speed in bytes/second
        """
        if self.file_task_id is not None:
            desc = (
                f"Extracting: {Path(current_file).name}"
                if current_file
                else "Extracting files"
            )
            self.file_progress.update(
                self.file_task_id,
                completed=completed,
                description=desc,
                speed=speed,
            )

    @contextmanager
    def operation_context(
        self, operation_name: str, total: int | None = None
    ) -> Generator[str]:
        """Context manager for individual operations.

        Args:
            operation_name: Name of the operation
            total: Total units of work (None for indeterminate)

        Yields:
            Task ID for updating progress
        """
        self.current_operation_id = self.operation_progress.add_task(
            operation_name, total=total
        )
        try:
            yield self.current_operation_id
        finally:
            if self.current_operation_id is not None:
                self.operation_progress.remove_task(self.current_operation_id)
                self.current_operation_id = None

    def update_operation(
        self, completed: int | None = None, description: str | None = None
    ) -> None:
        """Update current operation progress.

        Args:
            completed: Number of units completed
            description: New description
        """
        if self.current_operation_id is not None:
            update_kwargs: dict[str, Any] = {}
            if completed is not None:
                update_kwargs["completed"] = completed
            if description is not None:
                update_kwargs["description"] = description
            if update_kwargs:
                self.operation_progress.update(
                    self.current_operation_id, **update_kwargs
                )


class ProgressTracker:
    progress: Progress
    tasks: dict[str, Task]

    def __init__(self) -> None:
        self.progress = Progress()
        self.tasks = {}

    def start_task(self, task_id: str, description: str, total: int) -> None:
        task = self.progress.add_task(description, total=total)
        self.tasks[task_id] = task

    def update_task(
        self, task_id: str, advance: int = 1, message: str | None = None
    ) -> None:
        if task_id in self.tasks:
            kwargs: dict[str, Any] = {"advance": advance}
            if message is not None:
                kwargs["description"] = message
            self.progress.update(self.tasks[task_id], **kwargs)

    def complete_task(self, task_id: str) -> None:
        if task_id in self.tasks:
            self.progress.remove_task(self.tasks[task_id])
            del self.tasks[task_id]


def create_simple_progress() -> Progress:
    """Create a simple progress bar for basic operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeRemainingColumn(),
        console=Console(),
    )


@contextmanager
def track_progress(description: str, total: int | None = None) -> Iterator[Any]:
    """Simple progress tracking context manager.

    Args:
        description: Description of the task
        total: Total units of work (None for indeterminate)

    Yields:
        Progress task that can be updated
    """
    progress = create_simple_progress()
    with progress:
        task = progress.add_task(description, total=total)

        class ProgressTask:
            def advance(self, advance: int = 1, **kwargs: Any) -> None:
                progress.update(task, advance=advance, **kwargs)

            def set_description(self, description: str) -> None:
                progress.update(task, description=description)

        yield ProgressTask()


# Example usage for different scenarios
def example_usage() -> None:
    """Example of how to use the progress tracking."""
    import random
    import time

    # Full pipeline progress
    with PipelineProgress().pipeline_context(total_steps=5) as pipeline:
        # Step 1: Extraction
        pipeline.start_step("Extracting PowerBuilder files", 1)

        with pipeline.file_extraction_context(total_files=54) as _:
            for i in range(54):
                file_size = random.randint(100_000, 5_000_000)
                start_time = time.time()

                # Simulate file extraction
                time.sleep(0.1)

                speed = file_size / (time.time() - start_time)
                pipeline.update_file_progress(i + 1, f"file_{i}.pbd", speed)

        pipeline.complete_step(1)

        # Step 2: Decompilation
        pipeline.start_step("Decompiling P-code", 2)

        with pipeline.operation_context("Decompiling functions", total=500):
            for i in range(500):
                pipeline.update_operation(i + 1, f"Function {i + 1}/500")
                time.sleep(0.01)

        pipeline.complete_step(2)

        # Continue with other steps...
        for step in range(3, 6):
            step_names = {
                3: "Parsing source code",
                4: "Building models",
                5: "Generating output",
            }
            pipeline.start_step(step_names[step], step)
            time.sleep(2)  # Simulate work
            pipeline.complete_step(step)


if __name__ == "__main__":
    example_usage()
