#!/usr/bin/env python3
"""Performance benchmark script for PowerRebuilder optimizations.

This script tests various performance improvements including:
- Caching effectiveness
- Parallel processing benefits
- Streaming decoder performance
- Memory usage optimization
"""

import argparse
import json
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.performance import (
    get_performance_monitor,
    log_system_info,
    monitor_performance,
)
from src.decompile.coordinator import DecompileCoordinator
from src.decompile.parallel_coordinator import ParallelDecompileCoordinator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PowerRebuilderBenchmark:
    """Comprehensive benchmark for PowerRebuilder performance optimizations."""

    def __init__(self, input_dir: Path, output_base_dir: Path):
        self.input_dir = input_dir
        self.output_base_dir = output_base_dir
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "input_dir": str(input_dir),
            "benchmarks": [],
        }

        # Ensure output directory exists
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

    def run_all_benchmarks(self) -> dict:
        """Run all performance benchmarks."""
        logger.info("Starting PowerRebuilder Performance Benchmark Suite")
        log_system_info()

        # Benchmark configurations to test
        benchmarks = [
            {
                "name": "baseline_sequential",
                "description": "Baseline sequential processing without optimizations",
                "config": {
                    "enable_cache": False,
                    "enable_parallel": False,
                    "use_streaming": False,
                },
            },
            {
                "name": "cache_enabled",
                "description": "Sequential processing with caching enabled",
                "config": {
                    "enable_cache": True,
                    "enable_parallel": False,
                    "use_streaming": False,
                },
            },
            {
                "name": "parallel_processes",
                "description": "Parallel processing using processes",
                "config": {
                    "enable_cache": False,
                    "enable_parallel": True,
                    "use_processes": True,
                    "use_streaming": False,
                },
            },
            {
                "name": "parallel_threads",
                "description": "Parallel processing using threads",
                "config": {
                    "enable_cache": False,
                    "enable_parallel": True,
                    "use_processes": False,
                    "use_streaming": False,
                },
            },
            {
                "name": "cache_and_parallel",
                "description": "Both caching and parallel processing",
                "config": {
                    "enable_cache": True,
                    "enable_parallel": True,
                    "use_processes": True,
                    "use_streaming": False,
                },
            },
        ]

        for benchmark_config in benchmarks:
            try:
                result = self.run_benchmark(benchmark_config)
                self.results["benchmarks"].append(result)

                # Clean up between benchmarks
                self._cleanup_cache()

            except Exception as e:
                logger.error("Benchmark %s failed: %s", benchmark_config["name"], e)
                result = {
                    "name": benchmark_config["name"],
                    "description": benchmark_config["description"],
                    "status": "failed",
                    "error": str(e),
                    "duration": 0,
                }
                self.results["benchmarks"].append(result)

        # Analyze and report results
        self._analyze_results()
        self._save_results()

        return self.results

    def run_benchmark(self, benchmark_config: dict) -> dict:
        """Run a single benchmark configuration."""
        name = benchmark_config["name"]
        config = benchmark_config["config"]

        logger.info("\n" + "=" * 60)
        logger.info("Running benchmark: %s", name)
        logger.info("Description: %s", benchmark_config["description"])
        logger.info("Configuration: %s", config)
        logger.info("=" * 60)

        # Create output directory for this benchmark
        output_dir = self.output_base_dir / f"benchmark_{name}"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

        # Reset performance monitor
        from src.common.performance import reset_performance_monitor

        reset_performance_monitor()

        start_time = time.time()

        try:
            with monitor_performance(f"benchmark_{name}") as metrics:
                if config.get("enable_parallel", False):
                    # Use parallel coordinator
                    coordinator = ParallelDecompileCoordinator(
                        input_dir=self.input_dir,
                        output_dir=output_dir,
                        use_processes=config.get("use_processes", True),
                        use_adaptive_parallelism=True,
                    )
                    result = coordinator.decompile()
                else:
                    # Use sequential coordinator
                    coordinator = DecompileCoordinator(
                        input_dir=self.input_dir,
                        output_dir=output_dir,
                    )
                    result = coordinator.decompile(
                        enable_cache=config.get("enable_cache", False),
                        enable_parallel=False,
                    )

                # Update metrics
                metrics.files_processed = result.get("total_files", 0)
                metrics.cache_hits = result.get("cache_hits", 0)
                metrics.cache_misses = result.get("cache_misses", 0)

            duration = time.time() - start_time

            # Get performance monitor summary
            monitor = get_performance_monitor()
            performance_summary = monitor.get_summary()

            benchmark_result = {
                "name": name,
                "description": benchmark_config["description"],
                "config": config,
                "status": "completed",
                "duration": duration,
                "result": result,
                "performance": performance_summary,
            }

            logger.info("Benchmark %s completed in %.2f seconds", name, duration)
            if result.get("total_files", 0) > 0:
                logger.info("  Files processed: %d", result["total_files"])
                logger.info("  Success rate: %s", result.get("success_rate", "N/A"))
                if config.get("enable_cache"):
                    logger.info(
                        "  Cache hit rate: %s", result.get("cache_hit_rate", "N/A")
                    )

            return benchmark_result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Benchmark %s failed after %.2f seconds: %s", name, duration, e
            )

            return {
                "name": name,
                "description": benchmark_config["description"],
                "config": config,
                "status": "failed",
                "duration": duration,
                "error": str(e),
            }

    def _cleanup_cache(self):
        """Clean up cache between benchmarks."""
        try:
            import asyncio

            from src.core.cache_config import get_cache_manager

            cache_manager = get_cache_manager()
            asyncio.run(cache_manager.clear_all())
            logger.debug("Cache cleared between benchmarks")

        except Exception as e:
            logger.warning("Failed to clear cache: %s", e)

    def _analyze_results(self):
        """Analyze benchmark results and generate insights."""
        completed_benchmarks = [
            b for b in self.results["benchmarks"] if b["status"] == "completed"
        ]

        if len(completed_benchmarks) < 2:
            logger.warning("Need at least 2 successful benchmarks for comparison")
            return

        logger.info("\n" + "=" * 60)
        logger.info("BENCHMARK ANALYSIS")
        logger.info("=" * 60)

        # Find baseline
        baseline = next(
            (b for b in completed_benchmarks if b["name"] == "baseline_sequential"),
            None,
        )

        if baseline:
            baseline_time = baseline["duration"]
            logger.info("Baseline time: %.2f seconds", baseline_time)

            # Compare other benchmarks to baseline
            for benchmark in completed_benchmarks:
                if benchmark["name"] == "baseline_sequential":
                    continue

                duration = benchmark["duration"]
                improvement = ((baseline_time - duration) / baseline_time) * 100
                speedup = baseline_time / duration if duration > 0 else 0

                logger.info("%s:", benchmark["name"])
                logger.info("  Duration: %.2f seconds", duration)
                logger.info("  Improvement: %+.1f%%", improvement)
                logger.info("  Speedup: %.2fx", speedup)

                # Cache statistics
                result = benchmark.get("result", {})
                if result.get("cache_enabled"):
                    logger.info(
                        "  Cache hit rate: %s", result.get("cache_hit_rate", "N/A")
                    )

        # Performance insights
        logger.info("\nPerformance Insights:")
        self._generate_insights(completed_benchmarks)

    def _generate_insights(self, benchmarks: list):
        """Generate performance insights from benchmark results."""
        insights = []

        # Cache effectiveness
        cache_benchmarks = [
            b for b in benchmarks if b.get("result", {}).get("cache_enabled")
        ]
        if cache_benchmarks:
            avg_cache_hit_rate = sum(
                float(b["result"].get("cache_hit_rate", "0").rstrip("%"))
                for b in cache_benchmarks
            ) / len(cache_benchmarks)

            if avg_cache_hit_rate > 50:
                insights.append(
                    f"Caching is highly effective with {avg_cache_hit_rate:.1f}% average hit rate"
                )
            elif avg_cache_hit_rate > 20:
                insights.append(
                    f"Caching shows moderate effectiveness with {avg_cache_hit_rate:.1f}% hit rate"
                )
            else:
                insights.append(
                    f"Caching has low effectiveness with {avg_cache_hit_rate:.1f}% hit rate - check cache configuration"
                )

        # Parallel processing effectiveness
        parallel_benchmarks = [
            b for b in benchmarks if b.get("config", {}).get("enable_parallel")
        ]
        sequential_benchmarks = [
            b for b in benchmarks if not b.get("config", {}).get("enable_parallel")
        ]

        if parallel_benchmarks and sequential_benchmarks:
            avg_parallel_time = sum(b["duration"] for b in parallel_benchmarks) / len(
                parallel_benchmarks
            )
            avg_sequential_time = sum(
                b["duration"] for b in sequential_benchmarks
            ) / len(sequential_benchmarks)

            if avg_parallel_time < avg_sequential_time * 0.7:
                insights.append(
                    "Parallel processing provides significant performance benefits"
                )
            elif avg_parallel_time < avg_sequential_time * 0.9:
                insights.append(
                    "Parallel processing provides moderate performance benefits"
                )
            else:
                insights.append(
                    "Parallel processing shows limited benefits - may be I/O bound"
                )

        # Log insights
        for insight in insights:
            logger.info("  - %s", insight)

    def _save_results(self):
        """Save benchmark results to file."""
        results_file = self.output_base_dir / "benchmark_results.json"

        with results_file.open("w") as f:
            json.dump(self.results, f, indent=2)

        logger.info("\nBenchmark results saved to: %s", results_file)

        # Also save a summary report
        summary_file = self.output_base_dir / "benchmark_summary.txt"
        with summary_file.open("w") as f:
            f.write("PowerRebuilder Performance Benchmark Results\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Timestamp: {self.results['timestamp']}\n")
            f.write(f"Input Directory: {self.results['input_dir']}\n\n")

            for benchmark in self.results["benchmarks"]:
                f.write(f"Benchmark: {benchmark['name']}\n")
                f.write(f"Description: {benchmark['description']}\n")
                f.write(f"Status: {benchmark['status']}\n")
                f.write(f"Duration: {benchmark['duration']:.2f} seconds\n")

                if benchmark["status"] == "completed":
                    result = benchmark.get("result", {})
                    f.write(f"Files processed: {result.get('total_files', 'N/A')}\n")
                    f.write(f"Success rate: {result.get('success_rate', 'N/A')}\n")
                    if result.get("cache_enabled"):
                        f.write(
                            f"Cache hit rate: {result.get('cache_hit_rate', 'N/A')}\n"
                        )

                f.write("\n")

        logger.info("Benchmark summary saved to: %s", summary_file)


def main():
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(description="PowerRebuilder Performance Benchmark")
    parser.add_argument(
        "input_dir", type=Path, help="Directory containing P-code files to benchmark"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for benchmark results",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set default output directory
    if args.output_dir is None:
        args.output_dir = Path("benchmark_output") / datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

    # Validate input directory
    if not args.input_dir.exists():
        logger.error("Input directory does not exist: %s", args.input_dir)
        sys.exit(1)

    # Run benchmarks
    benchmark = PowerRebuilderBenchmark(args.input_dir, args.output_dir)
    results = benchmark.run_all_benchmarks()

    # Print final summary
    completed_count = sum(
        1 for b in results["benchmarks"] if b["status"] == "completed"
    )
    total_count = len(results["benchmarks"])

    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK SUITE COMPLETED")
    logger.info("=" * 60)
    logger.info("Completed: %d/%d benchmarks", completed_count, total_count)
    logger.info("Results saved to: %s", args.output_dir)


if __name__ == "__main__":
    main()
