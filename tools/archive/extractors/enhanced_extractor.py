"""Enhanced extractor with resource extraction capabilities.

This module extends the basic extraction functionality to include
comprehensive resource extraction (strings, images, binary data).
"""

import logging
from pathlib import Path
from typing import Any, BinaryIO
import struct

from extract.pbd.exceptions import PbdError, HeaderError
from extract.pbd.extraction.enhanced_image_extractor import EnhancedImageExtractor
from extract.pbd.extraction.extractor import _extract_pbl_logic
from extract.pbd.extraction.resource_catalog import ResourceCatalog
from extract.pbd.extraction.string_extractor import StringResourceExtractor
from extract.pbd.structures.header import HeaderClass as PblHeader
from extract.pbd.structures.pbd_object import PbdObject

logger = logging.getLogger(__name__)


class EnhancedExtractor:
    """Enhanced extractor with resource extraction capabilities."""

    def __init__(self, output_path: str, enable_resource_extraction: bool = True) -> None:


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

            for dir_path in [self.resources_dir, self.images_dir, self.strings_dir, self.binary_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
        else:
            self.catalog = None
            
        # Corruption detection settings
        self.max_recovery_attempts = 3
        self.corruption_tolerance = 0.1  # 10% corruption tolerance

    def _detect_corruption(self, file_data: bytes) -> dict[str, Any]:
        """Detect potential corruption in file data.
        
        Returns:
            Dictionary with corruption analysis
        """
        corruption_info = {
            "is_corrupted": False,
            "corruption_level": 0.0,
            "issues": [],
            "recoverable": True
        }
        
        # Check for null bytes at suspicious locations
        null_byte_ratio = file_data.count(b'\x00') / len(file_data) if file_data else 0
        if null_byte_ratio > 0.5:
            corruption_info["issues"].append("High null byte ratio")
            corruption_info["corruption_level"] += 0.3
            
        # Check for repeated patterns (possible corruption)
        if len(file_data) >= 1024:
            sample = file_data[:1024]
            unique_bytes = len(set(sample))
            if unique_bytes < 10:  # Very low entropy
                corruption_info["issues"].append("Low entropy data")
                corruption_info["corruption_level"] += 0.2
                
        # Check for truncated file indicators
        if len(file_data) < 100:
            corruption_info["issues"].append("File too small")
            corruption_info["corruption_level"] += 0.4
            corruption_info["recoverable"] = False
            
        # Check for invalid header patterns
        if file_data and not file_data.startswith((b'PBD', b'PBL')):
            # Check for recoverable header corruption
            for offset in range(min(100, len(file_data) - 3)):
                if file_data[offset:offset+3] in (b'PBD', b'PBL'):
                    corruption_info["issues"].append("Header offset corruption")
                    corruption_info["corruption_level"] += 0.1
                    break
            else:
                corruption_info["issues"].append("Invalid file signature")
                corruption_info["corruption_level"] += 0.5
                
        corruption_info["is_corrupted"] = corruption_info["corruption_level"] > self.corruption_tolerance
        
        return corruption_info

    def _attempt_corruption_recovery(self, file_data: bytes, corruption_info: dict[str, Any]) -> bytes:
        """Attempt to recover from detected corruption.
        
        Args:
            file_data: Original corrupted data
            corruption_info: Corruption analysis from _detect_corruption
            
        Returns:
            Potentially recovered data
        """
        if not corruption_info["recoverable"]:
            return file_data
            
        recovered_data = file_data
        
        # Attempt to fix header offset corruption
        if "Header offset corruption" in corruption_info["issues"]:
            for offset in range(min(100, len(file_data) - 3)):
                if file_data[offset:offset+3] in (b'PBD', b'PBL'):
                    logger.info("Attempting header recovery at offset %d", offset)
                    recovered_data = file_data[offset:]
                    break
                    
        # Attempt to remove null padding corruption
        if "High null byte ratio" in corruption_info["issues"]:
            # Remove excessive null bytes while preserving structure
            recovered_data = recovered_data.rstrip(b'\x00')
            
        return recovered_data

    def extract_with_resources(self, pbd_file_handle: BinaryIO, header: PblHeader, file_name: str, show_progress: bool = True) -> dict[str, Any]:




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
            "objects_extracted": 0, "strings_extracted": 0, "images_extracted": 0, "binary_extracted": 0, "errors": 0,
        }

        # First, do the standard extraction
        logger.info("Starting enhanced extraction for %s", file_name)

        # Use the existing extraction logic
        _extract_pbl_logic(
            pbd_file_handle, header, str(self.output_path), show_progress, file_name_for_logging=file_name,
        )

        # If resource extraction is disabled, return early
        if not self.enable_resource_extraction:
            return stats

        # Now extract resources
        logger.info("Extracting resources from %s", file_name)

        # Reset file position for resource extraction
        pbd_file_handle.seek(0)
        file_data = pbd_file_handle.read()

        # Detect and handle corruption
        corruption_info = self._detect_corruption(file_data)
        if corruption_info["is_corrupted"]:
            logger.warning("Corruption detected in %s: %s (level: %.2f)", 
                          file_name, corruption_info["issues"], 
                          corruption_info["corruption_level"])
            
            if corruption_info["recoverable"]:
                original_data = file_data
                file_data = self._attempt_corruption_recovery(file_data, corruption_info)
                if file_data != original_data:
                    logger.info("Applied corruption recovery to %s", file_name)
                    # Re-check corruption after recovery
                    new_corruption_info = self._detect_corruption(file_data)
                    if new_corruption_info["corruption_level"] < corruption_info["corruption_level"]:
                        logger.info("Corruption level reduced from %.2f to %.2f", 
                                   corruption_info["corruption_level"], 
                                   new_corruption_info["corruption_level"])
            else:
                logger.error("File %s appears to be severely corrupted and may not be recoverable", 
                            file_name)
                stats["errors"] += 1
                
        # Extract different resource types with error resilience
        self._extract_strings_with_recovery(file_data, file_name, stats)
        self._extract_images_with_recovery(file_data, file_name, stats)
        self._extract_properties_with_recovery(file_data, file_name, stats)
        self._extract_string_tables_with_recovery(file_data, file_name, stats)

        # Save catalog after each file
        if self.catalog:
            self.catalog.save_catalog()

        logger.info("Resource extraction complete for %s: %s strings, %s images", file_name, stats["strings_extracted"], stats["images_extracted"])

        return stats

    def _extract_strings_with_recovery(self, file_data: bytes, file_name: str, stats: dict[str, Any]) -> None:
        """Extract strings with corruption recovery."""
        for attempt in range(self.max_recovery_attempts):
            try:
                self._extract_strings(file_data, file_name, stats)
                break
            except (struct.error, UnicodeDecodeError, IndexError) as e:
                logger.warning("String extraction attempt %d failed for %s: %s", 
                              attempt + 1, file_name, e)
                if attempt == self.max_recovery_attempts - 1:
                    logger.error("All string extraction attempts failed for %s", file_name)
                    stats["errors"] += 1
                else:
                    # Try with a smaller data window
                    max_size = len(file_data) // (2 ** (attempt + 1))
                    file_data = file_data[:max_size] if max_size > 1000 else file_data
                    
    def _extract_strings(self, file_data: bytes, file_name: str, stats: dict[str, Any]) -> None:




        """Extract and save string resources."""
        try:
            strings = self.string_extractor.extract_strings_from_data(file_data, file_name)
            stats["strings_extracted"] = len(strings)

            if not strings:
                return

            # Save strings
            string_file = self.strings_dir / f"{Path(file_name).stem}_strings.txt"
            string_file.write_text("\n".join(strings), encoding="utf-8")

            # Add to catalog
            for string in strings:
                self.catalog.add_string_resource(file_name, string)

        except Exception as e:
            logger.error("Failed to extract strings from %s: %s", file_name, e)
            stats["errors"] += 1

    def _extract_images_with_recovery(self, file_data: bytes, file_name: str, stats: dict[str, Any]) -> None:
        """Extract images with corruption recovery."""
        for attempt in range(self.max_recovery_attempts):
            try:
                self._extract_images(file_data, file_name, stats)
                break
            except (struct.error, IndexError, ValueError) as e:
                logger.warning("Image extraction attempt %d failed for %s: %s", 
                              attempt + 1, file_name, e)
                if attempt == self.max_recovery_attempts - 1:
                    logger.error("All image extraction attempts failed for %s", file_name)
                    stats["errors"] += 1
                else:
                    # Try with progressive data reduction
                    reduction_factor = 2 ** (attempt + 1)
                    file_data = file_data[::reduction_factor] if len(file_data) > 1000 else file_data
                    
    def _extract_images(self, file_data: bytes, file_name: str, stats: dict[str, Any]) -> None:




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
                image_path = file_images_dir / f"image_{i:03d}.{image_info["format"]}"
                image_path.write_bytes(image_info["data"])
                image_info["saved_path"] = str(image_path)

                # Add to catalog
                self.catalog.add_image_resource(file_name, image_info)

            stats["images_extracted"] = len(images)

        except Exception as e:
            logger.error("Failed to extract images from %s: %s", file_name, e)
            stats["errors"] += 1

    def _extract_properties_with_recovery(self, file_data: bytes, file_name: str, stats: dict[str, Any]) -> None:
        """Extract properties with corruption recovery."""
        for attempt in range(self.max_recovery_attempts):
            try:
                self._extract_properties(file_data, file_name, stats)
                break
            except (struct.error, UnicodeDecodeError, ValueError) as e:
                logger.warning("Properties extraction attempt %d failed for %s: %s", 
                              attempt + 1, file_name, e)
                if attempt == self.max_recovery_attempts - 1:
                    logger.error("All properties extraction attempts failed for %s", file_name)
                    stats["errors"] += 1
                else:
                    # Try with limited data range
                    max_size = len(file_data) // 2
                    file_data = file_data[:max_size] if max_size > 500 else file_data
                    
    def _extract_properties(self, file_data: bytes, file_name: str, stats: dict[str, Any]) -> None:




        """Extract and save property strings."""
        try:
            properties = self.string_extractor.extract_property_strings(file_data)
            if not properties:
                return

            # Save properties
            props_file = self.strings_dir / f"{Path(file_name).stem}_properties.txt"
            with open(props_file, "w", encoding="utf-8") as f:
                for name, value in properties.items():
                    f.write(f"{name}={value}\n")
                    self.catalog.add_string_resource(file_name, value, context=name)

        except Exception as e:
            logger.error("Failed to extract properties from %s: %s", file_name, e)
            stats["errors"] += 1

    def _extract_string_tables_with_recovery(self, file_data: bytes, file_name: str, stats: dict[str, Any]) -> None:
        """Extract string tables with corruption recovery."""
        for attempt in range(self.max_recovery_attempts):
            try:
                self._extract_string_tables(file_data, file_name, stats)
                break
            except (struct.error, UnicodeDecodeError, IndexError) as e:
                logger.warning("String table extraction attempt %d failed for %s: %s", 
                              attempt + 1, file_name, e)
                if attempt == self.max_recovery_attempts - 1:
                    logger.error("All string table extraction attempts failed for %s", file_name)
                    stats["errors"] += 1
                else:
                    # Try with byte-aligned boundaries
                    alignment = 4 * (attempt + 1)
                    aligned_size = (len(file_data) // alignment) * alignment
                    file_data = file_data[:aligned_size] if aligned_size > 100 else file_data
                    
    def _extract_string_tables(self, file_data: bytes, file_name: str, stats: dict[str, Any]) -> None:




        """Extract and save string tables."""
        try:
            string_tables = self.string_extractor.extract_string_table(file_data)
            if not string_tables:
                return

            # Save string table
            table_file = self.strings_dir / f"{Path(file_name).stem}_string_table.txt"
            with open(table_file, "w", encoding="utf-8") as f:
                for index, string in string_tables:
                    f.write(f"{index:04d}: {string}\n")
                    self.catalog.add_string_resource(file_name, string, context=f"string_table[{index}]")

        except Exception as e:
            logger.error("Failed to extract string tables from %s: %s", file_name, e)
            stats["errors"] += 1

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
                obj.data, object_name,
            )
            for string in strings:
                self.catalog.add_string_resource(object_name, string)

            # Extract images if applicable object type
            if any(object_name.endswith(ext) for ext in 
                   self.image_extractor.SEARCHABLE_OBJECT_TYPES):
                images = self.image_extractor.find_images_in_data(
                    obj.data, object_name,
                )

                if images:
                    # Save images
                    obj_images_dir = self.images_dir / Path(object_name).stem
                    obj_images_dir.mkdir(exist_ok=True)

                    for i, image_info in enumerate(images):
                        image_path = obj_images_dir / f"{object_name}_img_{i}.{image_info["format"]}"
                        image_path.write_bytes(image_info["data"])
                        image_info["saved_path"] = str(image_path)
                        self.catalog.add_image_resource(object_name, image_info)

        except Exception as e:
            logger.error("Failed to extract resources from %s: %s", object_name, e)

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
        report.append(f"Generated: {stats.get("last_updated", "Unknown")}")
        report.append("")

        report.append("## Summary Statistics")
        report.append(f"- Total Resources: {stats["total_resources"]:, }")
        report.append(f"- Total Size: {stats["total_size"]:, } bytes")
        report.append(f"- Unique Objects: {stats["unique_objects"]}")
        report.append("")

        report.append("## Resource Breakdown")
        for rtype, count in stats["resource_counts"].items():
            report.append(f"- {rtype.title()}: {count:, }")
        report.append("")

        if "string_statistics" in stats:
            report.append("## String Statistics")
            string_stats = stats["string_statistics"]
            report.append(f"- Total Strings: {string_stats["total"]:, }")
            report.append(f"- Average Length: {string_stats["avg_length"]:.1f} characters")
            report.append(f"- Min/Max Length: {string_stats["min_length"]}/{string_stats["max_length"]}")
            report.append("")

        if "image_formats" in stats:
            report.append("## Image Formats")
            for format_name, count in stats["image_formats"].items():
                report.append(f"- {format_name.upper()}: {count}")
            report.append("")

        # Write report
        report_path.write_text("\n".join(report))
        logger.info("Generated extraction report: %s", report_path)

        return report_path
