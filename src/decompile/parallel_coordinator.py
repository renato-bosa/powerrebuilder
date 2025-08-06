"""Parallel PowerBuilder decompilation coordinator with enhanced progress reporting.

This module provides parallel file processing capabilities for PowerBuilder decompilation,
using ProcessPoolExecutor for CPU-bound tasks and rich progress bars for visualization.
"""

import logging
import os
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
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
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from src.contracts.interfaces import IDecompilerCoordinator
from src.decompile.adaptive_parallelism import optimize_for_files
from src.decompile.coordinator import ExtractedFileDecompiler
from src.extract.pbd.type_detection import ObjectTypeDetector

logger = logging.getLogger(__name__)


class ParallelDecompileCoordinator(IDecompilerCoordinator):
    """Enhanced decompile coordinator with parallel processing and rich progress reporting."""

    def __init__(
        self,
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        max_workers: int | None = None,
        use_processes: bool = True,
        chunk_size: int = 1,
        enable_memory_mapping: bool = True,
        progress_refresh_rate: float = 0.1,
        use_adaptive_parallelism: bool = True,
    ) -> None:
        """Initialize the parallel coordinator.

        Args:
            input_dir: Directory containing P-code files
            output_dir: Directory to write decompiled files
            max_workers: Maximum parallel workers (defaults to adaptive optimization)
            use_processes: Use ProcessPoolExecutor instead of ThreadPoolExecutor
            chunk_size: Chunk size for batch processing
            enable_memory_mapping: Enable memory mapping for large files
            progress_refresh_rate: Progress bar refresh rate in seconds
            use_adaptive_parallelism: Use adaptive parallelism engine for optimization
        """
        self.input_dir = Path(input_dir) if input_dir else None
        self.output_dir = Path(output_dir) if output_dir else None
        self.use_adaptive_parallelism = use_adaptive_parallelism
        self.progress_refresh_rate = progress_refresh_rate

        # These will be set by adaptive optimization or defaults
        self.use_processes = use_processes
        self.chunk_size = chunk_size
        self.enable_memory_mapping = enable_memory_mapping

        # Determine optimal worker count (will be refined by adaptive engine)
        cpu_count = os.cpu_count() or 4
        if use_processes:
            self.max_workers = max_workers or cpu_count
        else:
            self.max_workers = max_workers or min(cpu_count * 2, 16)

        self.console = Console()

        # Performance tracking
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "skipped_files": 0,
            "total_bytes": 0,
            "processed_bytes": 0,
            "start_time": None,
            "end_time": None,
        }

        # Adaptive configuration (will be set during decompile)
        self.adaptive_config = None

        logger.info(
            "ParallelDecompileCoordinator initialized: adaptive=%s, initial_workers=%d, processes=%s",
            use_adaptive_parallelism,
            self.max_workers,
            use_processes,
        )

    def decompile(
        self,
        input_dir: Path | None = None,
        output_dir: Path | None = None,
        progress_callback: Callable | None = None,
    ) -> dict[str, Any]:
        """Coordinate parallel decompilation process with rich progress reporting.

        Args:
            input_dir: Optional override for input directory
            output_dir: Optional override for output directory
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with decompilation results and performance metrics
        """
        # Use provided directories or fall back to instance ones
        in_dir = Path(input_dir) if input_dir else self.input_dir
        out_dir = Path(output_dir) if output_dir else self.output_dir

        if not in_dir:
            raise ValueError("No input directory specified")
        if not out_dir:
            raise ValueError("No output directory specified")

        # Ensure output directory exists
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Starting parallel decompilation process")
        logger.info("Input directory: %s", in_dir)
        logger.info("Output directory: %s", out_dir)
        logger.info(
            "Max workers: %d (%s)",
            self.max_workers,
            "processes" if self.use_processes else "threads",
        )

        # Initialize stats
        self.stats["start_time"] = time.time()

        try:
            # Collect all files to process
            pcode_files = self._collect_pcode_files(in_dir)
            self.stats["total_files"] = len(pcode_files)
            self.stats["total_bytes"] = sum(f.stat().st_size for f in pcode_files)

            logger.info(
                "Found %d P-code files (%d MB total)",
                len(pcode_files),
                self.stats["total_bytes"] // 1024 // 1024,
            )

            if not pcode_files:
                return self._create_result_dict("completed", "No P-code files found")

            # Use adaptive parallelism to optimize configuration
            if self.use_adaptive_parallelism:
                self.adaptive_config = optimize_for_files(pcode_files)

                # Apply adaptive configuration
                self.use_processes = self.adaptive_config.use_processes
                self.max_workers = self.adaptive_config.max_workers
                self.chunk_size = self.adaptive_config.chunk_size
                self.enable_memory_mapping = self.adaptive_config.use_memory_mapping

                logger.info("Adaptive parallelism configuration:")
                logger.info("  Use processes: %s", self.use_processes)
                logger.info("  Max workers: %d", self.max_workers)
                logger.info("  Memory mapping: %s", self.enable_memory_mapping)
                logger.info(
                    "  Reasoning: %s", "; ".join(self.adaptive_config.reasoning)
                )

                # Show summary
                from src.decompile.adaptive_parallelism import get_adaptive_engine

                engine = get_adaptive_engine()
                summary = engine.get_recommended_config_summary(self.adaptive_config)
                logger.info("Configuration summary: %s", summary)

            # Group files by size for better load balancing
            file_groups = self._group_files_by_size(pcode_files)

            # Process files in parallel with rich progress reporting
            if self.use_processes:
                results = self._process_files_with_processes(file_groups, out_dir)
            else:
                results = self._process_files_with_threads(file_groups, out_dir)

            # Calculate final statistics
            self.stats["end_time"] = time.time()
            duration = self.stats["end_time"] - self.stats["start_time"]

            success_rate = (
                (self.stats["processed_files"] / self.stats["total_files"] * 100)
                if self.stats["total_files"] > 0
                else 0
            )

            throughput = (
                self.stats["processed_bytes"] / duration / 1024 / 1024
                if duration > 0
                else 0
            )

            result = self._create_result_dict("completed")
            result.update(
                {
                    "performance": {
                        "duration_seconds": duration,
                        "success_rate": f"{success_rate:.1f}%",
                        "throughput_mb_per_sec": f"{throughput:.2f}",
                        "files_per_second": f"{self.stats['processed_files'] / duration:.2f}"
                        if duration > 0
                        else "0",
                        "average_file_size_kb": f"{self.stats['total_bytes'] / self.stats['total_files'] / 1024:.1f}"
                        if self.stats["total_files"] > 0
                        else "0",
                    },
                    "system_info": self._get_system_info(),
                }
            )

            # Record performance for adaptive learning
            if self.use_adaptive_parallelism and self.adaptive_config:
                from src.decompile.adaptive_parallelism import get_adaptive_engine

                engine = get_adaptive_engine()
                engine.record_performance(
                    self.adaptive_config,
                    {
                        "duration": duration,
                        "success_rate": success_rate,
                        "throughput_mbps": throughput,
                        "files_processed": self.stats["processed_files"],
                        "files_total": self.stats["total_files"],
                    },
                )

            logger.info("Parallel decompilation complete:")
            logger.info("  Total files: %d", self.stats["total_files"])
            logger.info("  Processed: %d", self.stats["processed_files"])
            logger.info("  Failed: %d", self.stats["failed_files"])
            logger.info("  Skipped: %d", self.stats["skipped_files"])
            logger.info("  Success rate: %.1f%%", success_rate)
            logger.info("  Duration: %.2f seconds", duration)
            logger.info("  Throughput: %.2f MB/s", throughput)

            return result

        except Exception as e:
            logger.exception("Parallel decompilation failed: %s", e)
            self.stats["end_time"] = time.time()
            result = self._create_result_dict("failed", str(e))
            result["performance"] = {
                "duration_seconds": self.stats["end_time"] - self.stats["start_time"]
            }
            return result

    def _collect_pcode_files(self, input_dir: Path) -> list[Path]:
        """Collect all P-code files to process.

        Args:
            input_dir: Directory to search for P-code files

        Returns:
            List of P-code file paths
        """
        pcode_extensions = [".fun", ".men", ".mef", ".apf", ".udo", ".win"]
        all_files = []

        if input_dir.is_file():
            # Single file mode
            if any(input_dir.suffix.lower() == ext for ext in pcode_extensions):
                all_files.append(input_dir)
        else:
            # Directory mode - collect files recursively
            for ext in pcode_extensions:
                all_files.extend(input_dir.rglob(f"*{ext}"))

        # Filter files that should be decompiled
        filtered_files = [
            f for f in all_files if ObjectTypeDetector.should_decompile(str(f.name))
        ]

        logger.info(
            "Collected %d P-code files (filtered from %d total)",
            len(filtered_files),
            len(all_files),
        )

        return filtered_files

    def _group_files_by_size(self, files: list[Path]) -> list[list[Path]]:
        """Group files by size for optimal load balancing.

        Args:
            files: List of file paths

        Returns:
            List of file groups, sorted by total size (largest first)
        """
        # Sort files by size (largest first)
        files_with_size = [(f, f.stat().st_size) for f in files]
        files_with_size.sort(key=lambda x: x[1], reverse=True)

        # Create groups for load balancing
        groups = []
        current_group = []
        current_group_size = 0
        max_group_size = max(1, len(files) // self.max_workers)

        for file_path, file_size in files_with_size:
            current_group.append(file_path)
            current_group_size += file_size

            if len(current_group) >= max_group_size:
                groups.append(current_group)
                current_group = []
                current_group_size = 0

        # Add remaining files
        if current_group:
            groups.append(current_group)

        logger.info(
            "Created %d file groups (avg %.1f files per group)",
            len(groups),
            len(files) / len(groups) if groups else 0,
        )

        return groups

    def _process_files_with_processes(
        self, file_groups: list[list[Path]], output_dir: Path
    ) -> dict[str, Any]:
        """Process files using ProcessPoolExecutor.

        Args:
            file_groups: Groups of files to process
            output_dir: Output directory

        Returns:
            Processing results
        """
        logger.info("Using ProcessPoolExecutor with %d workers", self.max_workers)

        # Create progress display
        live, progress = self._create_progress_display()
        with live:
            # Create tasks for each group
            group_tasks = []
            for i, group in enumerate(file_groups):
                task_id = progress.add_task(
                    f"[cyan]Group {i + 1}",
                    total=len(group),
                )
                group_tasks.append(task_id)

            overall_task = progress.add_task(
                "[bold green]Overall Progress",
                total=len(file_groups),
            )

            # Process groups in parallel
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all groups
                future_to_group = {
                    executor.submit(
                        _process_file_group_worker,
                        group,
                        str(output_dir),
                        self.enable_memory_mapping,
                    ): (i, group)
                    for i, group in enumerate(file_groups)
                }

                # Collect results
                for future in as_completed(future_to_group):
                    group_idx, group = future_to_group[future]
                    task_id = group_tasks[group_idx]

                    try:
                        group_result = future.result()
                        self.stats["processed_files"] += group_result["processed"]
                        self.stats["failed_files"] += group_result["failed"]
                        self.stats["skipped_files"] += group_result["skipped"]
                        self.stats["processed_bytes"] += group_result["processed_bytes"]

                        progress.update(
                            task_id,
                            completed=len(group),
                            description=f"[green]Group {group_idx + 1} ✓",
                        )
                        progress.update(overall_task, advance=1)

                    except Exception as e:
                        logger.error("Group %d failed: %s", group_idx + 1, e)
                        self.stats["failed_files"] += len(group)
                        progress.update(
                            task_id,
                            completed=len(group),
                            description=f"[red]Group {group_idx + 1} ✗",
                        )
                        progress.update(overall_task, advance=1)

        return {"status": "completed"}

    def _process_files_with_threads(
        self, file_groups: list[list[Path]], output_dir: Path
    ) -> dict[str, Any]:
        """Process files using ThreadPoolExecutor.

        Args:
            file_groups: Groups of files to process
            output_dir: Output directory

        Returns:
            Processing results
        """
        logger.info("Using ThreadPoolExecutor with %d workers", self.max_workers)

        # Flatten groups for thread processing (threads are lighter weight)
        all_files = [f for group in file_groups for f in group]

        # Create progress display
        live, progress = self._create_progress_display()
        with live:
            main_task = progress.add_task(
                "[bold green]Decompiling files",
                total=len(all_files),
            )

            # Process files with threads
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Create decompiler instances (one per worker to avoid contention)
                decompilers = [
                    ExtractedFileDecompiler(
                        output_dir=output_dir,
                        enable_filtering=True,
                        output_format="pb",
                    )
                    for _ in range(self.max_workers)
                ]

                # Submit all files
                future_to_file = {
                    executor.submit(
                        _process_single_file_worker,
                        file_path,
                        decompilers[i % len(decompilers)],
                    ): file_path
                    for i, file_path in enumerate(all_files)
                }

                # Collect results
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]

                    try:
                        result = future.result()
                        if result["success"]:
                            self.stats["processed_files"] += 1
                            self.stats["processed_bytes"] += result["file_size"]
                        else:
                            self.stats["failed_files"] += 1

                        progress.update(
                            main_task,
                            advance=1,
                            description=f"[bold green]Processed {file_path.name}",
                        )

                    except Exception as e:
                        logger.error("File %s failed: %s", file_path, e)
                        self.stats["failed_files"] += 1
                        progress.update(main_task, advance=1)

        return {"status": "completed"}

    def _create_progress_display(self) -> tuple[Live, Progress]:
        """Create a rich progress display with system monitoring.

        Returns:
            Tuple of (Live display object, Progress object)
        """
        # Create progress bar
        progress = Progress(
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
            refresh_per_second=1 / self.progress_refresh_rate,
        )

        # Create system info table
        system_table = Table.grid(padding=1)
        system_table.add_column("Metric", style="cyan")
        system_table.add_column("Value", style="white")

        # Combine into layout
        layout = Table.grid()
        layout.add_row(progress)
        layout.add_row(Panel(system_table, title="System Info", border_style="dim"))

        return Live(layout, refresh_per_second=1 / self.progress_refresh_rate), progress

    def _get_system_info(self) -> dict[str, Any]:
        """Get current system information.

        Returns:
            Dictionary with system metrics
        """
        try:
            return {
                "cpu_count": os.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage("/").percent,
                "max_workers": self.max_workers,
                "use_processes": self.use_processes,
            }
        except Exception as e:
            logger.warning("Could not get system info: %s", e)
            return {"error": str(e)}

    def _create_result_dict(
        self, status: str, error: str | None = None
    ) -> dict[str, Any]:
        """Create a standardized result dictionary.

        Args:
            status: Result status
            error: Optional error message

        Returns:
            Result dictionary
        """
        result = {
            "status": status,
            "input_dir": str(self.input_dir) if self.input_dir else None,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "total_files": self.stats["total_files"],
            "processed_files": self.stats["processed_files"],
            "failed_files": self.stats["failed_files"],
            "skipped_files": self.stats["skipped_files"],
            "total_bytes": self.stats["total_bytes"],
            "processed_bytes": self.stats["processed_bytes"],
        }

        if error:
            result["error"] = error

        return result

    # Interface methods for compatibility
    def decompile_file(self, file_path: Path) -> str:
        """Decompile a single file."""
        # Create a temporary decompiler for single file processing
        decompiler = ExtractedFileDecompiler(
            output_dir=None,
            enable_filtering=True,
            output_format="pb",
        )

        if decompiler.decompile_extracted_file(file_path):
            return f"Successfully decompiled {file_path}"
        raise RuntimeError(f"Failed to decompile {file_path}")

    def register_decompiler(self, decompiler: Any) -> None:
        """Register a new decompiler (for interface compatibility)."""
        logger.warning("register_decompiler is not implemented in parallel coordinator")

    def get_decompilers(self) -> list[Any]:
        """Get all registered decompilers (for interface compatibility)."""
        return []


