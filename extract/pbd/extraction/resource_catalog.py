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
from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET

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
            'images': {}, 'strings': {}, 'binary': {}, 'pcode': {}, 'datawindows': {}, 'other': {}
        }
        
        # Cross-references
        self.resource_usage: dict[str, set[str]] = defaultdict(set)  # resource_id -> set of object_ids
        self.object_resources: dict[str, set[str]] = defaultdict(set)  # object_id -> set of resource_ids
        
        # Metadata
        self.metadata = {
            'created': datetime.now().isoformat(), 'last_updated': datetime.now().isoformat(), 'version': '1.0', 'statistics': {}
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
        resource_id = self._generate_resource_id('IMG', source_file, image_data.get('offset', 0))
        
        # Store resource
        self.resources['images'][resource_id] = {
            'id': resource_id, 'source_file': source_file, 'format': image_data.get('format'), 'size': image_data.get('size'), 'offset': image_data.get('offset'), 'metadata': image_data.get('metadata', {}), 'saved_path': image_data.get('saved_path'), 'added': datetime.now().isoformat()
        }
        
        # Update cross-references
        self._add_cross_reference(resource_id, source_file)
        
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
        if resource_id in self.resources['strings']:
            # Update sources
            existing = self.resources['strings'][resource_id]
            if source_file not in existing['sources']:
                existing['sources'].append(source_file)
                existing['occurrences'] += 1
        else:
            # Store new string resource
            self.resources['strings'][resource_id] = {
                'id': resource_id, 'value': string_value, 'sources': [source_file], 'contexts': [context] if context else [], 'length': len(string_value), 'occurrences': 1, 'added': datetime.now().isoformat()
            }
            
        # Update cross-references
        self._add_cross_reference(resource_id, source_file)
        
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
        resource_id = self._generate_resource_id('BIN', source_file, data_info.get('offset', 0))
        
        # Store resource
        self.resources['binary'][resource_id] = {
            'id': resource_id, 'source_file': source_file, 'resource_type': resource_type, 'size': data_info.get('size'), 'offset': data_info.get('offset'), 'saved_path': data_info.get('saved_path'), 'metadata': data_info.get('metadata', {}), 'added': datetime.now().isoformat()
        }
        
        # Update cross-references
        self._add_cross_reference(resource_id, source_file)
        
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
        
        for resource_id, string_data in self.resources['strings'].items():
            if string_data['occurrences'] > 1:
                duplicates[string_data['value']] = {
                    'sources': string_data['sources'], 'occurrences': string_data['occurrences'], 'contexts': string_data.get('contexts', [])
                }
                
        return duplicates
        
    def generate_statistics(self) -> dict[str, Any]:

        
        
        
        """Generate catalog statistics.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_resources': sum(len(r) for r in self.resources.values()), 'resource_counts': {}, 'total_size': 0, 'unique_objects': len(self.object_resources), 'common_resources': len(self.find_common_resources()), 'duplicate_strings': len(self.find_duplicate_strings())
        }
        
        # Count by type and calculate sizes
        for resource_type, resources in self.resources.items():
            stats['resource_counts'][resource_type] = len(resources)
            
            # Calculate total size
            for resource in resources.values():
                if 'size' in resource and resource['size']:
                    stats['total_size'] += resource['size']
                    
        # String statistics
        if self.resources['strings']:
            string_lengths = [r['length'] for r in self.resources['strings'].values()]
            stats['string_statistics'] = {
                'total': len(string_lengths), 'min_length': min(string_lengths), 'max_length': max(string_lengths), 'avg_length': sum(string_lengths) / len(string_lengths)
            }
            
        # Image statistics
        if self.resources['images']:
            format_counts = defaultdict(int)
            for img in self.resources['images'].values():
                format_counts[img['format']] += 1
            stats['image_formats'] = dict(format_counts)
            
        self.metadata['statistics'] = stats
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
        summary.append(f"  Total Resources: {stats['total_resources']:, }")
        summary.append(f"  Total Size: {stats['total_size']:, } bytes")
        summary.append(f"  Unique Objects: {stats['unique_objects']}")
        summary.append("")
        
        summary.append("RESOURCE COUNTS:")
        for rtype, count in stats['resource_counts'].items():
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
                if 'value' in resource:  # String resource
                    summary.append(f"    Value: {resource['value'][:50]}...")
        summary.append("")
        
        # Duplicate strings
        summary.append("TOP DUPLICATE STRINGS:")
        duplicates = self.find_duplicate_strings()
        for string, info in sorted(duplicates.items(), key=lambda x:
            x[1]['occurrences'], reverse=True)[:10]:
            summary.append(f"  '{string[:50]}...' - {info['occurrences']} occurrences")
        
        # Write summary
        output_path.write_text('\n'.join(summary))
        logger.info("Exported catalog summary to %s", output_path)
        
    def save_catalog(self) -> None:

        
        
        
        """Save catalog to disk."""
        if not self.catalog_path:
            logger.warning("No catalog path set, cannot save")
            return
            
        try:
            # Update metadata
            self.metadata['last_updated'] = datetime.now().isoformat()
            self.generate_statistics()
            
            # Prepare data for JSON serialization
            catalog_data = {
                'metadata': self.metadata, 'resources': self.resources, 'resource_usage': {k: list(v) for k, v in self.resource_usage.items()}, 'object_resources': {k: list(v) for k, v in self.object_resources.items()}
            }
            
            # Save to file
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.catalog_path, 'w') as f:
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
            self.metadata = catalog_data.get('metadata', self.metadata)
            self.resources = catalog_data.get('resources', self.resources)
            
            # Restore cross-references (convert lists back to sets)
            self.resource_usage = {
                k: set(v) for k, v in catalog_data.get('resource_usage', {}).items()
            }
            self.object_resources = {
                k: set(v) for k, v in catalog_data.get('object_resources', {}).items()
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
        
    def _find_resource(self, resource_id: str) -> dict[str, Any | None]:

        
        
        
        """Find a resource by ID."""
        for resources in self.resources.values():
            if resource_id in resources:
                return resources[resource_id]
        return None