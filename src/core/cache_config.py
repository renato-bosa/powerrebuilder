"""Cache configuration and management for PowerRebuilder."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.core.cache import FileCache, LRUCache

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for a cache instance."""

    enabled: bool = True
    type: str = "memory"  # "memory", "file", or "hybrid"
    size: int = 1000  # Max entries for memory cache
    memory: int = 512  # Max memory in MB
    ttl: int = 3600  # Time to live in seconds
    directory: Path | None = None


class CacheManager:
    """Manages caches for all pipeline stages."""

    def __init__(self, base_config: dict[str, Any] | None = None) -> None:
        """Initialize cache manager with configuration."""
        self.config = base_config or {}
        self.enabled = self._get_bool_env("POWERREBUILDER_CACHE_ENABLED", True)

        # Base cache directory
        cache_dir = os.getenv(
            "POWERREBUILDER_CACHE_DIR", str(Path.home() / ".powerrebuilder" / "cache")
        )
        self.base_cache_dir = Path(cache_dir)
        self.base_cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize stage caches
        self._caches: dict[str, Any] = {}
        self._init_stage_caches()

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "yes", "1", "on")

    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer from environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _get_stage_config(self, stage: str) -> CacheConfig:
        """Get configuration for a specific stage."""
        # Default configurations per stage
        defaults = {
            "extract": CacheConfig(
                type="file",
                ttl=self._get_int_env("POWERREBUILDER_CACHE_TTL_EXTRACT", 86400),
            ),
            "decompile": CacheConfig(
                type="file",
                ttl=self._get_int_env("POWERREBUILDER_CACHE_TTL_DECOMPILE", 86400),
            ),
            "parse": CacheConfig(
                type="hybrid",
                size=500,
                ttl=self._get_int_env("POWERREBUILDER_CACHE_TTL_PARSE", 43200),
            ),
            "model": CacheConfig(
                type="memory",
                size=500,
                ttl=self._get_int_env("POWERREBUILDER_CACHE_TTL_MODEL", 21600),
            ),
            "generate": CacheConfig(
                type="file",
                ttl=self._get_int_env("POWERREBUILDER_CACHE_TTL_GENERATE", 604800),
            ),
        }

        # Get stage-specific config
        stage_config = defaults.get(stage, CacheConfig())

        # Override with config file settings
        if "cache" in self.config and "stages" in self.config["cache"]:
            if stage in self.config["cache"]["stages"]:
                cfg = self.config["cache"]["stages"][stage]
                stage_config.enabled = cfg.get("enabled", stage_config.enabled)
                stage_config.type = cfg.get("type", stage_config.type)
                stage_config.size = cfg.get("size", stage_config.size)
                stage_config.memory = cfg.get("memory", stage_config.memory)
                stage_config.ttl = cfg.get("ttl", stage_config.ttl)

        # Set directory
        stage_config.directory = self.base_cache_dir / stage

        return stage_config

    def _init_stage_caches(self) -> None:
        """Initialize caches for all stages."""
        stages = ["extract", "decompile", "parse", "model", "generate"]

        for stage in stages:
            config = self._get_stage_config(stage)

            if not config.enabled or not self.enabled:
                logger.info(f"Cache disabled for stage: {stage}")
                continue

            if config.type == "memory":
                self._caches[stage] = LRUCache(
                    max_size=config.size,
                    max_memory=config.memory * 1024 * 1024,
                )
            elif config.type == "file":
                cache_dir = config.directory or self.base_cache_dir / stage
                self._caches[stage] = FileCache(
                    cache_dir=cache_dir,
                    ttl=config.ttl,
                )
            elif config.type == "hybrid":
                # Use both memory and file cache
                self._caches[f"{stage}_memory"] = LRUCache(
                    max_size=config.size,
                    max_memory=config.memory * 1024 * 1024,
                )
                cache_dir = config.directory or self.base_cache_dir / f"{stage}_file"
                self._caches[f"{stage}_file"] = FileCache(
                    cache_dir=cache_dir,
                    ttl=config.ttl,
                )

            logger.info(
                f"Initialized {config.type} cache for stage: {stage} "
                f"(size={config.size}, ttl={config.ttl}s)"
            )

    def get_cache(self, stage: str, cache_type: str = "default") -> Any:
        """Get cache for a specific stage.

        Args:
            stage: Pipeline stage name
            cache_type: "default", "memory", or "file" for hybrid caches

        Returns:
            Cache instance or None if disabled
        """
        if not self.enabled:
            return None

        if cache_type == "default":
            return self._caches.get(stage)
        return self._caches.get(f"{stage}_{cache_type}")

    async def get_or_compute(
        self, stage: str, key: str, compute_func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Get from cache or compute if missing.

        Args:
            stage: Pipeline stage name
            key: Cache key
            compute_func: Function to compute value if not cached
            *args, **kwargs: Arguments for compute_func

        Returns:
            Cached or computed value
        """
        cache = self.get_cache(stage)
        if not cache:
            # Cache disabled, compute directly
            return await compute_func(*args, **kwargs)

        # Try memory cache first for hybrid
        if stage in ["parse"] and self.get_cache(stage, "memory"):
            memory_cache = self.get_cache(stage, "memory")
            result = await memory_cache.get(key)
            if result is not None:
                logger.debug(f"Memory cache hit for {stage}: {key}")
                return result

        # Try main cache
        result = await cache.get(key)
        if result is not None:
            logger.debug(f"Cache hit for {stage}: {key}")

            # Store in memory cache for hybrid
            if stage in ["parse"] and self.get_cache(stage, "memory"):
                memory_cache = self.get_cache(stage, "memory")
                await memory_cache.put(key, result)

            return result

        # Compute value
        logger.debug(f"Cache miss for {stage}: {key}")
        result = await compute_func(*args, **kwargs)

        # Store in cache
        await cache.put(key, result)

        # Store in memory cache for hybrid
        if stage in ["parse"] and self.get_cache(stage, "memory"):
            memory_cache = self.get_cache(stage, "memory")
            await memory_cache.put(key, result)

        return result

    async def clear_stage(self, stage: str) -> None:
        """Clear cache for a specific stage."""
        cache = self.get_cache(stage)
        if cache:
            await cache.clear()
            logger.info(f"Cleared cache for stage: {stage}")

        # Clear hybrid caches
        for cache_type in ["memory", "file"]:
            cache = self.get_cache(stage, cache_type)
            if cache:
                await cache.clear()

    async def clear_all(self) -> None:
        """Clear all caches."""
        for stage in ["extract", "decompile", "parse", "model", "generate"]:
            await self.clear_stage(stage)

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all caches."""
        stats = {}

        for stage in ["extract", "decompile", "parse", "model", "generate"]:
            cache = self.get_cache(stage)
            if cache and hasattr(cache, "stats"):
                stats[stage] = cache.stats()

            # Get hybrid cache stats
            for cache_type in ["memory", "file"]:
                cache = self.get_cache(stage, cache_type)
                if cache and hasattr(cache, "stats"):
                    stats[f"{stage}_{cache_type}"] = cache.stats()

        return stats

    async def warm_cache(
        self, input_dir: Path, stages: list[str] | None = None
    ) -> None:
        """Pre-warm caches by processing files.

        Args:
            input_dir: Directory containing input files
            stages: List of stages to warm (default: all)
        """
        if stages is None:
            stages = ["extract", "decompile", "parse", "model", "generate"]

        logger.info(f"Warming caches for stages: {stages}")

        # TODO: Implement cache warming logic
        # This would involve running each stage with cache enabled
        # to populate the caches before actual processing


# Global cache manager instance
_cache_manager: CacheManager | None = None


def get_cache_manager(config: dict[str, Any] | None = None) -> CacheManager:
    """Get or create global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(config)
    return _cache_manager
