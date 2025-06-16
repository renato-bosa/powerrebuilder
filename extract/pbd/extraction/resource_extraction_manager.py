"""Resource extraction manager for PowerBuilder files.

This module provides a centralized manager for resource extraction that:
- Coordinates extraction across multiple files
- Provides better progress tracking
- Handles resource deduplication across the entire extraction
- Generates comprehensive reports
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict

from extract.pbd.extraction.unified_resource_extractor import UnifiedResourceExtractor

logger = logging.getLogger(__name__)


class ResourceExtractionManager:
    """Manages resource extraction across multiple PowerBuilder files."""
    
    def __init__(self, base_output_dir: Path):
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
        self.all_resources: List[Dict[str, Any]] = []
        self.resource_hashes: Set[str] = set()
        self.source_file_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.duplicate_count = 0
        
        # Enhanced statistics
        self.stats = {
            'total_files_processed': 0,
            'files_with_resources': 0,
            'total_resources': 0,
            'unique_resources': 0,
            'duplicate_resources': 0,
            'resource_types': defaultdict(int),
            'resource_categories': defaultdict(int),
            'total_size': 0,
            'size_by_type': defaultdict(int),
            'size_by_category': defaultdict(int),
            'extraction_errors': 0
        }
    
    def extract_from_object(self, data: bytes, source_file: str, 
                           object_name: str, object_type: str) -> List[Dict[str, Any]]:
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
                self.stats['total_files_processed'] += 1
            
            # Extract resources
            resources = self.extractor.extract_resources_from_data(
                data, object_name, object_type
            )
            
            if resources:
                self.stats['files_with_resources'] += 1
                
                # Process each resource
                for resource in resources:
                    # Add source file info
                    resource['source_file'] = source_file
                    
                    # Check for duplicates globally
                    if resource['hash'] in self.resource_hashes:
                        self.duplicate_count += 1
                        self.stats['duplicate_resources'] += 1
                        resource['is_duplicate'] = True
                    else:
                        self.resource_hashes.add(resource['hash'])
                        self.stats['unique_resources'] += 1
                        resource['is_duplicate'] = False
                    
                    # Update statistics
                    self.stats['total_resources'] += 1
                    self.stats['resource_types'][resource['type']] += 1
                    
                    category = self.extractor._get_resource_category(resource['type'])
                    self.stats['resource_categories'][category] += 1
                    self.stats['size_by_type'][resource['type']] += resource['size']
                    self.stats['size_by_category'][category] += resource['size']
                    
                    # Track by source file
                    self.source_file_map[source_file].append(resource)
                    self.all_resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.error(f"Failed to extract resources from {object_name}: {e}")
            self.stats['extraction_errors'] += 1
            return []
    
    def generate_comprehensive_report(self) -> None:
        """Generate comprehensive extraction report and manifests."""
        # Update total size
        self.stats['total_size'] = self.extractor.stats['total_size']
        
        # Generate main manifest
        self._generate_main_manifest()
        
        # Generate detailed resource catalog
        self._generate_detailed_catalog()
        
        # Generate source file report
        self._generate_source_file_report()
        
        # Generate statistics report
        self._generate_statistics_report()
        
        # Let the extractor generate its own reports
        self.extractor.generate_manifest()
        
        logger.info(
            f"Resource extraction complete: {self.stats['total_resources']} total resources "
            f"({self.stats['unique_resources']} unique, {self.stats['duplicate_resources']} duplicates) "
            f"from {self.stats['total_files_processed']} files"
        )
    
    def _generate_main_manifest(self) -> None:
        """Generate the main resource manifest."""
        manifest_path = self.resources_dir / "extraction_manifest.json"
        
        manifest = {
            'extraction_summary': {
                'total_files_processed': self.stats['total_files_processed'],
                'files_with_resources': self.stats['files_with_resources'],
                'total_resources_found': self.stats['total_resources'],
                'unique_resources': self.stats['unique_resources'],
                'duplicate_resources': self.stats['duplicate_resources'],
                'total_size_bytes': self.stats['total_size'],
                'extraction_errors': self.stats['extraction_errors']
            },
            'resource_types': dict(self.stats['resource_types']),
            'resource_categories': dict(self.stats['resource_categories']),
            'size_by_type': dict(self.stats['size_by_type']),
            'size_by_category': dict(self.stats['size_by_category'])
        }
        
        with open(manifest_path, 'w') as f:
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
                'id': resource['id'],
                'type': resource['type'],
                'size': resource['size'],
                'source_object': resource['source_object'],
                'source_file': resource.get('source_file', 'unknown'),
                'path': resource['path'],
                'is_duplicate': resource.get('is_duplicate', False),
                'metadata': resource.get('metadata', {})
            }
            
            by_type[resource['type']].append(resource_info)
            category = self.extractor._get_resource_category(resource['type'])
            by_category[category].append(resource_info)
            by_source[resource.get('source_file', 'unknown')].append(resource_info)
        
        catalog = {
            'by_type': dict(by_type),
            'by_category': dict(by_category),
            'by_source': dict(by_source)
        }
        
        with open(catalog_path, 'w') as f:
            json.dump(catalog, f, indent=2)
    
    def _generate_source_file_report(self) -> None:
        """Generate report grouped by source files."""
        report_path = self.resources_dir / "source_file_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("PowerBuilder Resource Extraction - Source File Report\n")
            f.write("=" * 70 + "\n\n")
            
            for source_file, resources in sorted(self.source_file_map.items()):
                f.write(f"Source File: {source_file}\n")
                f.write(f"Resources Found: {len(resources)}\n")
                
                # Group by type
                type_counts = defaultdict(int)
                total_size = 0
                for resource in resources:
                    type_counts[resource['type']] += 1
                    total_size += resource['size']
                
                f.write(f"Total Size: {total_size:,} bytes\n")
                f.write("Resource Types:\n")
                for res_type, count in sorted(type_counts.items()):
                    f.write(f"  - {res_type}: {count}\n")
                f.write("\n")
    
    def _generate_statistics_report(self) -> None:
        """Generate detailed statistics report."""
        report_path = self.resources_dir / "extraction_statistics.txt"
        
        with open(report_path, 'w') as f:
            f.write("PowerBuilder Resource Extraction - Statistics Report\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("Overall Statistics:\n")
            f.write(f"  Total Files Processed: {self.stats['total_files_processed']}\n")
            f.write(f"  Files with Resources: {self.stats['files_with_resources']}\n")
            f.write(f"  Total Resources Found: {self.stats['total_resources']}\n")
            f.write(f"  Unique Resources: {self.stats['unique_resources']}\n")
            f.write(f"  Duplicate Resources: {self.stats['duplicate_resources']}\n")
            f.write(f"  Total Size: {self.stats['total_size']:,} bytes ({self.stats['total_size'] / 1024 / 1024:.2f} MB)\n")
            f.write(f"  Extraction Errors: {self.stats['extraction_errors']}\n\n")
            
            f.write("Resources by Category:\n")
            for category, count in sorted(self.stats['resource_categories'].items()):
                size = self.stats['size_by_category'][category]
                f.write(f"  {category}: {count} resources ({size:,} bytes)\n")
            
            f.write("\nResources by Type:\n")
            for res_type, count in sorted(self.stats['resource_types'].items()):
                size = self.stats['size_by_type'][res_type]
                f.write(f"  {res_type}: {count} resources ({size:,} bytes)\n")
            
            if self.stats['extraction_errors'] > 0:
                f.write(f"\nWarning: {self.stats['extraction_errors']} extraction errors occurred.\n")
                f.write("Check the log files for details.\n")