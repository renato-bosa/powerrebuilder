"""Enhanced extractor with resource extraction capabilities.

This module extends the basic extraction functionality to include
comprehensive resource extraction (strings, images, binary data).
"""

import logging
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional

from extract.pbd.extraction.extractor import _extract_pbl_logic
from extract.pbd.extraction.string_extractor import StringResourceExtractor  
from extract.pbd.extraction.enhanced_image_extractor import EnhancedImageExtractor
from extract.pbd.extraction.resource_catalog import ResourceCatalog
from extract.pbd.io.file_operations import save_extracted_file
from extract.pbd.structures.header import PblHeader
from extract.pbd.structures.pbd_object import PbdObject

logger = logging.getLogger(__name__)


class EnhancedExtractor:
    """Enhanced extractor with resource extraction capabilities."""
    
    def __init__(self, output_path: str, enable_resource_extraction: bool = True):
        """Initialize the enhanced extractor.
        
        Args:
            output_path: Base output directory
            enable_resource_extraction: Whether to enable resource extraction
        """
        self.output_path = Path(output_path)
        self.enable_resource_extraction = enable_resource_extraction
        
        if enable_resource_extraction:
            # Initialize resource extractors
            self.string_extractor = StringResourceExtractor()
            self.image_extractor = EnhancedImageExtractor()
            
            # Initialize resource catalog
            catalog_path = self.output_path / "resources" / "resource_catalog.json"
            self.catalog = ResourceCatalog(catalog_path)
            
            # Create resource directories
            self.resources_dir = self.output_path / "resources"
            self.images_dir = self.resources_dir / "images"
            self.strings_dir = self.resources_dir / "strings"
            self.binary_dir = self.resources_dir / "binary"
            
            for dir_path in [self.resources_dir, self.images_dir, 
                           self.strings_dir, self.binary_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
        else:
            self.catalog = None
            
    def extract_with_resources(self, pbd_file_handle: BinaryIO, header: PblHeader,
                             file_name: str, show_progress: bool = True) -> Dict[str, Any]:
        """Extract PBL/PBD file with resource extraction.
        
        Args:
            pbd_file_handle: Open file handle
            header: Parsed PBL header
            file_name: File name for logging
            show_progress: Whether to show progress
            
        Returns:
            Dictionary with extraction statistics
        """
        stats = {
            'objects_extracted': 0,
            'strings_extracted': 0,
            'images_extracted': 0,
            'binary_extracted': 0,
            'errors': 0
        }
        
        # First, do the standard extraction
        logger.info(f"Starting enhanced extraction for {file_name}")
        
        # Use the existing extraction logic
        _extract_pbl_logic(
            pbd_file_handle,
            header,
            str(self.output_path),
            show_progress,
            file_name_for_logging=file_name
        )
        
        # If resource extraction is disabled, return early
        if not self.enable_resource_extraction:
            return stats
            
        # Now extract resources
        logger.info(f"Extracting resources from {file_name}")
        
        # Reset file position for resource extraction
        pbd_file_handle.seek(0)
        file_data = pbd_file_handle.read()
        
        # Extract different resource types
        self._extract_strings(file_data, file_name, stats)
        self._extract_images(file_data, file_name, stats)
        self._extract_properties(file_data, file_name, stats)
        self._extract_string_tables(file_data, file_name, stats)
        
        # Save catalog after each file
        if self.catalog:
            self.catalog.save_catalog()
            
        logger.info(f"Resource extraction complete for {file_name}: "
                   f"{stats['strings_extracted']} strings, "
                   f"{stats['images_extracted']} images")
        
        return stats
    
    def _extract_strings(self, file_data: bytes, file_name: str, stats: Dict[str, Any]) -> None:
        """Extract and save string resources."""
        try:
            strings = self.string_extractor.extract_strings_from_data(file_data, file_name)
            stats['strings_extracted'] = len(strings)
            
            if not strings:
                return
                
            # Save strings
            string_file = self.strings_dir / f"{Path(file_name).stem}_strings.txt"
            string_file.write_text('\n'.join(strings), encoding='utf-8')
            
            # Add to catalog
            for string in strings:
                self.catalog.add_string_resource(file_name, string)
                    
        except Exception as e:
            logger.error(f"Failed to extract strings from {file_name}: {e}")
            stats['errors'] += 1
    
    def _extract_images(self, file_data: bytes, file_name: str, stats: Dict[str, Any]) -> None:
        """Extract and save image resources."""
        try:
            images = self.image_extractor.find_images_in_data(file_data, file_name)
            
            if not images:
                return
                
            # Create subdirectory for this file's images
            file_images_dir = self.images_dir / Path(file_name).stem
            file_images_dir.mkdir(exist_ok=True)
            
            # Save each image
            for i, image_info in enumerate(images):
                image_path = file_images_dir / f"image_{i:03d}.{image_info['format']}"
                image_path.write_bytes(image_info['data'])
                image_info['saved_path'] = str(image_path)
                
                # Add to catalog
                self.catalog.add_image_resource(file_name, image_info)
                
            stats['images_extracted'] = len(images)
                
        except Exception as e:
            logger.error(f"Failed to extract images from {file_name}: {e}")
            stats['errors'] += 1
    
    def _extract_properties(self, file_data: bytes, file_name: str, stats: Dict[str, Any]) -> None:
        """Extract and save property strings."""
        try:
            properties = self.string_extractor.extract_property_strings(file_data)
            if not properties:
                return
                
            # Save properties
            props_file = self.strings_dir / f"{Path(file_name).stem}_properties.txt"
            with open(props_file, 'w', encoding='utf-8') as f:
                for name, value in properties.items():
                    f.write(f"{name}={value}\n")
                    self.catalog.add_string_resource(file_name, value, context=name)
                        
        except Exception as e:
            logger.error(f"Failed to extract properties from {file_name}: {e}")
            stats['errors'] += 1
    
    def _extract_string_tables(self, file_data: bytes, file_name: str, stats: Dict[str, Any]) -> None:
        """Extract and save string tables."""
        try:
            string_tables = self.string_extractor.extract_string_table(file_data)
            if not string_tables:
                return
                
            # Save string table
            table_file = self.strings_dir / f"{Path(file_name).stem}_string_table.txt"
            with open(table_file, 'w', encoding='utf-8') as f:
                for index, string in string_tables:
                    f.write(f"{index:04d}: {string}\n")
                    self.catalog.add_string_resource(file_name, string, 
                                                   context=f"string_table[{index}]")
                        
        except Exception as e:
            logger.error(f"Failed to extract string tables from {file_name}: {e}")
            stats['errors'] += 1
        
    def process_extracted_object(self, obj: PbdObject, object_path: Path) -> None:
        """Process an already extracted object for additional resources.
        
        Args:
            obj: PBD object
            object_path: Path where object was saved
        """
        if not self.enable_resource_extraction or not obj.data:
            return
            
        try:
            # Extract resources from object data
            object_name = object_path.name
            
            # Extract strings from object
            strings = self.string_extractor.extract_strings_from_data(
                obj.data, object_name
            )
            for string in strings:
                self.catalog.add_string_resource(object_name, string)
                
            # Extract images if applicable object type
            if any(object_name.endswith(ext) for ext in 
                   self.image_extractor.SEARCHABLE_OBJECT_TYPES):
                images = self.image_extractor.find_images_in_data(
                    obj.data, object_name
                )
                
                if images:
                    # Save images
                    obj_images_dir = self.images_dir / Path(object_name).stem
                    obj_images_dir.mkdir(exist_ok=True)
                    
                    for i, image_info in enumerate(images):
                        image_path = obj_images_dir / f"{object_name}_img_{i}.{image_info['format']}"
                        image_path.write_bytes(image_info['data'])
                        image_info['saved_path'] = str(image_path)
                        self.catalog.add_image_resource(object_name, image_info)
                        
        except Exception as e:
            logger.error(f"Failed to extract resources from {object_name}: {e}")
            
    def generate_extraction_report(self) -> Path:
        """Generate a comprehensive extraction report.
        
        Returns:
            Path to the generated report
        """
        if not self.catalog:
            return None
            
        # Generate catalog statistics
        stats = self.catalog.generate_statistics()
        
        # Export summary
        summary_path = self.resources_dir / "extraction_summary.txt"
        self.catalog.export_summary(summary_path)
        
        # Create detailed report
        report_path = self.resources_dir / "extraction_report.md"
        report = []
        report.append("# PowerBuilder Resource Extraction Report")
        report.append("")
        report.append(f"Generated: {stats.get('last_updated', 'Unknown')}")
        report.append("")
        
        report.append("## Summary Statistics")
        report.append(f"- Total Resources: {stats['total_resources']:,}")
        report.append(f"- Total Size: {stats['total_size']:,} bytes")
        report.append(f"- Unique Objects: {stats['unique_objects']}")
        report.append("")
        
        report.append("## Resource Breakdown")
        for rtype, count in stats['resource_counts'].items():
            report.append(f"- {rtype.title()}: {count:,}")
        report.append("")
        
        if 'string_statistics' in stats:
            report.append("## String Statistics")
            string_stats = stats['string_statistics']
            report.append(f"- Total Strings: {string_stats['total']:,}")
            report.append(f"- Average Length: {string_stats['avg_length']:.1f} characters")
            report.append(f"- Min/Max Length: {string_stats['min_length']}/{string_stats['max_length']}")
            report.append("")
            
        if 'image_formats' in stats:
            report.append("## Image Formats")
            for format_name, count in stats['image_formats'].items():
                report.append(f"- {format_name.upper()}: {count}")
            report.append("")
            
        # Write report
        report_path.write_text('\n'.join(report))
        logger.info(f"Generated extraction report: {report_path}")
        
        return report_path