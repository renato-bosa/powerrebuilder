"""Resource catalog for tracking extracted resources."""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ResourceCatalog:
    """Catalog for tracking and managing extracted resources."""

    def __init__(self) -> None:
        """Initialize the resource catalog."""
        self.resources = defaultdict(list)
        self.statistics = defaultdict(int)

    def add_resource(self, resource_type: str, resource_info: dict[str, Any]) -> None:
        """Add a resource to the catalog.

        Args:
            resource_type: Type of resource (e.g., 'image', 'string', 'binary')
            resource_info: Dictionary with resource metadata
        """
        self.resources[resource_type].append(resource_info)
        self.statistics[resource_type] += 1

    def get_resources(self, resource_type: str | None = None) -> dict[str, list] | list:
        """Get resources from the catalog.

        Args:
            resource_type: Optional filter by resource type

        Returns:
            All resources or resources of specified type
        """
        if resource_type:
            return self.resources.get(resource_type, [])
        return dict(self.resources)

    def get_statistics(self) -> dict[str, int]:
        """Get extraction statistics."""
        return dict(self.statistics)

    def add_image_resource(
        self, source_object: str, resource_info: dict[str, Any]
    ) -> None:
        """Add an image resource to the catalog.

        Args:
            source_object: Name of the source object
            resource_info: Dictionary with image metadata (format, size, offset, etc.)
        """
        enhanced_info = {
            "source_object": source_object,
            "resource_type": "image",
            **resource_info,
        }
        self.add_resource("images", enhanced_info)
        logger.debug(
            f"Added image resource from {source_object}: {resource_info.get('format', 'unknown')}"
        )

    def add_string_resource(self, source_object: str, string_value: str) -> None:
        """Add a string resource to the catalog.

        Args:
            source_object: Name of the source object
            string_value: The extracted string value
        """
        resource_info = {
            "source_object": source_object,
            "resource_type": "string",
            "value": string_value,
            "length": len(string_value),
            "encoding": "utf-8",
        }
        self.add_resource("strings", resource_info)
        logger.debug(
            f"Added string resource from {source_object}: {len(string_value)} chars"
        )

    def add_binary_resource(
        self, source_object: str, resource_type: str, resource_info: dict[str, Any]
    ) -> None:
        """Add a binary resource to the catalog.

        Args:
            source_object: Name of the source object
            resource_type: Type of binary resource (e.g., 'wav', 'pdf', 'exe')
            resource_info: Dictionary with resource metadata
        """
        enhanced_info = {
            "source_object": source_object,
            "resource_type": "binary",
            "format": resource_type,
            **resource_info,
        }
        self.add_resource("binary", enhanced_info)
        logger.debug("Added binary resource from %s: %s", source_object, resource_type)

    def save_catalog(self, output_path: Path) -> None:
        """Save catalog to JSON file.

        Args:
            output_path: Directory to save catalog file
        """
        catalog_file = output_path / "resource_catalog.json"
        catalog_data = {
            "resources": dict(self.resources),
            "statistics": dict(self.statistics),
        }

        try:
            with Path(catalog_file).open("w") as f:
                json.dump(catalog_data, f, indent=2, default=str)
            logger.info("Saved resource catalog to %s", catalog_file)
        except Exception as e:
            logger.error("Failed to save resource catalog: %s", e)
