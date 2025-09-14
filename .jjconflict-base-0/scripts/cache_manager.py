#!/usr/bin/env python3
"""Cache management utility for PowerRebuilder.

This script provides utilities for managing the PowerRebuilder cache:
- Clear caches (all or specific stages)
- View cache statistics
- Warm up caches
- Export/import cache data
"""

import asyncio
import json
import logging
import sys
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


@click.group()
def cli():
    """PowerRebuilder cache management utility."""


@cli.command()
@click.option("--stage", help="Clear cache for specific stage")
@click.option("--all", "clear_all", is_flag=True, help="Clear all caches")
@click.option("--config", type=click.Path(exists=True), help="Configuration file")
def clear(stage: str | None, clear_all: bool, config: str | None):
    """Clear cache entries."""

    async def _clear():
        # Load configuration
        config_data = {}
        if config:
            with open(config) as f:
                config_data = json.load(f)

        # Get cache manager
        cache_manager = get_cache_manager(config_data)

        if clear_all:
            logger.info("Clearing all caches...")
            await cache_manager.clear_all()
            logger.info("All caches cleared")
        elif stage:
            logger.info("Clearing cache for stage: %s", stage)
            await cache_manager.clear_stage(stage)
            logger.info("Cache cleared for stage: %s", stage)
        else:
            logger.error("Please specify --stage or --all")
            sys.exit(1)

    asyncio.run(_clear())


@cli.command()
@click.option("--stage", help="Show statistics for specific stage")
@click.option("--detailed", is_flag=True, help="Show detailed statistics")
@click.option("--config", type=click.Path(exists=True), help="Configuration file")
def stats(stage: str | None, detailed: bool, config: str | None):
    """View cache statistics."""

    # Load configuration
    config_data = {}
    if config:
        with open(config) as f:
            config_data = json.load(f)

    # Get cache manager
    cache_manager = get_cache_manager(config_data)

    # Get statistics
    stats = cache_manager.get_stats()

    if stage:
        # Show statistics for specific stage
        if stage in stats:
            _print_stage_stats(stage, stats[stage], detailed)
        else:
            logger.error("No cache statistics for stage: %s", stage)
    else:
        # Show statistics for all stages
        logger.info("Cache Statistics Summary")
        logger.info("=" * 60)

        total_hits = 0
        total_misses = 0
        total_memory = 0

        for stage_name, stage_stats in stats.items():
            if isinstance(stage_stats, dict):
                logger.info("\n%s Cache:", stage_name.upper())
                _print_stage_stats(stage_name, stage_stats, detailed)

                total_hits += stage_stats.get("hits", 0)
                total_misses += stage_stats.get("misses", 0)
                total_memory += stage_stats.get("memory", 0)

        # Overall statistics
        logger.info("\nOverall Statistics:")
        logger.info("-" * 40)

        total_requests = total_hits + total_misses
        if total_requests > 0:
            overall_hit_rate = (total_hits / total_requests) * 100
            logger.info("Total requests: %s", f"{total_requests:,}")
            logger.info("Total hits: %s", f"{total_hits:,}")
            logger.info("Total misses: %s", f"{total_misses:,}")
            logger.info("Overall hit rate: %.1f%%", overall_hit_rate)

        logger.info("Total memory usage: %s", _format_bytes(total_memory))


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--stages", help="Comma-separated list of stages to warm")
@click.option("--config", type=click.Path(exists=True), help="Configuration file")
@click.option("--parallel", is_flag=True, help="Warm caches in parallel")
def warm(input_dir: str, stages: str | None, config: str | None, parallel: bool):
    """Warm up caches by processing files."""

    async def _warm():
        # Load configuration
        config_data = {}
        if config:
            with open(config) as f:
                config_data = json.load(f)

        # Parse stages
        stage_list = None
        if stages:
            stage_list = [s.strip() for s in stages.split(",")]

        # Get cache manager
        cache_manager = get_cache_manager(config_data)

        logger.info("Warming caches for directory: %s", input_dir)

        if stage_list:
            logger.info("Stages to warm: %s", ", ".join(stage_list))
        else:
            logger.info("Warming all stages")

        # Create temporary output directory
        output_dir = Path("/tmp/powerrebuilder_cache_warm")
        output_dir.mkdir(exist_ok=True)

        # Enable caching in config
        config_data["cache"] = {"enabled": True}

        # Create pipeline coordinator
        coordinator = PipelineCoordinator(
            input_dir=input_dir,
            output_dir=output_dir,
            config=config_data,
        )

        # Run pipeline to warm caches
        start_time = asyncio.get_event_loop().time()

        if parallel:
            await coordinator.run_async(use_streaming=True, enable_cache=True)
        else:
            coordinator.run(enable_cache=True)

        elapsed_time = asyncio.get_event_loop().time() - start_time

        logger.info("Cache warming completed in %.1f seconds", elapsed_time)

        # Show cache statistics after warming
        stats = cache_manager.get_stats()
        logger.info("\nCache statistics after warming:")

        for stage_name, stage_stats in stats.items():
            if isinstance(stage_stats, dict) and stage_stats.get("size", 0) > 0:
                logger.info("{stage_name}: %s entries", stage_stats["size"])

    asyncio.run(_warm())


