"""Resource catalog for tracking extracted PowerBuilder resources.

This module provides a comprehensive catalog system for managing and tracking
all extracted resources (images, strings, binary data) and their relationships.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

logger = logging.getLogger(__name__)


class ResourceCatalog:
    """Manages a catalog of extracted resources and their relationships."""

    def __init__(self, catalog_path: Path | None = None) -> None:


        """Initialize the resource catalog.

        Args:
            catalog_path: Optional path to save/load catalog data
        """
        self.catalog_path = catalog_path

        # Resource collections
        self.resources: dict[str, dict[str, Any]] = {
            "images": {}, "strings": {}, "binary": {}, "pcode": {}, "datawindows": {}, "other": {},
        }

        # Cross-references
        self.resource_usage: dict[str, set[str]] = defaultdict(set)  # resource_id -> set of object_ids
        self.object_resources: dict[str, set[str]] = defaultdict(set)  # object_id -> set of resource_ids

        # Metadata
        self.metadata = {
            "created": datetime.now().isoformat(), "last_updated": datetime.now().isoformat(), "version": "1.0", "statistics": {},
        }
        
        # Indexing structures for fast lookups
        self.indexes = {
            "by_size": defaultdict(list),      # size -> [resource_ids]
            "by_format": defaultdict(list),    # format -> [resource_ids]
            "by_source": defaultdict(list),    # source_file -> [resource_ids]
            "by_content_hash": {},             # content_hash -> resource_id
            "string_content": {},              # string_value -> resource_id
            "large_resources": set(),          # resource_ids of large resources (>1MB)
            "recent_resources": [],            # recently added resources (last 100)
        }

        # Load existing catalog if path provided
        if catalog_path and catalog_path.exists():
            self.load_catalog()

    def add_image_resource(self, source_file: str, image_data: dict[str, Any]) -> str:




        """Add an image resource to the catalog.

        Args:
            source_file: Source file path
            image_data: Image information dictionary

        Returns:
            Resource ID
        """
        # Generate resource ID
        resource_id = self._generate_resource_id("IMG", source_file, image_data.get("offset", 0))

        # Store resource
        self.resources["images"][resource_id] = {
            "id": resource_id, "source_file": source_file, "format": image_data.get("format"), "size": image_data.get("size"), "offset": image_data.get("offset"), "metadata": image_data.get("metadata", {}), "saved_path": image_data.get("saved_path"), "added": datetime.now().isoformat(),
        }

        # Update cross-references and indexes
        self._add_cross_reference(resource_id, source_file)
        self._update_indexes(resource_id, "images", self.resources["images"][resource_id])

        return resource_id

    def add_string_resource(self, source_file: str, string_value: str, context: str | None = None) -> str:




        """Add a string resource to the catalog.

        Args:
            source_file: Source file path
            string_value: String value
            context: Optional context (property name, etc.)

        Returns:
            Resource ID
        """
        # Generate resource ID based on content hash
        resource_id = self._generate_string_id(string_value)

        # Check if string already exists
        is_new_resource = resource_id not in self.resources["strings"]
        
        if not is_new_resource:
            # Update sources
            existing = self.resources["strings"][resource_id]
            if source_file not in existing["sources"]:
                existing["sources"].append(source_file)
                existing["occurrences"] += 1
        else:
            # Store new string resource
            self.resources["strings"][resource_id] = {
                "id": resource_id, "value": string_value, "sources": [source_file], "contexts": [context] if context else [], "length": len(string_value), "occurrences": 1, "added": datetime.now().isoformat(),
            }

        # Update cross-references and indexes
        self._add_cross_reference(resource_id, source_file)
        if is_new_resource:
            # Only update indexes for new strings
            self._update_indexes(resource_id, "strings", self.resources["strings"][resource_id])

        return resource_id

    def add_binary_resource(self, source_file: str, resource_type: str, data_info: dict[str, Any]) -> str:




        """Add a binary resource to the catalog.

        Args:
            source_file: Source file path
            resource_type: Type of binary resource
            data_info: Resource information

        Returns:
            Resource ID
        """
        # Generate resource ID
        resource_id = self._generate_resource_id("BIN", source_file, data_info.get("offset", 0))

        # Store resource
        self.resources["binary"][resource_id] = {
            "id": resource_id, "source_file": source_file, "resource_type": resource_type, "size": data_info.get("size"), "offset": data_info.get("offset"), "saved_path": data_info.get("saved_path"), "metadata": data_info.get("metadata", {}), "added": datetime.now().isoformat(),
        }

        # Update cross-references and indexes
        self._add_cross_reference(resource_id, source_file)
        self._update_indexes(resource_id, "binary", self.resources["binary"][resource_id])

        return resource_id

    def find_resource_usage(self, resource_id: str) -> list[str]:




        """Find all objects that use a specific resource.

        Args:
            resource_id: Resource identifier

        Returns:
            List of object paths that use this resource
        """
        return list(self.resource_usage.get(resource_id, set()))

    def find_object_resources(self, object_path: str) -> dict[str, list[str]]:




        """Find all resources used by a specific object.

        Args:
            object_path: Object file path

        Returns:
            Dictionary of resource types to resource IDs
        """
        resource_ids = self.object_resources.get(object_path, set())

        resources_by_type = defaultdict(list)
        for resource_id in resource_ids:
            resource_type = self._get_resource_type(resource_id)
            if resource_type:
                resources_by_type[resource_type].append(resource_id)

        return dict(resources_by_type)

    def find_common_resources(self, min_usage: int = 2) -> dict[str, list[str]]:




        """Find resources used by multiple objects.

        Args:
            min_usage: Minimum number of objects using the resource

        Returns:
            Dictionary of resource IDs to list of objects using them
        """
        common_resources = {}

        for resource_id, objects in self.resource_usage.items():
            if len(objects) >= min_usage:
                common_resources[resource_id] = list(objects)

        return common_resources

    def find_duplicate_strings(self) -> dict[str, list[dict[str, Any]]]:




        """Find duplicate strings across different sources.

        Returns:
            Dictionary of strings that appear in multiple sources
        """
        duplicates = {}

        for resource_id, string_data in self.resources["strings"].items():
            if string_data["occurrences"] > 1:
                duplicates[string_data["value"]] = {
                    "sources": string_data["sources"], "occurrences": string_data["occurrences"], "contexts": string_data.get("contexts", []),
                }

        return duplicates

    def generate_statistics(self) -> dict[str, Any]:




        """Generate catalog statistics.

        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_resources": sum(len(r) for r in self.resources.values()), "resource_counts": {}, "total_size": 0, "unique_objects": len(self.object_resources), "common_resources": len(self.find_common_resources()), "duplicate_strings": len(self.find_duplicate_strings()),
        }

        # Count by type and calculate sizes
        for resource_type, resources in self.resources.items():
            stats["resource_counts"][resource_type] = len(resources)

            # Calculate total size
            for resource in resources.values():
                if "size" in resource and resource["size"]:
                    stats["total_size"] += resource["size"]

        # String statistics
        if self.resources["strings"]:
            string_lengths = [r["length"] for r in self.resources["strings"].values()]
            stats["string_statistics"] = {
                "total": len(string_lengths), "min_length": min(string_lengths), "max_length": max(string_lengths), "avg_length": sum(string_lengths) / len(string_lengths),
            }

        # Image statistics
        if self.resources["images"]:
            format_counts = defaultdict(int)
            for img in self.resources["images"].values():
                format_counts[img["format"]] += 1
            stats["image_formats"] = dict(format_counts)

        self.metadata["statistics"] = stats
        return stats

    def export_summary(self, output_path: Path) -> None:




        """Export a human-readable summary of the catalog.

        Args:
            output_path: Path to write summary
        """
        summary = []
        summary.append("PowerBuilder Resource Catalog Summary")
        summary.append("=" * 50)
        summary.append(f"Generated: {datetime.now().isoformat()}")
        summary.append("")

        # Statistics
        stats = self.generate_statistics()
        summary.append("STATISTICS:")
        summary.append(f"  Total Resources: {stats["total_resources"]:, }")
        summary.append(f"  Total Size: {stats["total_size"]:, } bytes")
        summary.append(f"  Unique Objects: {stats["unique_objects"]}")
        summary.append("")

        summary.append("RESOURCE COUNTS:")
        for rtype, count in stats["resource_counts"].items():
            summary.append(f"  {rtype.title()}: {count:, }")
        summary.append("")

        # Common resources
        summary.append("COMMON RESOURCES (used by 3+ objects):")
        common = self.find_common_resources(min_usage=3)
        for resource_id, objects in sorted(common.items())[:
            10]:
            resource = self._find_resource(resource_id)
            if resource:
                summary.append(f"  {resource_id}: Used by {len(objects)} objects")
                if "value" in resource:  # String resource
                    summary.append(f"    Value: {resource["value"][:50]}...")
        summary.append("")

        # Duplicate strings
        summary.append("TOP DUPLICATE STRINGS:")
        duplicates = self.find_duplicate_strings()
        for string, info in sorted(duplicates.items(), key=lambda x:
            x[1]["occurrences"], reverse=True,)[:10]:
            summary.append(f"  '{string[:50]}...' - {info["occurrences"]} occurrences")

        # Write summary
        output_path.write_text("\n".join(summary))
        logger.info("Exported catalog summary to %s", output_path)

    def search_resources(self, query: str, resource_type: str | None = None, case_sensitive: bool = False) -> list[dict[str, Any]]:
        """Search resources by content, filename, or metadata.
        
        Args:
            query: Search query string
            resource_type: Optional filter by resource type
            case_sensitive: Whether search is case sensitive
            
        Returns:
            List of matching resources
        """
        results = []
        search_query = query if case_sensitive else query.lower()
        
        # Search through all resource types or specific type
        resource_types = [resource_type] if resource_type else self.resources.keys()
        
        for rtype in resource_types:
            for resource_id, resource_data in self.resources[rtype].items():
                if self._matches_search_query(resource_data, search_query, case_sensitive):
                    results.append({
                        "resource_id": resource_id,
                        "resource_type": rtype,
                        "data": resource_data,
                        "usage_count": len(self.resource_usage.get(resource_id, []))
                    })
        
        # Sort by relevance (usage count)
        results.sort(key=lambda x: x["usage_count"], reverse=True)
        return results

    def find_resources_by_size(self, min_size: int | None = None, max_size: int | None = None) -> list[dict[str, Any]]:
        """Find resources within a size range.
        
        Args:
            min_size: Minimum size in bytes
            max_size: Maximum size in bytes
            
        Returns:
            List of matching resources
        """
        results = []
        
        for resource_type, resources in self.resources.items():
            for resource_id, resource_data in resources.items():
                size = resource_data.get("size")
                if size is not None:
                    if (min_size is None or size >= min_size) and (max_size is None or size <= max_size):
                        results.append({
                            "resource_id": resource_id,
                            "resource_type": resource_type,
                            "size": size,
                            "data": resource_data
                        })
        
        # Sort by size (largest first)
        results.sort(key=lambda x: x["size"], reverse=True)
        return results

    def find_resources_by_format(self, format_type: str) -> list[dict[str, Any]]:
        """Find resources by format type.
        
        Args:
            format_type: Format to search for (e.g., 'PNG', 'JPEG', 'ICO')
            
        Returns:
            List of matching resources
        """
        # Use index if available
        if format_type in self.indexes["by_format"]:
            resource_ids = self.indexes["by_format"][format_type]
        else:
            # Fallback to full search
            resource_ids = []
            for resources in self.resources.values():
                for resource_id, resource_data in resources.items():
                    if resource_data.get("format") == format_type:
                        resource_ids.append(resource_id)
        
        results = []
        for resource_id in resource_ids:
            resource_data = self._find_resource(resource_id)
            if resource_data:
                results.append({
                    "resource_id": resource_id,
                    "resource_type": self._get_resource_type(resource_id),
                    "data": resource_data
                })
        
        return results

    def find_recent_resources(self, limit: int = 50) -> list[dict[str, Any]]:
        """Find recently added resources.
        
        Args:
            limit: Maximum number of resources to return
            
        Returns:
            List of recent resources
        """
        # Use recent index if available
        if self.indexes["recent_resources"]:
            recent_ids = self.indexes["recent_resources"][-limit:]
        else:
            # Fallback: collect all resources and sort by added time
            all_resources = []
            for resource_type, resources in self.resources.items():
                for resource_id, resource_data in resources.items():
                    all_resources.append((resource_id, resource_type, resource_data.get("added", "")))
            
            # Sort by added time (most recent first)
            all_resources.sort(key=lambda x: x[2], reverse=True)
            recent_ids = [r[0] for r in all_resources[:limit]]
        
        results = []
        for resource_id in recent_ids:
            resource_data = self._find_resource(resource_id)
            if resource_data:
                results.append({
                    "resource_id": resource_id,
                    "resource_type": self._get_resource_type(resource_id),
                    "data": resource_data
                })
        
        return results

    def find_large_resources(self, threshold: int = 1024 * 1024) -> list[dict[str, Any]]:
        """Find resources larger than threshold.
        
        Args:
            threshold: Size threshold in bytes (default 1MB)
            
        Returns:
            List of large resources
        """
        # Update large resources index
        self._update_large_resources_index(threshold)
        
        results = []
        for resource_id in self.indexes["large_resources"]:
            resource_data = self._find_resource(resource_id)
            if resource_data:
                results.append({
                    "resource_id": resource_id,
                    "resource_type": self._get_resource_type(resource_id),
                    "size": resource_data.get("size", 0),
                    "data": resource_data
                })
        
        # Sort by size (largest first)
        results.sort(key=lambda x: x["size"], reverse=True)
        return results

    def rebuild_indexes(self) -> None:
        """Rebuild all indexes from scratch."""
        logger.info("Rebuilding resource catalog indexes...")
        
        # Clear existing indexes
        self.indexes = {
            "by_size": defaultdict(list),
            "by_format": defaultdict(list),
            "by_source": defaultdict(list),
            "by_content_hash": {},
            "string_content": {},
            "large_resources": set(),
            "recent_resources": [],
        }
        
        # Rebuild indexes for all resources
        for resource_type, resources in self.resources.items():
            for resource_id, resource_data in resources.items():
                self._update_indexes(resource_id, resource_type, resource_data)
        
        logger.info(f"Rebuilt indexes for {sum(len(r) for r in self.resources.values())} resources")

    def get_index_statistics(self) -> dict[str, Any]:
        """Get statistics about the indexing system.
        
        Returns:
            Dictionary of index statistics
        """
        return {
            "index_counts": {
                "by_size": len(self.indexes["by_size"]),
                "by_format": len(self.indexes["by_format"]),
                "by_source": len(self.indexes["by_source"]),
                "by_content_hash": len(self.indexes["by_content_hash"]),
                "string_content": len(self.indexes["string_content"]),
                "large_resources": len(self.indexes["large_resources"]),
                "recent_resources": len(self.indexes["recent_resources"]),
            },
            "top_formats": dict(sorted(
                {k: len(v) for k, v in self.indexes["by_format"].items()}.items(),
                key=lambda x: x[1], reverse=True
            )[:10]),
            "top_sources": dict(sorted(
                {k: len(v) for k, v in self.indexes["by_source"].items()}.items(),
                key=lambda x: x[1], reverse=True
            )[:10]),
        }

    def save_catalog(self) -> None:




        """Save catalog to disk."""
        if not self.catalog_path:
            logger.warning("No catalog path set, cannot save")
            return

        try:
            # Update metadata
            self.metadata["last_updated"] = datetime.now().isoformat()
            self.generate_statistics()

            # Prepare data for JSON serialization
            catalog_data = {
                "metadata": self.metadata, "resources": self.resources, "resource_usage": {k: list(v) for k, v in self.resource_usage.items()}, "object_resources": {k: list(v) for k, v in self.object_resources.items()},
            }

            # Save to file
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.catalog_path, "w") as f:
                json.dump(catalog_data, f, indent=2)

            logger.info("Saved resource catalog to %s", self.catalog_path)

        except Exception as e:
            logger.error("Failed to save catalog: %s", e)

    def load_catalog(self) -> None:




        """Load catalog from disk."""
        if not self.catalog_path or not self.catalog_path.exists():
            logger.warning("No catalog file to load")
            return

        try:
            with open(self.catalog_path) as f:
                catalog_data = json.load(f)

            # Restore data
            self.metadata = catalog_data.get("metadata", self.metadata)
            self.resources = catalog_data.get("resources", self.resources)

            # Restore cross-references (convert lists back to sets)
            self.resource_usage = {
                k: set(v) for k, v in catalog_data.get("resource_usage", {}).items()
            }
            self.object_resources = {
                k: set(v) for k, v in catalog_data.get("object_resources", {}).items()
            }

            logger.info("Loaded resource catalog from %s", self.catalog_path)

        except Exception as e:
            logger.error("Failed to load catalog: %s", e)

    def _generate_resource_id(self, prefix: str, source: str, offset: int) -> str:




        """Generate a unique resource ID."""
        source_hash = abs(hash(source)) % 10000
        return f"{prefix}_{source_hash:04d}_{offset:08X}"

    def _generate_string_id(self, string_value: str) -> str:




        """Generate ID for string resource based on content."""
        string_hash = abs(hash(string_value)) % 100000000
        return f"STR_{string_hash:08X}"

    def _add_cross_reference(self, resource_id: str, object_path: str) -> None:




        """Add cross-reference between resource and object."""
        self.resource_usage[resource_id].add(object_path)
        self.object_resources[object_path].add(resource_id)

    def _get_resource_type(self, resource_id: str) -> str | None:




        """Get the type of a resource from its ID."""
        for resource_type, resources in self.resources.items():
            if resource_id in resources:
                return resource_type
        return None

    def _update_indexes(self, resource_id: str, resource_type: str, resource_data: dict[str, Any]) -> None:
        """Update all indexes for a resource."""
        # Update size index
        size = resource_data.get("size")
        if size is not None:
            # Group by size ranges for better indexing
            size_range = self._get_size_range(size)
            self.indexes["by_size"][size_range].append(resource_id)
            
            # Large resources index
            if size > 1024 * 1024:  # 1MB threshold
                self.indexes["large_resources"].add(resource_id)
        
        # Update format index
        format_type = resource_data.get("format")
        if format_type:
            self.indexes["by_format"][format_type].append(resource_id)
        
        # Update source file index
        source_file = resource_data.get("source_file")
        if source_file:
            self.indexes["by_source"][source_file].append(resource_id)
        
        # Update string content index
        if resource_type == "strings" and "value" in resource_data:
            self.indexes["string_content"][resource_data["value"]] = resource_id
        
        # Update recent resources (maintain last 100)
        self.indexes["recent_resources"].append(resource_id)
        if len(self.indexes["recent_resources"]) > 100:
            self.indexes["recent_resources"] = self.indexes["recent_resources"][-100:]

    def _get_size_range(self, size: int) -> str:
        """Get size range category for indexing."""
        if size < 1024:
            return "small"  # < 1KB
        elif size < 1024 * 1024:
            return "medium"  # 1KB - 1MB
        elif size < 10 * 1024 * 1024:
            return "large"  # 1MB - 10MB
        else:
            return "xlarge"  # > 10MB

    def _matches_search_query(self, resource_data: dict[str, Any], query: str, case_sensitive: bool) -> bool:
        """Check if resource matches search query."""
        search_fields = [
            resource_data.get("value", ""),  # String content
            resource_data.get("source_file", ""),  # Source file path
            resource_data.get("saved_path", ""),  # Saved file path
            resource_data.get("format", ""),  # Format type
            resource_data.get("resource_type", ""),  # Resource type
        ]
        
        # Include metadata fields
        metadata = resource_data.get("metadata", {})
        if isinstance(metadata, dict):
            search_fields.extend(str(v) for v in metadata.values())
        
        # Include contexts for strings
        contexts = resource_data.get("contexts", [])
        if contexts:
            search_fields.extend(contexts)
        
        # Perform search
        search_text = " ".join(str(field) for field in search_fields)
        if not case_sensitive:
            search_text = search_text.lower()
        
        return query in search_text

    def _update_large_resources_index(self, threshold: int) -> None:
        """Update the large resources index with new threshold."""
        self.indexes["large_resources"].clear()
        
        for resources in self.resources.values():
            for resource_id, resource_data in resources.items():
                size = resource_data.get("size")
                if size and size > threshold:
                    self.indexes["large_resources"].add(resource_id)

    def _find_resource(self, resource_id: str) -> dict[str, Any | None]:




        """Find a resource by ID."""
        for resources in self.resources.values():
            if resource_id in resources:
                return resources[resource_id]
        return None
