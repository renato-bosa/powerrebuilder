"""Resource extraction manager for PowerBuilder files.

This module provides a centralized manager for resource extraction that:
- Coordinates extraction across multiple files
- Provides better progress tracking
- Handles resource deduplication across the entire extraction
- Generates comprehensive reports
"""

import contextlib
import hashlib
import json
import logging
import pickle
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.extract.pbd.resources import UnifiedResourceExtractor

logger = logging.getLogger(__name__)


class ResourceExtractionManager:
    """Manages resource extraction across multiple PowerBuilder files."""

    def __init__(self, base_output_dir: Path) -> None:
        """Initialize the resource extraction manager.

        Args:
            base_output_dir: Base directory for all output
        """
        self.base_output_dir = base_output_dir
        self.resources_dir = base_output_dir / "resources"
        self.resources_dir.mkdir(parents=True, exist_ok=True)

        # Initialize unified extractor
        self.extractor = UnifiedResourceExtractor(self.resources_dir)

        # Global tracking
        self.all_resources: list[dict[str, Any]] = []
        self.resource_hashes: set[str] = set()
        self.source_file_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.duplicate_count = 0

        # Enhanced statistics
        self.stats = {
            "total_files_processed": 0,
            "files_with_resources": 0,
            "total_resources": 0,
            "unique_resources": 0,
            "duplicate_resources": 0,
            "resource_types": defaultdict(int),
            "resource_categories": defaultdict(int),
            "total_size": 0,
            "size_by_type": defaultdict(int),
            "size_by_category": defaultdict(int),
            "extraction_errors": 0,
        }

        # Caching infrastructure
        self.cache_dir = base_output_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_enabled = True
        self.cache_max_age = 3600 * 24  # 24 hours in seconds
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "evictions": 0,
        }

        # Resource management
        self.resource_registry: dict[
            str, dict[str, Any]
        ] = {}  # hash -> resource metadata
        self.resource_references: dict[str, int] = defaultdict(
            int
        )  # hash -> reference count
        # hash -> last access time
        self.resource_access_times: dict[str, float] = {}
        self.max_memory_usage = 500 * 1024 * 1024  # 500MB max memory usage
        self.current_memory_usage = 0

        # Load existing cache index if available
        self._load_cache_index()

    def extract_from_object(
        self, data: bytes, source_file: str, object_name: str, object_type: str
    ) -> list[dict[str, Any]]:
        """Extract resources from a PowerBuilder object.

        Args:
            data: Object data bytes
            source_file: Source PBL/PBD file name
            object_name: Name of the object
            object_type: Type of the object

        Returns:
            List of extracted resources
        """
        try:
            # Track file processing
            if source_file not in self.source_file_map:
                self.stats["total_files_processed"] += 1

            # Extract resources
            resources = self.extractor.extract_resources_from_data(
                data,
                object_name,
                object_type,
            )

            if resources:
                self.stats["files_with_resources"] += 1

            # Process each resource
            for resource in resources:
                # Add source file info
                resource["source_file"] = source_file

                # Check for duplicates globally
                if resource["hash"] in self.resource_hashes:
                    self.duplicate_count += 1
                    self.stats["duplicate_resources"] += 1
                    resource["is_duplicate"] = True
                else:
                    self.resource_hashes.add(resource["hash"])
                    self.stats["unique_resources"] += 1
                    resource["is_duplicate"] = False

                # Update statistics
                self.stats["total_resources"] += 1
                self.stats["resource_types"][resource["type"]] += 1

                category = self.extractor._get_resource_category(resource["type"])
                self.stats["resource_categories"][category] += 1
                self.stats["size_by_type"][resource["type"]] += resource["size"]
                self.stats["size_by_category"][category] += resource["size"]

                # Track by source file
                self.source_file_map[source_file].append(resource)
                self.all_resources.append(resource)

            return resources

        except Exception as e:
            logger.error("Failed to extract resources from %s: %s", object_name, e)
            self.stats["extraction_errors"] += 1
            return []

    def extract_from_object_cached(
        self, data: bytes, source_file: str, object_name: str, object_type: str
    ) -> list[dict[str, Any]]:
        """Extract resources with caching support.

        Args:
            data: Object data bytes
            source_file: Source PBL/PBD file name
            object_name: Name of the object
            object_type: Type of the object

        Returns:
            List of extracted resources
        """
        if not self.cache_enabled:
            return self.extract_from_object(data, source_file, object_name, object_type)

        # Generate cache key based on data hash and object metadata
        cache_key = self._generate_cache_key(
            data, source_file, object_name, object_type
        )

        # Try to load from cache
        cached_resources = self._load_from_cache(cache_key)
        if cached_resources is not None:
            self.cache_stats["hits"] += 1
            logger.debug("Cache hit for %s in %s", object_name, source_file)
            return cached_resources

        # Cache miss - perform extraction
        self.cache_stats["misses"] += 1
        resources = self.extract_from_object(
            data, source_file, object_name, object_type
        )

        # Cache the results
        if resources:
            self._save_to_cache(cache_key, resources)

        return resources

    def register_resource(self, resource_hash: str, metadata: dict[str, Any]) -> None:
        """Register a resource in the resource registry.

        Args:
            resource_hash: Unique hash of the resource
            metadata: Resource metadata
        """
        self.resource_registry[resource_hash] = {
            **metadata,
            "registered_at": time.time(),
            "last_accessed": time.time(),
        }
        self.resource_references[resource_hash] = 1
        self.resource_access_times[resource_hash] = time.time()

        # Update memory usage estimate
        size = metadata.get("size", 0)
        self.current_memory_usage += size

        # Check if memory cleanup is needed
        if self.current_memory_usage > self.max_memory_usage:
            self._cleanup_resources()

    def get_resource(self, resource_hash: str) -> dict[str, Any] | None:
        """Get resource metadata by hash.

        Args:
            resource_hash: Resource hash

        Returns:
            Resource metadata or None if not found
        """
        if resource_hash in self.resource_registry:
            # Update access time
            self.resource_access_times[resource_hash] = time.time()
            self.resource_registry[resource_hash]["last_accessed"] = time.time()
            return self.resource_registry[resource_hash]
        return None

    def reference_resource(self, resource_hash: str) -> None:
        """Increment reference count for a resource.

        Args:
            resource_hash: Resource hash
        """
        if resource_hash in self.resource_references:
            self.resource_references[resource_hash] += 1
            self.resource_access_times[resource_hash] = time.time()

    def dereference_resource(self, resource_hash: str) -> None:
        """Decrement reference count for a resource.

        Args:
            resource_hash: Resource hash
        """
        if resource_hash in self.resource_references:
            self.resource_references[resource_hash] -= 1
            if self.resource_references[resource_hash] <= 0:
                self._remove_resource(resource_hash)

    def cleanup_cache(self, max_age_seconds: int | None = None) -> int:
        """Clean up old cache entries.

        Args:
            max_age_seconds: Maximum age in seconds (defaults to cache_max_age)

        Returns:
            Number of entries removed
        """
        max_age = max_age_seconds or self.cache_max_age
        current_time = time.time()
        removed_count = 0

        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                stat = cache_file.stat()
                if current_time - stat.st_mtime > max_age:
                    cache_file.unlink()
                    removed_count += 1
                    self.cache_stats["evictions"] += 1
            except Exception as e:
                logger.warning("Failed to remove cache file %s: %s", cache_file, e)

        logger.info("Cleaned up %s old cache entries", removed_count)
        return removed_count

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary of cache statistics
        """
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        cache_files = list(self.cache_dir.glob("*.cache"))
        cache_size = sum(f.stat().st_size for f in cache_files if f.exists())

        return {
            "enabled": self.cache_enabled,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "cache_files": len(cache_files),
            "cache_size_bytes": cache_size,
            "cache_size_mb": round(cache_size / 1024 / 1024, 2),
            **self.cache_stats,
        }

    def get_resource_statistics(self) -> dict[str, Any]:
        """Get resource management statistics.

        Returns:
            Dictionary of resource statistics
        """
        total_resources = len(self.resource_registry)
        total_references = sum(self.resource_references.values())

        # Find most referenced resources
        most_referenced = sorted(
            self.resource_references.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Find recently accessed resources
        recently_accessed = sorted(
            self.resource_access_times.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_resources_managed": total_resources,
            "total_references": total_references,
            "current_memory_usage_bytes": self.current_memory_usage,
            "current_memory_usage_mb": round(
                self.current_memory_usage / 1024 / 1024, 2
            ),
            "max_memory_usage_mb": round(self.max_memory_usage / 1024 / 1024, 2),
            "most_referenced": [(hash[:16], count) for hash, count in most_referenced],
            "recently_accessed": [
                (hash[:16], time.ctime(access_time))
                for hash, access_time in recently_accessed
            ],
        }

    def _generate_cache_key(
        self, data: bytes, source_file: str, object_name: str, object_type: str
    ) -> str:
        """Generate a cache key for the given parameters."""
        # Re-use imported hashlib from top of file

        # Create a hash from the data and metadata
        hasher = hashlib.sha256()
        hasher.update(data)
        hasher.update(source_file.encode())
        hasher.update(object_name.encode())
        hasher.update(object_type.encode())

        return hasher.hexdigest()[:16]  # Use first 16 chars for filename

    def _load_from_cache(self, cache_key: str) -> list[dict[str, Any]] | None:
        """Load resources from cache."""
        cache_file = self.cache_dir / f"{cache_key}.cache"

        if not cache_file.exists():
            return None

        try:
            # Check if cache is too old
            stat = cache_file.stat()
            if time.time() - stat.st_mtime > self.cache_max_age:
                cache_file.unlink()  # Remove expired cache
                return None

            with Path(cache_file).open("rb") as f:
                return pickle.load(f)

        except Exception as e:
            logger.warning("Failed to load cache %s: %s", cache_key, e)
            # Remove corrupted cache file
            with contextlib.suppress(Exception):
                cache_file.unlink()
            return None

    def _save_to_cache(self, cache_key: str, resources: list[dict[str, Any]]) -> None:
        """Save resources to cache."""
        cache_file = self.cache_dir / f"{cache_key}.cache"

        try:
            with Path(cache_file).open("wb") as f:
                pickle.dump(resources, f, protocol=pickle.HIGHEST_PROTOCOL)

            self.cache_stats["writes"] += 1

        except Exception as e:
            logger.warning("Failed to save cache %s: %s", cache_key, e)

    def _load_cache_index(self) -> None:
        """Load cache index from disk."""
        index_file = self.cache_dir / "cache_index.json"

        if index_file.exists():
            try:
                with Path(index_file).open() as f:
                    data = json.load(f)
                self.cache_stats.update(data.get("stats", {}))
                logger.debug("Loaded cache index")
            except Exception as e:
                logger.warning("Failed to load cache index: %s", e)

    def _save_cache_index(self) -> None:
        """Save cache index to disk."""
        index_file = self.cache_dir / "cache_index.json"

        try:
            index_data = {
                "stats": self.cache_stats,
                "saved_at": time.time(),
            }

            with Path(index_file).open("w") as f:
                json.dump(index_data, f, indent=2)

        except Exception as e:
            logger.warning("Failed to save cache index: %s", e)

    def _cleanup_resources(self) -> None:
        """Clean up resources to free memory."""
        logger.info("Performing resource cleanup to free memory")

        # Sort by access time (oldest first) and low reference count
        candidates = []
        for resource_hash in self.resource_registry:
            access_time = self.resource_access_times.get(resource_hash, 0)
            ref_count = self.resource_references.get(resource_hash, 0)
            size = self.resource_registry[resource_hash].get("size", 0)

            # Score for cleanup (higher score = better candidate for removal)
            score = (time.time() - access_time) / max(ref_count, 1) * size
            candidates.append((resource_hash, score))

        # Sort by score (highest first) and remove resources
        candidates.sort(key=lambda x: x[1], reverse=True)

        target_reduction = self.current_memory_usage - (
            self.max_memory_usage * 0.8
        )  # Reduce to 80% of max
        freed_memory = 0
        removed_count = 0

        for resource_hash, _ in candidates:
            if freed_memory >= target_reduction:
                break

            size = self.resource_registry[resource_hash].get("size", 0)
            self._remove_resource(resource_hash)
            freed_memory += size
            removed_count += 1

        logger.info(
            "Cleaned up %s resources, freed %.2f MB",
            removed_count,
            freed_memory / 1024 / 1024,
        )

    def _remove_resource(self, resource_hash: str) -> None:
        """Remove a resource from the registry."""
        if resource_hash in self.resource_registry:
            size = self.resource_registry[resource_hash].get("size", 0)
            self.current_memory_usage -= size

        del self.resource_registry[resource_hash]
        del self.resource_references[resource_hash]
        del self.resource_access_times[resource_hash]

    def generate_comprehensive_report(self) -> None:
        """Generate comprehensive extraction report and manifests."""
        # Update total size
        self.stats["total_size"] = self.extractor.stats["total_size"]

        # Generate main manifest
        self._generate_main_manifest()

        # Generate detailed resource catalog
        self._generate_detailed_catalog()

        # Generate source file report
        self._generate_source_file_report()

        # Generate statistics report
        self._generate_statistics_report()

        # Generate caching and resource management reports
        self._generate_cache_report()
        self._generate_resource_management_report()

        # Let the extractor generate its own reports
        self.extractor.generate_manifest()

        # Save cache index for future sessions
        self._save_cache_index()

        logger.info(
            "Resource extraction complete: %s total resources "
            "(%s unique, %s duplicates) "
            "from %s files",
            self.stats["total_resources"],
            self.stats["unique_resources"],
            self.stats["duplicate_resources"],
            self.stats["total_files_processed"],
        )

    def _generate_main_manifest(self) -> None:
        """Generate the main resource manifest."""
        manifest_path = self.resources_dir / "extraction_manifest.json"

        manifest = {
            "extraction_summary": {
                "total_files_processed": self.stats["total_files_processed"],
                "files_with_resources": self.stats["files_with_resources"],
                "total_resources_found": self.stats["total_resources"],
                "unique_resources": self.stats["unique_resources"],
                "duplicate_resources": self.stats["duplicate_resources"],
                "total_size_bytes": self.stats["total_size"],
                "extraction_errors": self.stats["extraction_errors"],
            },
            "resource_types": dict(self.stats["resource_types"]),
            "resource_categories": dict(self.stats["resource_categories"]),
            "size_by_type": dict(self.stats["size_by_type"]),
            "size_by_category": dict(self.stats["size_by_category"]),
        }

        with Path(manifest_path).open("w") as f:
            json.dump(manifest, f, indent=2)

    def _generate_detailed_catalog(self) -> None:
        """Generate detailed resource catalog."""
        catalog_path = self.resources_dir / "detailed_resource_catalog.json"

        # Group resources by various criteria
        by_type = defaultdict(list)
        by_category = defaultdict(list)
        by_source = defaultdict(list)

        for resource in self.all_resources:
            # Simplified resource info for catalog
            resource_info = {
                "id": resource["id"],
                "type": resource["type"],
                "size": resource["size"],
                "source_object": resource["source_object"],
                "source_file": resource.get("source_file", "unknown"),
                "path": resource["path"],
                "is_duplicate": resource.get("is_duplicate", False),
                "metadata": resource.get("metadata", {}),
            }

            by_type[resource["type"]].append(resource_info)
            category = self.extractor._get_resource_category(resource["type"])
            by_category[category].append(resource_info)
            by_source[resource.get("source_file", "unknown")].append(resource_info)

        catalog = {
            "by_type": dict(by_type),
            "by_category": dict(by_category),
            "by_source": dict(by_source),
        }

        with Path(catalog_path).open("w") as f:
            json.dump(catalog, f, indent=2)

    def _generate_source_file_report(self) -> None:
        """Generate report grouped by source files."""
        report_path = self.resources_dir / "source_file_report.txt"

        with report_path.open("w") as f:
            f.write("PowerBuilder Resource Extraction - Source File Report\n")
            f.write("=" * 70 + "\n\n")

            for source_file, resources in sorted(self.source_file_map.items()):
                f.write(f"Source File: {source_file}\n")
                f.write(f"Resources Found: {len(resources)}\n")

                # Group by type
                type_counts = defaultdict(int)
                total_size = 0
                for resource in resources:
                    type_counts[resource["type"]] += 1
                    total_size += resource["size"]

                f.write(f"Total Size: {total_size:,} bytes\n")
                f.write("Resource Types:\n")
                for res_type, count in sorted(type_counts.items()):
                    f.write(f"  - {res_type}: {count}\n")
                f.write("\n")

    def _generate_statistics_report(self) -> None:
        """Generate detailed statistics report."""
        report_path = self.resources_dir / "extraction_statistics.txt"

        with report_path.open("w") as f:
            f.write("PowerBuilder Resource Extraction - Statistics Report\n")
            f.write("=" * 70 + "\n\n")

            f.write("Overall Statistics:\n")
            f.write(f"  Total Files Processed: {self.stats['total_files_processed']}\n")
            f.write(f"  Files with Resources: {self.stats['files_with_resources']}\n")
            f.write(f"  Total Resources Found: {self.stats['total_resources']}\n")
            f.write(f"  Unique Resources: {self.stats['unique_resources']}\n")
            f.write(f"  Duplicate Resources: {self.stats['duplicate_resources']}\n")
            f.write(
                f"  Total Size: {self.stats['total_size']:,} bytes ({self.stats['total_size'] / 1024 / 1024:.2f} MB)\n"
            )
            f.write(f"  Extraction Errors: {self.stats['extraction_errors']}\n\n")

            f.write("Resources by Category:\n")
            for category, count in sorted(self.stats["resource_categories"].items()):
                size = self.stats["size_by_category"][category]
                f.write(f"  {category}: {count} resources ({size:,} bytes)\n")

            f.write("\nResources by Type:\n")
            for res_type, count in sorted(self.stats["resource_types"].items()):
                size = self.stats["size_by_type"][res_type]
                f.write(f"  {res_type}: {count} resources ({size:,} bytes)\n")

            if self.stats["extraction_errors"] > 0:
                f.write(
                    f"\nWarning: {self.stats['extraction_errors']} extraction errors occurred.\n"
                )
                f.write("Check the log files for details.\n")

    def _generate_cache_report(self) -> None:
        """Generate cache performance report."""
        report_path = self.resources_dir / "cache_performance.txt"
        cache_stats = self.get_cache_statistics()

        with report_path.open("w") as f:
            f.write("PowerBuilder Resource Extraction - Cache Performance Report\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Cache Enabled: {cache_stats['enabled']}\n")
            f.write(f"Hit Rate: {cache_stats['hit_rate_percent']:.2f}%\n")
            f.write(f"Total Requests: {cache_stats['total_requests']}\n")
            f.write(f"Cache Hits: {cache_stats['hits']}\n")
            f.write(f"Cache Misses: {cache_stats['misses']}\n")
            f.write(f"Cache Writes: {cache_stats['writes']}\n")
            f.write(f"Cache Evictions: {cache_stats['evictions']}\n")
            f.write(f"Cache Files: {cache_stats['cache_files']}\n")
            f.write(f"Cache Size: {cache_stats['cache_size_mb']:.2f} MB\n\n")

            # Performance recommendations
            f.write("Performance Recommendations:\n")
            if cache_stats["hit_rate_percent"] < 50:
                f.write(
                    "- Low cache hit rate. Consider increasing cache retention time.\n"
                )
            if cache_stats["cache_size_mb"] > 100:
                f.write("- Large cache size. Consider periodic cleanup.\n")
            if cache_stats["evictions"] > cache_stats["writes"] * 0.1:
                f.write("- High eviction rate. Consider increasing cache storage.\n")

    def _generate_resource_management_report(self) -> None:
        """Generate resource management report."""
        report_path = self.resources_dir / "resource_management.txt"
        resource_stats = self.get_resource_statistics()

        with report_path.open("w") as f:
            f.write("PowerBuilder Resource Extraction - Resource Management Report\n")
            f.write("=" * 70 + "\n\n")

            f.write("Resource Registry Statistics:\n")
            f.write(
                f"  Total Resources Managed: {resource_stats['total_resources_managed']}\n"
            )
            f.write(f"  Total References: {resource_stats['total_references']}\n")
            f.write(
                f"  Current Memory Usage: {resource_stats['current_memory_usage_mb']:.2f} MB\n"
            )
            f.write(
                f"  Maximum Memory Limit: {resource_stats['max_memory_usage_mb']:.2f} MB\n"
            )

            memory_usage_percent = (
                resource_stats["current_memory_usage_mb"]
                / resource_stats["max_memory_usage_mb"]
                * 100
            )
            f.write(f"  Memory Usage: {memory_usage_percent:.1f}% of limit\n\n")

            f.write("Most Referenced Resources:\n")
            for hash_prefix, count in resource_stats["most_referenced"][:5]:
                f.write(f"  {hash_prefix}... : {count} references\n")

            f.write("\nRecently Accessed Resources:\n")
            for hash_prefix, access_time in resource_stats["recently_accessed"][:5]:
                f.write(f"  {hash_prefix}... : {access_time}\n")

            f.write("\nMemory Management:\n")
            if memory_usage_percent > 80:
                f.write("- High memory usage. Resource cleanup may be triggered.\n")
            elif memory_usage_percent < 20:
                f.write("- Low memory usage. Good resource efficiency.\n")
            else:
                f.write("- Normal memory usage levels.\n")

    def cleanup(self) -> None:
        """Cleanup resources and save state before shutdown."""
        logger.info("Cleaning up resource extraction manager")

        # Save cache index
        self._save_cache_index()

        # Optional: Clean up old cache files
        removed = self.cleanup_cache()
        if removed > 0:
            logger.info("Cleaned up %s old cache entries during shutdown", removed)

        # Clear in-memory resources
        self.resource_registry.clear()
        self.resource_references.clear()
        self.resource_access_times.clear()
        self.current_memory_usage = 0

        logger.info("Resource extraction manager cleanup complete")
