"""Benchmark framework for parallel decompilation performance validation.

This module provides comprehensive benchmarking tools to validate the performance
improvements of the enhanced parallel processing system, targeting 8-16x speedup
on multi-core systems.
"""

import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.decompile.coordinator import DecompileCoordinator
from src.decompile.enhanced_parallel_coordinator import (
    EnhancedParallelDecompileCoordinator,
)
from src.decompile.parallel_config import get_config

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetrics:
    """Comprehensive metrics for a benchmark run."""

    # Basic metrics
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    duration_seconds: float = 0.0

    # Performance metrics
    files_per_second: float = 0.0
    mb_per_second: float = 0.0
    cpu_utilization_percent: float = 0.0
    memory_peak_mb: float = 0.0
    memory_average_mb: float = 0.0

    # Detailed timing
    startup_time: float = 0.0
    processing_time: float = 0.0
    shutdown_time: float = 0.0

    # File size distribution
    total_bytes: int = 0
    average_file_size_mb: float = 0.0
    largest_file_mb: float = 0.0
    smallest_file_mb: float = 0.0

    # Error analysis
    timeout_failures: int = 0
    memory_failures: int = 0
    other_failures: int = 0
    failure_rate_percent: float = 0.0

    # System info
    worker_count: int = 0
    cpu_count: int = 0
    system_memory_gb: float = 0.0

    # Advanced metrics
    cache_hit_rate_percent: float = 0.0
    throttle_events: int = 0
    work_steal_events: int = 0
    checkpoint_saves: int = 0

    def calculate_derived_metrics(self) -> None:
        """Calculate derived metrics from basic measurements."""
        if self.duration_seconds > 0:
            self.files_per_second = self.processed_files / self.duration_seconds
            if self.total_bytes > 0:
                self.mb_per_second = (
                    self.total_bytes / 1024 / 1024
                ) / self.duration_seconds

        if self.total_files > 0:
            self.failure_rate_percent = (self.failed_files / self.total_files) * 100

        if self.total_bytes > 0 and self.total_files > 0:
            self.average_file_size_mb = (self.total_bytes / self.total_files) / (
                1024 * 1024
            )


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""

    # Test data
    input_directory: Path = Path("test_data")
    output_directory: Path = Path("benchmark_output")

    # Test parameters
    warmup_runs: int = 1
    measurement_runs: int = 3
    max_files_per_run: int | None = None

    # System monitoring
    monitor_system_resources: bool = True
    resource_sampling_interval: float = 1.0

    # Comparison tests
    test_sequential: bool = True
    test_parallel_basic: bool = True
    test_parallel_enhanced: bool = True

    # Output options
    save_detailed_results: bool = True
    generate_charts: bool = False
    output_format: str = "json"  # json, csv, html


@dataclass
class ComparisonResult:
    """Results from comparing different processing approaches."""

    sequential_metrics: BenchmarkMetrics | None = None
    parallel_basic_metrics: BenchmarkMetrics | None = None
    parallel_enhanced_metrics: BenchmarkMetrics | None = None

    speedup_basic: float = 0.0
    speedup_enhanced: float = 0.0
    efficiency_basic: float = 0.0
    efficiency_enhanced: float = 0.0

    memory_improvement: float = 0.0
    reliability_improvement: float = 0.0

    system_info: dict[str, Any] = field(default_factory=dict)
    test_timestamp: str = ""

    def calculate_improvements(self) -> None:
        """Calculate improvement metrics."""
        if not self.sequential_metrics:
            return

        baseline_time = self.sequential_metrics.duration_seconds
        baseline_failures = self.sequential_metrics.failed_files

        # Calculate speedup
        if (
            self.parallel_basic_metrics
            and self.parallel_basic_metrics.duration_seconds > 0
        ):
            self.speedup_basic = (
                baseline_time / self.parallel_basic_metrics.duration_seconds
            )
            workers = self.parallel_basic_metrics.worker_count or 1
            self.efficiency_basic = self.speedup_basic / workers

        if (
            self.parallel_enhanced_metrics
            and self.parallel_enhanced_metrics.duration_seconds > 0
        ):
            self.speedup_enhanced = (
                baseline_time / self.parallel_enhanced_metrics.duration_seconds
            )
            workers = self.parallel_enhanced_metrics.worker_count or 1
            self.efficiency_enhanced = self.speedup_enhanced / workers

        # Calculate reliability improvement
        if self.parallel_enhanced_metrics:
            enhanced_failures = self.parallel_enhanced_metrics.failed_files
            if baseline_failures > 0:
                self.reliability_improvement = (
                    (baseline_failures - enhanced_failures) / baseline_failures * 100
                )

        # Calculate memory improvement
        if (
            self.parallel_basic_metrics
            and self.parallel_enhanced_metrics
            and self.parallel_basic_metrics.memory_peak_mb > 0
        ):
            basic_memory = self.parallel_basic_metrics.memory_peak_mb
            enhanced_memory = self.parallel_enhanced_metrics.memory_peak_mb
            self.memory_improvement = (
                (basic_memory - enhanced_memory) / basic_memory * 100
            )