# Worker functions for multiprocessing
def _process_file_group_worker(
    file_group: list[Path],
    output_dir: str,
    enable_memory_mapping: bool,
) -> dict[str, Any]:
    """Worker function to process a group of files.

    Args:
        file_group: Group of files to process
        output_dir: Output directory path
        enable_memory_mapping: Whether to use memory mapping

    Returns:
        Processing results for the group
    """
    # Create decompiler instance for this worker
    decompiler = ExtractedFileDecompiler(
        output_dir=Path(output_dir),
        enable_filtering=True,
        output_format="pb",
    )

    results = {
        "processed": 0,
        "failed": 0,
        "skipped": 0,
        "processed_bytes": 0,
    }

    for file_path in file_group:
        try:
            if decompiler.decompile_extracted_file(file_path):
                results["processed"] += 1
                results["processed_bytes"] += file_path.stat().st_size
            else:
                results["failed"] += 1
        except Exception as e:
            logger.error("Failed to process %s: %s", file_path, e)
            results["failed"] += 1

    return results


def _process_single_file_worker(
    file_path: Path,
    decompiler: ExtractedFileDecompiler,
) -> dict[str, Any]:
    """Worker function to process a single file.

    Args:
        file_path: File to process
        decompiler: Decompiler instance

    Returns:
        Processing result for the file
    """
    try:
        success = decompiler.decompile_extracted_file(file_path)
        return {
            "success": success,
            "file_size": file_path.stat().st_size,
        }
    except Exception as e:
        logger.error("Failed to process %s: %s", file_path, e)
        return {
            "success": False,
            "file_size": file_path.stat().st_size,
            "error": str(e),
        }
