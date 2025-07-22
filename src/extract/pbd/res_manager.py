"""Resource extraction manager for PowerBuilder files."""

import json
import logging
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
                self.source_file_map[source_file].extend(resources)

                for resource in resources:
                    self._track_resource(resource, source_file)

            return resources

        except Exception as e:
            logger.error(
                "Failed to extract resources from %s.%s: %s",
                source_file,
                object_name,
                e,
            )
            self.stats["extraction_errors"] += 1
            return []

    def _track_resource(self, resource: dict[str, Any], _source_file: Any) -> None:
        """Track a resource in statistics.

        Args:
            resource: Resource metadata
            source_file: Source file name
        """
        self.all_resources.append(resource)
        self.stats["total_resources"] += 1

        # Track by type
        resource_type = resource.get("type", "unknown")
        self.stats["resource_types"][resource_type] += 1

        # Track by category
        category = resource.get("category", "unknown")
        self.stats["resource_categories"][category] += 1

        # Track size
        size = resource.get("size", 0)
        self.stats["total_size"] += size
        self.stats["size_by_type"][resource_type] += size
        self.stats["size_by_category"][category] += size

        # Check for duplicates
        resource_hash = resource.get("hash")
        if resource_hash:
            if resource_hash in self.resource_hashes:
                self.stats["duplicate_resources"] += 1
                self.duplicate_count += 1
            else:
                self.resource_hashes.add(resource_hash)
                self.stats["unique_resources"] += 1

    def generate_report(self) -> dict[str, Any]:
        """Generate extraction report.

        Returns:
            Report dictionary
        """
        return {
            "summary": dict(self.stats),
            "files": dict(self.source_file_map),
            "resources": self.all_resources,
            "duplicates": self.duplicate_count,
            "timestamp": time.time(),
        }

    def save_report(self, output_path: Path | None = None) -> None:
        """Save extraction report to JSON file.

        Args:
            output_path: Optional path for report (defaults to base_output_dir)
        """
        if output_path is None:
            output_path = self.base_output_dir / "resource_extraction_report.json"

        report = self.generate_report()

        try:
            with output_path.open("w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info("Saved resource extraction report to %s", output_path)
        except Exception as e:
            logger.error("Failed to save report: %s", e)