class SystemMonitor:
    """System resource monitor for benchmark runs."""

    def __init__(self, sampling_interval: float = 1.0):
        """Initialize system monitor."""
        self.sampling_interval = sampling_interval
        self.cpu_samples: list[float] = []
        self.memory_samples: list[float] = []
        self.disk_io_samples: list[tuple[int, int]] = []  # (read_bytes, write_bytes)
        self._monitoring = False
        self._monitor_task: asyncio.Task | None = None

    async def start_monitoring(self) -> None:
        """Start system resource monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop system resource monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self) -> None:
        """Monitoring loop."""
        last_disk_io = psutil.disk_io_counters()

        while self._monitoring:
            try:
                # Sample CPU
                cpu_percent = psutil.cpu_percent(interval=None)
                self.cpu_samples.append(cpu_percent)

                # Sample memory
                memory = psutil.virtual_memory()
                memory_mb = memory.used / (1024 * 1024)
                self.memory_samples.append(memory_mb)

                # Sample disk I/O
                current_disk_io = psutil.disk_io_counters()
                if last_disk_io and current_disk_io:
                    read_bytes = current_disk_io.read_bytes - last_disk_io.read_bytes
                    write_bytes = current_disk_io.write_bytes - last_disk_io.write_bytes
                    self.disk_io_samples.append((read_bytes, write_bytes))
                    last_disk_io = current_disk_io

                await asyncio.sleep(self.sampling_interval)

            except Exception as e:
                logger.warning("System monitoring error: %s", e)
                await asyncio.sleep(self.sampling_interval)

    def get_summary(self) -> dict[str, Any]:
        """Get monitoring summary."""
        summary = {
            "cpu_average": statistics.mean(self.cpu_samples)
            if self.cpu_samples
            else 0.0,
            "cpu_peak": max(self.cpu_samples) if self.cpu_samples else 0.0,
            "memory_average_mb": statistics.mean(self.memory_samples)
            if self.memory_samples
            else 0.0,
            "memory_peak_mb": max(self.memory_samples) if self.memory_samples else 0.0,
            "sample_count": len(self.cpu_samples),
        }

        if self.disk_io_samples:
            total_read = sum(sample[0] for sample in self.disk_io_samples)
            total_write = sum(sample[1] for sample in self.disk_io_samples)
            summary.update(
                {
                    "total_disk_read_mb": total_read / (1024 * 1024),
                    "total_disk_write_mb": total_write / (1024 * 1024),
                }
            )

        return summary

    def reset(self) -> None:
        """Reset all collected samples."""
        self.cpu_samples.clear()
        self.memory_samples.clear()
        self.disk_io_samples.clear()


class BenchmarkRunner:
    """Main benchmark runner for testing decompilation performance."""

    def __init__(self, config: BenchmarkConfig):
        """Initialize benchmark runner."""
        self.config = config
        self.console = Console()
        self.monitor = SystemMonitor(config.resource_sampling_interval)

        # Ensure output directory exists
        self.config.output_directory.mkdir(parents=True, exist_ok=True)

    async def run_full_benchmark(self) -> ComparisonResult:
        """Run complete benchmark comparing all approaches."""
        self.console.print(
            Panel(
                "[bold blue]PowerRebuilder Decompilation Performance Benchmark[/bold blue]",
                style="white on blue",
            )
        )

        # Collect test files
        test_files = self._collect_test_files()
        if not test_files:
            raise ValueError("No test files found in input directory")

        self.console.print(f"Found {len(test_files)} test files")

        # Initialize result
        result = ComparisonResult(
            test_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            system_info=self._get_system_info(),
        )

        # Run sequential benchmark
        if self.config.test_sequential:
            self.console.print("\n[yellow]Running sequential benchmark...[/yellow]")
            result.sequential_metrics = await self._benchmark_sequential(test_files)

        # Run basic parallel benchmark
        if self.config.test_parallel_basic:
            self.console.print("\n[yellow]Running basic parallel benchmark...[/yellow]")
            result.parallel_basic_metrics = await self._benchmark_parallel_basic(
                test_files
            )

        # Run enhanced parallel benchmark
        if self.config.test_parallel_enhanced:
            self.console.print(
                "\n[yellow]Running enhanced parallel benchmark...[/yellow]"
            )
            result.parallel_enhanced_metrics = await self._benchmark_parallel_enhanced(
                test_files
            )

        # Calculate improvements
        result.calculate_improvements()

        # Display results
        self._display_results(result)

        # Save results
        if self.config.save_detailed_results:
            await self._save_results(result)

        return result

    def _collect_test_files(self) -> list[Path]:
        """Collect test files from input directory."""
        extensions = [".fun", ".men", ".mef", ".apf", ".udo", ".win"]
        files = []

        for ext in extensions:
            files.extend(self.config.input_directory.rglob(f"*{ext}"))

        # Apply file limit if specified
        if self.config.max_files_per_run:
            files = files[: self.config.max_files_per_run]

        return sorted(files)

    async def _benchmark_sequential(self, test_files: list[Path]) -> BenchmarkMetrics:
        """Benchmark sequential processing."""
        # Create temporary sequential coordinator (max_workers=1)

        metrics = BenchmarkMetrics()
        metrics.worker_count = 1
        metrics.cpu_count = psutil.cpu_count()
        metrics.system_memory_gb = psutil.virtual_memory().total / (1024**3)

        # Calculate file statistics
        metrics.total_files = len(test_files)
        file_sizes = []
        for file_path in test_files:
            try:
                size = file_path.stat().st_size
                file_sizes.append(size)
                metrics.total_bytes += size
            except Exception:
                pass

        if file_sizes:
            metrics.largest_file_mb = max(file_sizes) / (1024 * 1024)
            metrics.smallest_file_mb = min(file_sizes) / (1024 * 1024)

        # Create output directory
        output_dir = self.config.output_directory / "sequential"
        output_dir.mkdir(exist_ok=True)

        # Run benchmark
        await self.monitor.start_monitoring()

        start_time = time.time()

        try:
            # Use single-threaded coordinator
            coordinator = DecompileCoordinator(
                input_dir=self.config.input_directory, output_dir=output_dir
            )

            # Process files one by one
            for file_path in test_files:
                try:
                    coordinator.decompile_file(file_path)
                    metrics.processed_files += 1
                except Exception as e:
                    metrics.failed_files += 1
                    if "timeout" in str(e).lower():
                        metrics.timeout_failures += 1
                    elif "memory" in str(e).lower():
                        metrics.memory_failures += 1
                    else:
                        metrics.other_failures += 1

        finally:
            metrics.duration_seconds = time.time() - start_time
            await self.monitor.stop_monitoring()

        # Get system metrics
        system_summary = self.monitor.get_summary()
        metrics.cpu_utilization_percent = system_summary.get("cpu_average", 0.0)
        metrics.memory_peak_mb = system_summary.get("memory_peak_mb", 0.0)
        metrics.memory_average_mb = system_summary.get("memory_average_mb", 0.0)

        metrics.calculate_derived_metrics()
        self.monitor.reset()

        return metrics

    async def _benchmark_parallel_basic(
        self, test_files: list[Path]
    ) -> BenchmarkMetrics:
        """Benchmark basic parallel processing."""
        from src.decompile.parallel_coordinator import ParallelDecompileCoordinator

        metrics = BenchmarkMetrics()
        metrics.worker_count = psutil.cpu_count() or 4
        metrics.cpu_count = psutil.cpu_count()
        metrics.system_memory_gb = psutil.virtual_memory().total / (1024**3)

        # Calculate file statistics (same as sequential)
        metrics.total_files = len(test_files)
        file_sizes = []
        for file_path in test_files:
            try:
                size = file_path.stat().st_size
                file_sizes.append(size)
                metrics.total_bytes += size
            except Exception:
                pass

        if file_sizes:
            metrics.largest_file_mb = max(file_sizes) / (1024 * 1024)
            metrics.smallest_file_mb = min(file_sizes) / (1024 * 1024)

        # Create output directory
        output_dir = self.config.output_directory / "parallel_basic"
        output_dir.mkdir(exist_ok=True)

        # Run benchmark
        await self.monitor.start_monitoring()
        start_time = time.time()

        try:
            coordinator = ParallelDecompileCoordinator(
                input_dir=self.config.input_directory,
                output_dir=output_dir,
                use_adaptive_parallelism=False,  # Disable for baseline
            )

            result = coordinator.decompile()

            metrics.processed_files = result.get("processed_files", 0)
            metrics.failed_files = result.get("failed_files", 0)

        finally:
            metrics.duration_seconds = time.time() - start_time
            await self.monitor.stop_monitoring()

        # Get system metrics
        system_summary = self.monitor.get_summary()
        metrics.cpu_utilization_percent = system_summary.get("cpu_average", 0.0)
        metrics.memory_peak_mb = system_summary.get("memory_peak_mb", 0.0)
        metrics.memory_average_mb = system_summary.get("memory_average_mb", 0.0)

        metrics.calculate_derived_metrics()
        self.monitor.reset()

        return metrics

    async def _benchmark_parallel_enhanced(
        self, test_files: list[Path]
    ) -> BenchmarkMetrics:
        """Benchmark enhanced parallel processing."""
        metrics = BenchmarkMetrics()

        # Get optimal configuration
        config = get_config()
        metrics.worker_count = config.parallelism.max_workers or (
            psutil.cpu_count() or 4
        )
        metrics.cpu_count = psutil.cpu_count()
        metrics.system_memory_gb = psutil.virtual_memory().total / (1024**3)

        # Calculate file statistics
        metrics.total_files = len(test_files)
        file_sizes = []
        for file_path in test_files:
            try:
                size = file_path.stat().st_size
                file_sizes.append(size)
                metrics.total_bytes += size
            except Exception:
                pass

        if file_sizes:
            metrics.largest_file_mb = max(file_sizes) / (1024 * 1024)
            metrics.smallest_file_mb = min(file_sizes) / (1024 * 1024)

        # Create output directory
        output_dir = self.config.output_directory / "parallel_enhanced"
        output_dir.mkdir(exist_ok=True)

        # Run benchmark
        await self.monitor.start_monitoring()
        start_time = time.time()

        try:
            coordinator = EnhancedParallelDecompileCoordinator(
                input_dir=self.config.input_directory,
                output_dir=output_dir,
                max_workers=metrics.worker_count,
                enable_work_stealing=True,
                enable_memory_monitoring=True,
                enable_heartbeat_tracking=True,
            )

            result = coordinator.decompile(enable_resumption=True)

            metrics.processed_files = result.get("processed_files", 0)
            metrics.failed_files = result.get("failed_files", 0)
            metrics.cache_hit_rate_percent = result.get("cache_hit_rate_percent", 0)

            # Extract enhanced metrics
            load_balancer_stats = result.get("load_balancer_stats", {})
            metrics.work_steal_events = load_balancer_stats.get("steal_events", 0)

            memory_stats = result.get("memory_stats", {})
            metrics.throttle_events = memory_stats.get("throttle_events", 0)

        finally:
            metrics.duration_seconds = time.time() - start_time
            await self.monitor.stop_monitoring()

        # Get system metrics
        system_summary = self.monitor.get_summary()
        metrics.cpu_utilization_percent = system_summary.get("cpu_average", 0.0)
        metrics.memory_peak_mb = system_summary.get("memory_peak_mb", 0.0)
        metrics.memory_average_mb = system_summary.get("memory_average_mb", 0.0)

        metrics.calculate_derived_metrics()
        self.monitor.reset()

        return metrics

    def _display_results(self, result: ComparisonResult) -> None:
        """Display benchmark results in a formatted table."""
        table = Table(title="Benchmark Results Comparison")

        table.add_column("Metric", style="cyan")
        table.add_column("Sequential", style="white")
        table.add_column("Basic Parallel", style="yellow")
        table.add_column("Enhanced Parallel", style="green")
        table.add_column("Improvement", style="bold green")

        # Helper function to format values
        def fmt(value: Any, unit: str = "") -> str:
            if value is None:
                return "N/A"
            if isinstance(value, float):
                if unit == "%":
                    return f"{value:.1f}%"
                if unit == "s":
                    return f"{value:.2f}s"
                if unit == "MB":
                    return f"{value:.1f}MB"
                return f"{value:.2f}{unit}"
            return f"{value}{unit}"

        # Add rows
        rows = [
            (
                "Files Processed",
                fmt(
                    result.sequential_metrics.processed_files
                    if result.sequential_metrics
                    else None
                ),
                fmt(
                    result.parallel_basic_metrics.processed_files
                    if result.parallel_basic_metrics
                    else None
                ),
                fmt(
                    result.parallel_enhanced_metrics.processed_files
                    if result.parallel_enhanced_metrics
                    else None
                ),
                "",
            ),
            (
                "Processing Time",
                fmt(
                    result.sequential_metrics.duration_seconds
                    if result.sequential_metrics
                    else None,
                    "s",
                ),
                fmt(
                    result.parallel_basic_metrics.duration_seconds
                    if result.parallel_basic_metrics
                    else None,
                    "s",
                ),
                fmt(
                    result.parallel_enhanced_metrics.duration_seconds
                    if result.parallel_enhanced_metrics
                    else None,
                    "s",
                ),
                "",
            ),
            (
                "Speedup vs Sequential",
                "1.0x",
                f"{result.speedup_basic:.1f}x" if result.speedup_basic > 0 else "N/A",
                f"{result.speedup_enhanced:.1f}x"
                if result.speedup_enhanced > 0
                else "N/A",
                f"+{(result.speedup_enhanced - result.speedup_basic):.1f}x"
                if result.speedup_enhanced > result.speedup_basic
                else "",
            ),
            (
                "Files/Second",
                fmt(
                    result.sequential_metrics.files_per_second
                    if result.sequential_metrics
                    else None
                ),
                fmt(
                    result.parallel_basic_metrics.files_per_second
                    if result.parallel_basic_metrics
                    else None
                ),
                fmt(
                    result.parallel_enhanced_metrics.files_per_second
                    if result.parallel_enhanced_metrics
                    else None
                ),
                "",
            ),
            (
                "Peak Memory",
                fmt(
                    result.sequential_metrics.memory_peak_mb
                    if result.sequential_metrics
                    else None,
                    "MB",
                ),
                fmt(
                    result.parallel_basic_metrics.memory_peak_mb
                    if result.parallel_basic_metrics
                    else None,
                    "MB",
                ),
                fmt(
                    result.parallel_enhanced_metrics.memory_peak_mb
                    if result.parallel_enhanced_metrics
                    else None,
                    "MB",
                ),
                f"{result.memory_improvement:+.1f}%"
                if result.memory_improvement != 0
                else "",
            ),
            (
                "Failure Rate",
                fmt(
                    result.sequential_metrics.failure_rate_percent
                    if result.sequential_metrics
                    else None,
                    "%",
                ),
                fmt(
                    result.parallel_basic_metrics.failure_rate_percent
                    if result.parallel_basic_metrics
                    else None,
                    "%",
                ),
                fmt(
                    result.parallel_enhanced_metrics.failure_rate_percent
                    if result.parallel_enhanced_metrics
                    else None,
                    "%",
                ),
                f"{result.reliability_improvement:+.1f}%"
                if result.reliability_improvement != 0
                else "",
            ),
        ]

        for row in rows:
            table.add_row(*row)

        self.console.print("\n")
        self.console.print(table)

        # Performance summary
        if result.speedup_enhanced >= 8.0:
            status = "[bold green]✓ EXCELLENT[/bold green]"
        elif result.speedup_enhanced >= 4.0:
            status = "[bold yellow]✓ GOOD[/bold yellow]"
        elif result.speedup_enhanced >= 2.0:
            status = "[bold blue]~ FAIR[/bold blue]"
        else:
            status = "[bold red]✗ POOR[/bold red]"

        summary = f"""
