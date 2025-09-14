#!/usr/bin/env python3
"""Benchmark script to measure cache performance improvements.

This script runs the PowerRebuilder pipeline with and without caching
to measure performance improvements.
"""

import json
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import click

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.pipeline.pipeline_coordinator import PipelineCoordinator
from src.core.cache_config import get_cache_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Runs benchmarks to measure cache performance."""

    def __init__(self, input_dir: Path, output_base_dir: Path):
        self.input_dir = input_dir
        self.output_base_dir = output_base_dir
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "input_dir": str(input_dir),
            "runs": [],
        }

    def run_pipeline(self, enable_cache: bool, run_name: str) -> dict[str, Any]:
        """Run the pipeline and measure performance."""
        logger.info("Starting %s run...", run_name)

        # Create output directory
        output_dir = self.output_base_dir / run_name.replace(" ", "_").lower()
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

        # Configure pipeline
        config = {
            "cache": {"enabled": enable_cache},
            "extract": {"enable_cache": enable_cache},
            "decompile": {"enable_cache": enable_cache},
            "parse": {"enable_cache": enable_cache},
            "model": {"enable_cache": enable_cache},
            "generate": {"enable_cache": enable_cache},
        }

        # Create coordinator
        coordinator = PipelineCoordinator(
            input_dir=self.input_dir,
            output_dir=output_dir,
            config=config,
        )

        # Measure execution time
        start_time = time.time()

        try:
            # Run pipeline
            summary = coordinator.run(enable_cache=enable_cache)

            elapsed_time = time.time() - start_time

            # Get cache statistics if enabled
            cache_stats = {}
            if enable_cache:
                cache_manager = get_cache_manager(config)
                cache_stats = cache_manager.get_stats()

            # Collect results
            result = {
                "run_name": run_name,
                "cache_enabled": enable_cache,
                "elapsed_time": elapsed_time,
                "summary": summary,
                "cache_stats": cache_stats,
            }

            logger.info("%s completed in %.1f seconds", run_name, elapsed_time)

            return result

        except Exception as e:
            logger.error("Pipeline failed: %s", e)
            return {
                "run_name": run_name,
                "cache_enabled": enable_cache,
                "elapsed_time": time.time() - start_time,
                "error": str(e),
            }

    def run_benchmark(self, iterations: int = 3) -> None:
        """Run complete benchmark with multiple iterations."""
        logger.info("Running benchmark with %s iterations", iterations)

        # Clear all caches before starting
        logger.info("Clearing all caches...")
        cache_manager = get_cache_manager()
        import asyncio

        asyncio.run(cache_manager.clear_all())

        # Run without cache (baseline)
        logger.info("\n" + "=" * 60)
        logger.info("BASELINE RUN (No Cache)")
        logger.info("=" * 60)

        baseline_result = self.run_pipeline(False, "Baseline (No Cache)")
        self.results["runs"].append(baseline_result)

        # Run with cache (cold)
        logger.info("\n" + "=" * 60)
        logger.info("FIRST RUN WITH CACHE (Cold Cache)")
        logger.info("=" * 60)

        cold_cache_result = self.run_pipeline(True, "First Run (Cold Cache)")
        self.results["runs"].append(cold_cache_result)

        # Run with cache (warm) - multiple iterations
        for i in range(iterations):
            logger.info("\n" + "=" * 60)
            logger.info("CACHED RUN %s (Warm Cache)", i + 1)
            logger.info("=" * 60)

            warm_cache_result = self.run_pipeline(True, f"Cached Run {i + 1}")
            self.results["runs"].append(warm_cache_result)

        # Calculate and display results
        self._analyze_results()

    def _analyze_results(self) -> None:
        """Analyze and display benchmark results."""
        logger.info("\n" + "=" * 60)
        logger.info("BENCHMARK RESULTS")
        logger.info("=" * 60)

        # Extract timings
        baseline_time = None
        cold_cache_time = None
        warm_cache_times = []

        for run in self.results["runs"]:
            if "error" in run:
                continue

            if not run["cache_enabled"]:
                baseline_time = run["elapsed_time"]
            elif "First Run" in run["run_name"]:
                cold_cache_time = run["elapsed_time"]
            else:
                warm_cache_times.append(run["elapsed_time"])

        # Display results
        if baseline_time:
            logger.info("Baseline (no cache): %.1f seconds", baseline_time)

        if cold_cache_time:
            logger.info("First run (cold cache): %.1f seconds", cold_cache_time)
            if baseline_time:
                overhead = ((cold_cache_time - baseline_time) / baseline_time) * 100
                logger.info("  Cache overhead: %+.1f%%", overhead)

        if warm_cache_times:
            avg_warm_time = sum(warm_cache_times) / len(warm_cache_times)
            logger.info("Average cached run: %.1f seconds", avg_warm_time)

            if baseline_time:
                improvement = ((baseline_time - avg_warm_time) / baseline_time) * 100
                speedup = baseline_time / avg_warm_time
                logger.info("  Improvement: %.1f%%", improvement)
                logger.info("  Speedup: %.1fx", speedup)

        # Cache statistics
        logger.info("\nCache Statistics:")
        logger.info("-" * 40)

        for run in self.results["runs"]:
            if run.get("cache_enabled") and "cache_stats" in run:
                logger.info("\n%s:", run["run_name"])
                self._print_cache_stats(run["cache_stats"])

        # Save results
        self._save_results()

    def _print_cache_stats(self, stats: dict[str, Any]) -> None:
        """Print cache statistics."""
        total_hits = 0
        total_misses = 0

        for stage, stage_stats in stats.items():
            if isinstance(stage_stats, dict):
                hits = stage_stats.get("hits", 0)
                misses = stage_stats.get("misses", 0)
                total = hits + misses

                if total > 0:
                    hit_rate = (hits / total) * 100
                    logger.info(
                        "  %s: %d/%d hits (%.1f%%)", stage, hits, total, hit_rate
                    )

                    total_hits += hits
                    total_misses += misses

        total = total_hits + total_misses
        if total > 0:
            overall_hit_rate = (total_hits / total) * 100
            logger.info(
                "  Overall: %s/%s hits (%.1f%)", total_hits, total, overall_hit_rate
            )

    def _save_results(self) -> None:
        """Save benchmark results to file."""
        output_file = self.output_base_dir / "benchmark_results.json"

        with output_file.open("w") as f:
            json.dump(self.results, f, indent=2)

        logger.info("\nResults saved to: %s", output_file)


@click.command()
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--output-dir", default="/tmp/powerrebuilder_benchmark", help="Output directory"
)
@click.option("--iterations", default=3, help="Number of warm cache iterations")
def main(input_dir: str, output_dir: str, iterations: int):
    """Run cache performance benchmark."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Run benchmark
    runner = BenchmarkRunner(input_path, output_path)
    runner.run_benchmark(iterations)


if __name__ == "__main__":
    main()
