"""Caching utilities for PowerRebuilder."""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    key: str
    value: Any
    size: int
    created_at: float
    accessed_at: float
    access_count: int = 0

    def touch(self) -> None:
        """Update access time and count."""
        self.accessed_at = time.time()
        self.access_count += 1


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, max_size: int = 1000, max_memory: int | None = None) -> None:
        self.max_size = max_size
        self.max_memory = max_memory or (1024 * 1024 * 512)  # 512MB default
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._current_memory = 0
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                entry = self._cache.pop(key)
                entry.touch()
                self._cache[key] = entry
                self._hits += 1
                return entry.value
            self._misses += 1
            return None

    async def put(self, key: str, value: Any, size: int | None = None) -> None:
        """Put value in cache."""
        if size is None:
            # Estimate size
            size = len(pickle.dumps(value))

        async with self._lock:
            # Remove if already exists
            if key in self._cache:
                old_entry = self._cache.pop(key)
                self._current_memory -= old_entry.size

            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                size=size,
                created_at=time.time(),
                accessed_at=time.time(),
            )

            # Add to cache
            self._cache[key] = entry
            self._current_memory += size

            # Evict if necessary
            await self._evict_if_needed()

    async def _evict_if_needed(self) -> None:
        """Evict entries if cache is full."""
        # Evict by count
        while len(self._cache) > self.max_size:
            key, entry = self._cache.popitem(last=False)
            self._current_memory -= entry.size
            logger.debug("Evicted %s (size limit)", key)

        # Evict by memory
        while self._current_memory > self.max_memory:
            if not self._cache:
                break
            key, entry = self._cache.popitem(last=False)
            self._current_memory -= entry.size
            logger.debug("Evicted %s (memory limit)", key)

    async def clear(self) -> None:
        """Clear the cache."""
        async with self._lock:
            self._cache.clear()
            self._current_memory = 0
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "memory": self._current_memory,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }


class FileCache:
    """File-based cache for persistent storage."""

    def __init__(self, cache_dir: str | Path, ttl: int = 3600) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl  # Time to live in seconds
        self._index_file = self.cache_dir / ".cache_index.json"
        self._index: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def _load_index(self) -> None:
        """Load cache index from disk."""
        if self._index_file.exists():
            try:
                async with aiofiles.open(self._index_file) as f:
                    content = await f.read()
                    self._index = json.loads(content)
            except Exception as e:
                logger.error("Failed to load cache index: %s", e)
                self._index = {}

    async def _save_index(self) -> None:
        """Save cache index to disk."""
        try:
            async with aiofiles.open(self._index_file, "w") as f:
                await f.write(json.dumps(self._index, indent=2))
        except (OSError, json.JSONEncodeError) as e:
            logger.error("Failed to save cache index: %s", e)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        # Use hash to avoid filesystem issues
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash[:2]}" / f"{key_hash}.cache"

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            # Check index
            if key not in self._index:
                return None

            entry = self._index[key]

            # Check TTL
            if time.time() - entry["created_at"] > self.ttl:
                # Expired
                await self._remove_entry(key)
                return None

            # Load from file
            cache_path = self._get_cache_path(key)
            if not await aiofiles.os.path.exists(cache_path):
                # File missing
                del self._index[key]
                return None

            try:
                async with aiofiles.open(cache_path, "rb") as f:
                    data = await f.read()
                    return pickle.loads(data)
            except Exception as e:
                logger.error("Failed to load cache entry %s: %s", key, e)
                await self._remove_entry(key)
                return None

    async def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        async with self._lock:
            # Serialize value
            data = pickle.dumps(value)

            # Create cache file
            cache_path = self._get_cache_path(key)
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                async with aiofiles.open(cache_path, "wb") as f:
                    await f.write(data)

                # Update index
                self._index[key] = {
                    "created_at": time.time(),
                    "size": len(data),
                    "path": str(cache_path),
                }

                await self._save_index()

            except Exception as e:
                logger.error("Failed to save cache entry %s: %s", key, e)
                if key in self._index:
                    del self._index[key]

    async def _remove_entry(self, key: str) -> None:
        """Remove cache entry."""
        if key in self._index:
            entry = self._index[key]
            cache_path = Path(entry["path"])

            try:
                if await aiofiles.os.path.exists(cache_path):
                    await aiofiles.os.remove(cache_path)
            except Exception as e:
                logger.error("Failed to remove cache file: %s", e)

            del self._index[key]

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            for key in list(self._index.keys()):
                await self._remove_entry(key)
            self._index.clear()
            await self._save_index()

    async def cleanup(self) -> None:
        """Remove expired entries."""
        async with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, entry in self._index.items():
                if current_time - entry["created_at"] > self.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                await self._remove_entry(key)

            if expired_keys:
                await self._save_index()
                logger.info("Cleaned up %s expired cache entries", len(expired_keys))


def file_hash(file_path: str | Path) -> str:
    """Calculate file hash for cache key."""
    path = Path(file_path)

    # Include file stats in hash
    stat = path.stat()
    hash_data = f"{path}:{stat.st_size}:{stat.st_mtime}".encode()

    # Add file content sample
    with path.open("rb") as f:
        # Read first and last 1KB
        hash_data += f.read(1024)
        if stat.st_size > 2048:
            f.seek(-1024, 2)
            hash_data += f.read(1024)

    return hashlib.sha256(hash_data).hexdigest()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = {"args": args, "kwargs": kwargs}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_str.encode()).hexdigest()


# Decorators for caching


def cached(cache: LRUCache | FileCache, key_func: Callable | None = None):
    """Decorator for caching function results."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = cache_key(func.__name__, *args, **kwargs)

            # Check cache
            result = await cache.get(key)
            if result is not None:
                logger.debug("Cache hit for %s", func.__name__)
                return result

            # Call function
            logger.debug("Cache miss for %s", func.__name__)
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.put(key, result)

            return result

        # Non-async version
        def sync_wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(wrapper(*args, **kwargs))

        return wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Global caches
_ast_cache = LRUCache(max_size=500)
_validation_cache = LRUCache(max_size=1000)


async def get_ast_cache() -> LRUCache:
    """Get global AST cache."""
    return _ast_cache


async def get_validation_cache() -> LRUCache:
    """Get global validation cache."""
    return _validation_cache