@cli.command()
@click.argument("output_file", type=click.Path())
@click.option("--stage", help="Export specific stage only")
@click.option("--config", type=click.Path(exists=True), help="Configuration file")
def export(output_file: str, stage: str | None, config: str | None):
    """Export cache data to file."""

    async def _export():
        # Load configuration
        config_data = {}
        if config:
            with open(config) as f:
                config_data = json.load(f)

        # Get cache manager
        get_cache_manager(config_data)

        logger.info("Exporting cache to: %s", output_file)

        # TODO: Implement cache export
        # This would involve serializing cache contents to a file
        # that can be imported later

        logger.warning("Cache export not yet implemented")

    asyncio.run(_export())


@cli.command("import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--stage", help="Import to specific stage only")
@click.option("--config", type=click.Path(exists=True), help="Configuration file")
def import_cache(input_file: str, stage: str | None, config: str | None):
    """Import cache data from file."""

    async def _import():
        # Load configuration
        config_data = {}
        if config:
            with open(config) as f:
                config_data = json.load(f)

        # Get cache manager
        get_cache_manager(config_data)

        logger.info("Importing cache from: %s", input_file)

        # TODO: Implement cache import
        # This would involve deserializing cache contents from a file
        # and loading them into the appropriate caches

        logger.warning("Cache import not yet implemented")

    asyncio.run(_import())


def _print_stage_stats(stage: str, stats: dict[str, Any], detailed: bool):
    """Print statistics for a single stage."""
    logger.info("-" * 40)

    # Basic statistics
    size = stats.get("size", 0)
    memory = stats.get("memory", 0)
    hits = stats.get("hits", 0)
    misses = stats.get("misses", 0)

    logger.info("Entries: %s", f"{size:,}")
    logger.info("Memory usage: %s", _format_bytes(memory))

    total = hits + misses
    if total > 0:
        hit_rate = (hits / total) * 100
        logger.info("Hits: %s", f"{hits:,}")
        logger.info("Misses: %s", f"{misses:,}")
        logger.info("Hit rate: %.1f%%", hit_rate)

    if detailed:
        # Additional detailed statistics
        if "avg_entry_size" in stats:
            logger.info(
                "Average entry size: %s", _format_bytes(stats["avg_entry_size"])
            )

        if "evictions" in stats:
            logger.info("Evictions: %s", f"{stats['evictions']:,}")

        if "oldest_entry" in stats:
            logger.info("Oldest entry: %s", stats["oldest_entry"])


def _format_bytes(size: int) -> str:
    """Format byte size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


if __name__ == "__main__":
    cli()