[bold]Performance Summary:[/bold]
• Target Speedup: 8-16x on multi-core systems
• Achieved Speedup: {result.speedup_enhanced:.1f}x {status}
• Parallel Efficiency: {result.efficiency_enhanced * 100:.1f}%
• Memory Optimization: {result.memory_improvement:+.1f}%
• Reliability Improvement: {result.reliability_improvement:+.1f}%
        """

        self.console.print(Panel(summary.strip(), title="Benchmark Summary"))

    async def _save_results(self, result: ComparisonResult) -> None:
        """Save benchmark results to file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        if self.config.output_format == "json":
            output_file = (
                self.config.output_directory / f"benchmark_results_{timestamp}.json"
            )

            # Convert to JSON-serializable format
            results_dict = {
                "test_timestamp": result.test_timestamp,
                "system_info": result.system_info,
                "speedup_basic": result.speedup_basic,
                "speedup_enhanced": result.speedup_enhanced,
                "efficiency_basic": result.efficiency_basic,
                "efficiency_enhanced": result.efficiency_enhanced,
                "memory_improvement": result.memory_improvement,
                "reliability_improvement": result.reliability_improvement,
            }

            # Add metrics
            if result.sequential_metrics:
                results_dict["sequential"] = result.sequential_metrics.__dict__
            if result.parallel_basic_metrics:
                results_dict["parallel_basic"] = result.parallel_basic_metrics.__dict__
            if result.parallel_enhanced_metrics:
                results_dict["parallel_enhanced"] = (
                    result.parallel_enhanced_metrics.__dict__
                )

            with output_file.open("w") as f:
                json.dump(results_dict, f, indent=2)

            self.console.print(f"\nResults saved to: {output_file}")

    def _get_system_info(self) -> dict[str, Any]:
        """Get current system information."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": memory.total / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "disk_free_gb": disk.free / (1024**3),
            "platform": {
                "system": psutil.uname().system,
                "machine": psutil.uname().machine,
                "processor": psutil.uname().processor,
            },
            "python_version": __import__("sys").version,
        }


# CLI interface for running benchmarks
async def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="PowerRebuilder Decompilation Benchmark"
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing test files")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_results"),
        help="Output directory for results",
    )
    parser.add_argument("--max-files", type=int, help="Maximum files per test run")
    parser.add_argument(
        "--runs", type=int, default=3, help="Number of measurement runs"
    )
    parser.add_argument(
        "--skip-sequential",
        action="store_true",
        help="Skip sequential benchmark (faster testing)",
    )
    parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Output format"
    )

    args = parser.parse_args()

    # Create config
    config = BenchmarkConfig(
        input_directory=args.input_dir,
        output_directory=args.output_dir,
        measurement_runs=args.runs,
        max_files_per_run=args.max_files,
        test_sequential=not args.skip_sequential,
        output_format=args.format,
    )

    # Run benchmark
    runner = BenchmarkRunner(config)
    await runner.run_full_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
