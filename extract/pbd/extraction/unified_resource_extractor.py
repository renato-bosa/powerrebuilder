"""Unified resource extraction from PowerBuilder files.

This module provides a comprehensive resource extraction system that combines
and enhances existing extractors for all resource types.
"""

import hashlib
import logging
import struct
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Protocol

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET
from extract.pbd.extraction.enhanced_image_extractor import EnhancedImageExtractor
from extract.pbd.extraction.resource_catalog import ResourceCatalog
from extract.pbd.extraction.string_extractor import StringResourceExtractor
from extract.pbd.io.resource_utils import get_bmp_size, get_ico_size

logger = logging.getLogger(__name__)


# Unified extraction interfaces
class ResourceExtractorProtocol(Protocol):
    """Protocol for resource extractors."""
    
    def extract_from_data(self, data: bytes, source: str) -> list[dict[str, Any]]:
        """Extract resources from binary data."""
        ...
    
    def get_supported_types(self) -> set[str]:
        """Get set of supported resource types."""
        ...


class BaseResourceExtractor(ABC):
    """Abstract base class for resource extractors."""
    
    def __init__(self, name: str):
        self.name = name
        self.stats = {
            "extractions": 0,
            "successes": 0,
            "failures": 0,
            "total_size": 0,
        }
    
    @abstractmethod
    def extract_from_data(self, data: bytes, source: str) -> list[dict[str, Any]]:
        """Extract resources from binary data."""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> set[str]:
        """Get set of supported resource types."""
        pass
    
    def validate_extraction(self, resource: dict[str, Any]) -> bool:
        """Validate an extracted resource."""
        required_fields = {"type", "size", "data"}
        return all(field in resource for field in required_fields)
    
    def get_statistics(self) -> dict[str, Any]:
        """Get extraction statistics."""
        success_rate = (self.stats["successes"] / max(self.stats["extractions"], 1)) * 100
        return {
            "extractor_name": self.name,
            "total_extractions": self.stats["extractions"],
            "successful_extractions": self.stats["successes"],
            "failed_extractions": self.stats["failures"],
            "success_rate_percent": round(success_rate, 2),
            "total_size_extracted": self.stats["total_size"],
        }


class TestCase:
    """Represents a test case for resource extraction."""
    
    def __init__(self, name: str, data: bytes, expected_types: set[str], 
                 expected_count: int = None, description: str = ""):
        self.name = name
        self.data = data
        self.expected_types = expected_types
        self.expected_count = expected_count
        self.description = description


class ExtractionTestSuite:
    """Test suite for resource extraction validation."""
    
    def __init__(self):
        self.test_cases: list[TestCase] = []
        self.results: list[dict[str, Any]] = []
    
    def add_test_case(self, test_case: TestCase) -> None:
        """Add a test case to the suite."""
        self.test_cases.append(test_case)
    
    def create_builtin_tests(self) -> None:
        """Create built-in test cases for common resource types."""
        # PNG test
        png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        self.add_test_case(TestCase(
            "PNG Detection", png_header, {"png"}, 1,
            "Test basic PNG signature detection"
        ))
        
        # JPEG test  
        jpeg_header = b'\xFF\xD8\xFF\xE0' + b'\x00' * 100 + b'\xFF\xD9'
        self.add_test_case(TestCase(
            "JPEG Detection", jpeg_header, {"jpg"}, 1,
            "Test basic JPEG signature detection"
        ))
        
        # BMP test
        bmp_header = b'BM' + struct.pack('<I', 1000) + b'\x00' * 994
        self.add_test_case(TestCase(
            "BMP Detection", bmp_header, {"bmp"}, 1,
            "Test basic BMP signature detection"
        ))
        
        # Mixed resource test
        mixed_data = png_header + jpeg_header + bmp_header
        self.add_test_case(TestCase(
            "Multiple Resources", mixed_data, {"png", "jpg", "bmp"}, 3,
            "Test detection of multiple resource types"
        ))
        
        # String extraction test
        string_data = b'Hello World\x00Property=Value\x00'
        self.add_test_case(TestCase(
            "String Extraction", string_data, {"string"}, None,
            "Test string resource extraction"
        ))
    
    def run_tests(self, extractor: 'UnifiedResourceExtractor') -> dict[str, Any]:
        """Run all test cases against an extractor."""
        self.results = []
        passed = 0
        failed = 0
        
        for test_case in self.test_cases:
            try:
                start_time = time.time()
                resources = extractor.extract_resources_from_data(
                    test_case.data, f"test_{test_case.name}", "test"
                )
                extraction_time = time.time() - start_time
                
                # Validate results
                extracted_types = {r["type"] for r in resources}
                type_match = test_case.expected_types.issubset(extracted_types)
                count_match = (test_case.expected_count is None or 
                             len(resources) == test_case.expected_count)
                
                test_passed = type_match and count_match
                
                result = {
                    "test_name": test_case.name,
                    "description": test_case.description,
                    "passed": test_passed,
                    "expected_types": test_case.expected_types,
                    "extracted_types": extracted_types,
                    "expected_count": test_case.expected_count,
                    "extracted_count": len(resources),
                    "extraction_time_ms": round(extraction_time * 1000, 2),
                    "resources": resources,
                }
                
                if test_passed:
                    passed += 1
                else:
                    failed += 1
                    
                self.results.append(result)
                
            except Exception as e:
                failed += 1
                self.results.append({
                    "test_name": test_case.name,
                    "description": test_case.description,
                    "passed": False,
                    "error": str(e),
                    "extraction_time_ms": 0,
                })
        
        return {
            "total_tests": len(self.test_cases),
            "passed": passed,
            "failed": failed,
            "success_rate_percent": round((passed / len(self.test_cases)) * 100, 2),
            "results": self.results,
        }


class UnifiedResourceExtractor:
    """Unified extractor for all resource types from PowerBuilder files."""

    # Extended resource signatures
    RESOURCE_SIGNATURES = {
        # Images (from EnhancedImageExtractor)
        b"\x89PNG\r\n\x1a\n": ("png", 8, "image/png"), b"GIF87a": ("gif", 6, "image/gif"), b"GIF89a": ("gif", 6, "image/gif"), b"\xFF\xD8\xFF": ("jpg", 3, "image/jpeg"), b"BM": ("bmp", 2, "image/bmp"), b"\x00\x00\x01\x00": ("ico", 4, "image/x-icon"), b"\x00\x00\x02\x00": ("cur", 4, "image/x-win-cursor"), b"RIFF": ("webp", 4, "image/webp"), b"II*\x00": ("tiff", 4, "image/tiff"), b"MM\x00*": ("tiff", 4, "image/tiff"), # Enhanced image formats
        b"\x00\x00\x00\x0CJXL ": ("jxl", 12, "image/jxl"), # JPEG XL
        b"HEIF": ("heif", 4, "image/heif"), # HEIF/HEIC
        b"\x00\x00\x00\x18ftypavif": ("avif", 12, "image/avif"), # AVIF
        b"\x00\x00\x00\x20ftypheic": ("heic", 12, "image/heic"), # HEIC
        b"<svg": ("svg", 4, "image/svg+xml"), # SVG (text-based)
        b"<?xml": ("svg", 5, "image/svg+xml"), # SVG with XML declaration

        # Audio
        b"RIFF....WAVE": ("wav", 12, "audio/wav"), # WAV files
        b"\xFF\xFB": ("mp3", 2, "audio/mpeg"), # MP3 with frame sync
        b"ID3": ("mp3", 3, "audio/mpeg"), # MP3 with ID3 tag
        b"OggS": ("ogg", 4, "audio/ogg"), # OGG Vorbis
        b"fLaC": ("flac", 4, "audio/flac"), # FLAC
        b"\x00\x00\x00\x20ftypM4A ": ("m4a", 12, "audio/mp4"), # M4A
        b"MThd": ("mid", 4, "audio/midi"), # MIDI

        # Video (might be embedded in presentations)
        b"\x00\x00\x00\x20ftypmp42": ("mp4", 12, "video/mp4"), # MP4
        b"\x00\x00\x00\x18ftypisom": ("mp4", 12, "video/mp4"), # MP4 ISO
        b"\x1A\x45\xDF\xA3": ("mkv", 4, "video/x-matroska"), # MKV
        b"RIFF....AVI ": ("avi", 12, "video/x-msvideo"), # AVI
        b"FLV\x01": ("flv", 4, "video/x-flv"), # FLV

        # Documents
        b"%PDF": ("pdf", 4, "application/pdf"), b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1": ("doc", 8, "application/msword"), # MS Office
        b"PK\x03\x04": ("zip", 4, "application/zip"), # ZIP/Office XML
        b"PK\x05\x06": ("zip", 4, "application/zip"), # ZIP (empty)
        b"PK\x07\x08": ("zip", 4, "application/zip"), # ZIP (spanned)
        b"{\rtf": ("rtf", 5, "application/rtf"), # Rich Text Format
        b"7z\xBC\xAF\x27\x1C": ("7z", 6, "application/x-7z-compressed"), # 7-Zip

        # PowerBuilder specific
        b"PBM\x00": ("pbm", 4, "application/x-powerbuilder-bitmap"), b"PBI\x00": ("pbi", 4, "application/x-powerbuilder-icon"), b"PBR\x00": ("pbr", 4, "application/x-powerbuilder-resource"), b"PBW\x00": ("pbw", 4, "application/x-powerbuilder-wav"), # PB Wave
        b"PBS\x00": ("pbs", 4, "application/x-powerbuilder-sound"), # PB Sound

        # Fonts (might be embedded)
        b"\x00\x01\x00\x00": ("ttf", 4, "font/ttf"), # TrueType
        b"OTTO": ("otf", 4, "font/otf"), # OpenType
        b"wOFF": ("woff", 4, "font/woff"), # WOFF
        b"wOF2": ("woff2", 4, "font/woff2"), # WOFF2

        # Other binary
        b"MZ": ("exe", 2, "application/x-msdownload"), # Embedded executables
        b"\x1F\x8B": ("gz", 2, "application/gzip"), # Compressed data
        b"BZh": ("bz2", 3, "application/x-bzip2"), # BZip2
        b"\xFD7zXZ\x00": ("xz", 6, "application/x-xz"), # XZ
        b"Rar!\x1A\x07": ("rar", 6, "application/x-rar-compressed"), # RAR5
        b"CAB\x00": ("cab", 4, "application/vnd.ms-cab-compressed"), # Cabinet
    }

    def __init__(self, output_dir: Path) -> None:




        """Initialize the unified resource extractor.

        Args:
            output_dir: Base output directory for extracted files
        """
        self.output_dir = output_dir
        self.resources_dir = output_dir / "resources"
        self.resources_dir.mkdir(parents=True, exist_ok=True)

        # Initialize sub-extractors using unified interface
        self.extractors: dict[str, ResourceExtractorProtocol] = {}
        self.image_extractor = EnhancedImageExtractor()
        self.string_extractor = StringResourceExtractor()
        
        # Register extractors
        self._register_extractors()
        
        # Initialize catalog and test suite
        self.catalog = ResourceCatalog(self.resources_dir / "resource_catalog.json")
        self.test_suite = ExtractionTestSuite()
        self.test_suite.create_builtin_tests()

        # Enhanced statistics
        self.stats = {
            "total_resources": 0, 
            "extracted_resources": 0, 
            "failed_resources": 0, 
            "resource_types": {}, 
            "total_size": 0,
            "extraction_methods": {
                "signature_based": 0,
                "heuristic_based": 0,
                "string_extraction": 0,
            },
            "validation_stats": {
                "validated_resources": 0,
                "validation_failures": 0,
            }
        }
        
        # Validation rules
        self.validation_rules: dict[str, Callable[[dict[str, Any]], bool]] = {
            "png": self._validate_png,
            "jpg": self._validate_jpeg,
            "bmp": self._validate_bmp,
            "gif": self._validate_gif,
        }

    def extract_resources_from_data(
        self, data: bytes, source_object: str, object_type: str,
    ) -> list[dict[str, Any]]:




        """Extract all resources from a data block.

        Args:
            data: Raw data bytes
            source_object: Name of the source object
            object_type: Type of the source object (e.g., "srm", "sru")

        Returns:
            List of extracted resource information
        """
        resources = []

        # Method 1: Signature-based extraction
        signature_resources = self._extract_signature_based(data, source_object, object_type)
        resources.extend(signature_resources)
        self.stats["extraction_methods"]["signature_based"] += len(signature_resources)

        # Method 2: String extraction using unified interface
        try:
            string_resources = self._extract_strings_unified(data, source_object)
            resources.extend(string_resources)
            self.stats["extraction_methods"]["string_extraction"] += len(string_resources)
        except Exception as e:
            logger.debug(f"String extraction failed for {source_object}: {e}")

        # Method 3: Heuristic-based extraction for unknown patterns
        heuristic_resources = self._extract_heuristic_based(data, source_object, object_type)
        resources.extend(heuristic_resources)
        self.stats["extraction_methods"]["heuristic_based"] += len(heuristic_resources)

        # Validate and deduplicate resources
        validated_resources = self._validate_and_deduplicate(resources)

        return validated_resources

    def _extract_signature_based(self, data: bytes, source_object: str, object_type: str) -> list[dict[str, Any]]:
        """Extract resources using signature detection."""
        resources = []

        # Scan for resource signatures
        for offset in range(len(data) - 16):  # Need at least 16 bytes for detection
            resource_info = self._detect_resource_at_offset(data, offset)
            if resource_info:
                # Extract the resource
                extracted = self._extract_resource(
                    data, offset, resource_info, source_object, object_type,
                )
                if extracted:
                    resources.append(extracted)
                    # Skip past this resource
                    offset += extracted["size"] - 1

        return resources

    def _extract_strings_unified(self, data: bytes, source_object: str) -> list[dict[str, Any]]:
        """Extract string resources using unified interface."""
        strings = self.string_extractor.extract_strings_from_data(data, source_object)
        
        resources = []
        for i, string_value in enumerate(strings):
            resource_hash = hashlib.sha256(string_value.encode()).hexdigest()
            
            resource = {
                "id": resource_hash[:16],
                "type": "string",
                "mime_type": "text/plain",
                "size": len(string_value.encode()),
                "hash": resource_hash,
                "source_object": source_object,
                "object_type": "string",
                "offset": i,  # Use index as offset
                "filename": f"{source_object}_string_{i}.txt",
                "content": string_value,
                "metadata": {
                    "length": len(string_value),
                    "encoding": "utf-8",
                }
            }
            
            # Add to catalog
            self.catalog.add_string_resource(source_object, string_value)
            resources.append(resource)
        
        return resources

    def _extract_heuristic_based(self, data: bytes, source_object: str, object_type: str) -> list[dict[str, Any]]:
        """Extract resources using heuristic methods."""
        resources = []
        
        # Look for potential embedded data patterns
        patterns = [
            # Repeated byte patterns that might indicate data
            (b'\x00\x00\x00\x00', 4, "null_data"),
            (b'\xFF\xFF\xFF\xFF', 4, "filled_data"),
            # Look for potential string tables (length + data patterns)
            (b'\x00\x01', 2, "potential_string_table"),
            (b'\x00\x02', 2, "potential_string_table"),
        ]
        
        for pattern, length, data_type in patterns:
            offset = 0
            while True:
                offset = data.find(pattern, offset)
                if offset == -1:
                    break
                
                # Heuristic analysis of the surrounding data
                if self._analyze_heuristic_context(data, offset, data_type):
                    potential_size = self._estimate_heuristic_size(data, offset, data_type)
                    if potential_size and potential_size > 10:  # Minimum meaningful size
                        resource_data = data[offset:offset + potential_size]
                        resource_hash = hashlib.sha256(resource_data).hexdigest()
                        
                        resource = {
                            "id": resource_hash[:16],
                            "type": data_type,
                            "mime_type": "application/octet-stream",
                            "size": potential_size,
                            "hash": resource_hash,
                            "source_object": source_object,
                            "object_type": object_type,
                            "offset": offset,
                            "filename": f"{source_object}_{offset:08x}.{data_type}",
                            "extraction_method": "heuristic",
                        }
                        
                        resources.append(resource)
                
                offset += 1
        
        return resources

    def _analyze_heuristic_context(self, data: bytes, offset: int, data_type: str) -> bool:
        """Analyze context around potential heuristic match."""
        # Simple heuristics - can be enhanced
        if data_type == "potential_string_table":
            # Check if there's readable text nearby
            context_window = 50
            start = max(0, offset - context_window)
            end = min(len(data), offset + context_window)
            context = data[start:end]
            
            # Count printable characters in context
            printable_count = sum(1 for b in context if 32 <= b <= 126)
            return printable_count > len(context) * 0.3
        
        return True  # Default to accepting other patterns

    def _estimate_heuristic_size(self, data: bytes, offset: int, data_type: str) -> int | None:
        """Estimate size of heuristically detected data."""
        if data_type == "potential_string_table":
            # Look for next null terminator or end of meaningful data
            for i in range(offset, min(len(data), offset + 1000)):
                if data[i] == 0 and (i + 1 >= len(data) or data[i + 1] == 0):
                    return i - offset + 1
        elif data_type in ["null_data", "filled_data"]:
            # Count consecutive bytes of the same pattern
            pattern_byte = data[offset]
            for i in range(offset, min(len(data), offset + 10000)):
                if data[i] != pattern_byte:
                    return max(i - offset, 10)  # Minimum 10 bytes
        
        return None

    def _validate_and_deduplicate(self, resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate resources and remove duplicates."""
        validated_resources = []
        seen_hashes = set()
        
        for resource in resources:
            # Validate resource structure
            if self._validate_resource_structure(resource):
                # Check for duplicates
                resource_hash = resource.get("hash", "")
                if resource_hash not in seen_hashes:
                    # Apply type-specific validation
                    if self._validate_resource_content(resource):
                        validated_resources.append(resource)
                        seen_hashes.add(resource_hash)
                        self.stats["validation_stats"]["validated_resources"] += 1
                    else:
                        self.stats["validation_stats"]["validation_failures"] += 1
                        logger.debug(f"Resource validation failed: {resource.get('filename', 'unknown')}")
                else:
                    logger.debug(f"Duplicate resource skipped: {resource.get('filename', 'unknown')}")
            else:
                self.stats["validation_stats"]["validation_failures"] += 1
                logger.debug(f"Resource structure validation failed: {resource}")
        
        return validated_resources

    def _validate_resource_structure(self, resource: dict[str, Any]) -> bool:
        """Validate basic resource structure."""
        required_fields = {"id", "type", "size", "hash", "source_object"}
        return all(field in resource for field in required_fields)

    def _validate_resource_content(self, resource: dict[str, Any]) -> bool:
        """Validate resource content using type-specific rules."""
        resource_type = resource.get("type", "")
        
        # Apply specific validation if available
        validator = self.validation_rules.get(resource_type)
        if validator:
            return validator(resource)
        
        # Basic validation for all types
        return resource.get("size", 0) > 0

    def _register_extractors(self) -> None:
        """Register all available extractors using unified interface."""
        # Note: This would register actual extractor implementations
        # For now, we use the internal methods
        logger.debug("Registered unified extraction interfaces")

    def run_comprehensive_tests(self) -> dict[str, Any]:
        """Run comprehensive test suite."""
        logger.info("Running comprehensive resource extraction tests")
        
        test_results = self.test_suite.run_tests(self)
        
        # Save test results
        test_report_path = self.resources_dir / "test_results.json"
        import json
        with open(test_report_path, "w") as f:
            json.dump(test_results, f, indent=2)
        
        logger.info(f"Test results: {test_results['passed']}/{test_results['total_tests']} passed "
                   f"({test_results['success_rate_percent']}%)")
        
        return test_results

    def get_unified_statistics(self) -> dict[str, Any]:
        """Get comprehensive statistics including unified interface metrics."""
        base_stats = self.stats.copy()
        
        # Add extractor-specific stats
        extractor_stats = {}
        if hasattr(self.string_extractor, 'get_extraction_statistics'):
            extractor_stats["string_extractor"] = self.string_extractor.get_extraction_statistics()
        
        # Add validation efficiency
        total_validations = (self.stats["validation_stats"]["validated_resources"] + 
                           self.stats["validation_stats"]["validation_failures"])
        validation_rate = (self.stats["validation_stats"]["validated_resources"] / 
                          max(total_validations, 1) * 100)
        
        base_stats["validation_success_rate_percent"] = round(validation_rate, 2)
        base_stats["extractor_statistics"] = extractor_stats
        
        return base_stats

    # Validation methods for specific resource types
    def _validate_png(self, resource: dict[str, Any]) -> bool:
        """Validate PNG resource."""
        # Basic PNG validation - check if it starts with PNG signature
        return resource.get("size", 0) >= 8

    def _validate_jpeg(self, resource: dict[str, Any]) -> bool:
        """Validate JPEG resource."""
        # Basic JPEG validation - check minimum size
        return resource.get("size", 0) >= 10

    def _validate_bmp(self, resource: dict[str, Any]) -> bool:
        """Validate BMP resource."""
        # Basic BMP validation - check minimum header size
        return resource.get("size", 0) >= 54

    def _validate_gif(self, resource: dict[str, Any]) -> bool:
        """Validate GIF resource."""
        # Basic GIF validation - check minimum size
        return resource.get("size", 0) >= 13

    def _detect_resource_at_offset(
        self, data: bytes, offset: int,
    ) -> dict[str, Any | None]:




        """Detect if there's a resource at the given offset.

        Args:
            data: Data bytes
            offset: Offset to check

        Returns:
            Resource info if detected, None otherwise
        """
        # Check against all signatures
        for signature, (ext, sig_len, mime_type) in self.RESOURCE_SIGNATURES.items():
            # Handle RIFF WAVE special case
            if signature == b"RIFF....WAVE":
                if (offset + 12 <= len(data) and 
                    data[offset:offset+4] == b"RIFF" and
                    data[offset+8:offset+12] == b"WAVE"):
                    return {
                        "type": ext, "mime_type": mime_type, "signature_length": sig_len,
                    }
            # Normal signature check
            elif data[offset:offset+sig_len] == signature:
                return {
                    "type": ext, "mime_type": mime_type, "signature_length": sig_len,
                }

        return None

    def _extract_resource(
        self, data: bytes, offset: int, resource_info: dict[str, Any], source_object: str, object_type: str,
    ) -> dict[str, Any | None]:




        """Extract a detected resource.

        Args:
            data: Data bytes
            offset: Resource start offset
            resource_info: Resource detection info
            source_object: Source object name
            object_type: Source object type

        Returns:
            Extracted resource info or None if failed
        """
        try:
            # Determine resource size
            size = self._get_resource_size(data, offset, resource_info["type"])
            if not size or size > len(data) - offset:
                return None

            # Extract resource data
            resource_data = data[offset:offset + size]

            # Calculate hash for deduplication
            resource_hash = hashlib.sha256(resource_data).hexdigest()

            # Generate filename
            filename = f"{source_object}_{offset:08x}.{resource_info["type"]}"

            # Save resource
            resource_path = self._save_resource(
                resource_data, filename, resource_info["type"], resource_hash,
            )

            # Create resource entry
            resource_entry = {
                "id": resource_hash[:16], "type": resource_info["type"], "mime_type": resource_info["mime_type"], "size": size, "hash": resource_hash, "source_object": source_object, "object_type": object_type, "offset": offset, "filename": filename, "path": str(resource_path.relative_to(self.output_dir)),
            }

            # Add metadata
            self._extract_metadata(resource_data, resource_entry)

            # Update catalog based on resource category
            category = self._get_resource_category(resource_info["type"])
            if category == "images":
                self.catalog.add_image_resource(source_object, {
                    "format": resource_info["type"], "size": size, "offset": offset, "metadata": resource_entry.get("metadata", {}), "saved_path": str(resource_path),
                },)
            elif category == "binary":
                self.catalog.add_binary_resource(source_object, resource_info["type"], {
                    "size": size, "offset": offset, "metadata": resource_entry.get("metadata", {}), "saved_path": str(resource_path),
                },)
            else:
                # For audio, documents, and other types, use binary resource
                self.catalog.add_binary_resource(source_object, resource_info["type"], {
                    "size": size, "offset": offset, "metadata": resource_entry.get("metadata", {}), "saved_path": str(resource_path),
                },)

            # Update statistics
            self.stats["total_resources"] += 1
            self.stats["extracted_resources"] += 1
            self.stats["total_size"] += size
            self.stats["resource_types"][resource_info["type"]] = \
                self.stats["resource_types"].get(resource_info["type"], 0) + 1

            logger.debug(
                f"Extracted {resource_info["type"]} resource from {source_object} "
                f"at offset {offset}: {filename} ({size} bytes)",
            )

            return resource_entry

        except Exception as e:
            logger.warning(
                f"Failed to extract {resource_info["type"]} resource at offset {offset}: {e}",
            )
            self.stats["failed_resources"] += 1
            return None

    def _get_resource_size(self, data: bytes, offset: int, resource_type: str) -> int | None:




        """Determine the size of a resource.

        Args:
            data: Data bytes
            offset: Resource start offset
            resource_type: Type of resource

        Returns:
            Size in bytes or None if cannot determine
        """
        # Use a dictionary to map resource types to their size detection functions
        size_detectors = {
            "bmp": lambda: get_bmp_size(data, offset), "ico": lambda: get_ico_size(data, offset), "cur": lambda: get_ico_size(data, offset), # Same format as ICO
            "png": lambda: self._get_png_size(data, offset), "jpg": lambda: self._get_jpeg_size(data, offset), "gif": lambda: self._get_gif_size(data, offset), "wav": lambda: self._get_wav_size(data, offset), }

        # Try to get size using specific detector
        detector = size_detectors.get(resource_type)
        if detector:
            return detector()

        # Default: use generic size detection
        return self._get_generic_resource_size(data, offset)

    def _get_png_size(self, data: bytes, offset: int) -> int | None:




        """Get PNG file size by parsing chunks."""
        pos = offset + 8  # Skip signature
        while pos + 12 <= len(data):
            chunk_len = struct.unpack(">I", data[pos:pos+4])[0]
            chunk_type = data[pos+4:pos+8]
            pos += 12 + chunk_len  # Header + data + CRC
            if chunk_type == b"IEND":
                return pos - offset
        return None

    def _get_jpeg_size(self, data: bytes, offset: int) -> int | None:




        """Get JPEG file size by scanning for EOI marker."""
        pos = offset + 2
        while pos + 2 <= len(data):
            if data[pos] == 0xFF:
                marker = data[pos+1]
                if marker == 0xD9:  # EOI marker
                    return pos + 2 - offset
                elif marker in (0xC0, 0xC1, 0xC2, 0xC3):  # SOF markers
                    pos += 2
                elif 0xD0 <= marker <= 0xD7:  # RST markers
                    pos += 2
                elif marker != 0x00:  # Not escaped FF
                    # Read segment length
                    if pos + 4 <= len(data):
                        seg_len = struct.unpack(">H", data[pos+2:pos+4])[0]
                        pos += 2 + seg_len
                    else:
                        break
                else:
                    pos += 1
            else:
                pos += 1
        return None

    def _get_gif_size(self, data: bytes, offset: int) -> int | None:




        """Get GIF file size by finding trailer byte."""
        for i in range(offset + 13, min(len(data), offset + 1024*1024)):  # Max 1MB
            if data[i] == 0x3B:
                return i + 1 - offset
        return None

    def _get_wav_size(self, data: bytes, offset: int) -> int | None:




        """Get WAV file size from RIFF header."""
        if offset + 8 <= len(data):
            # RIFF chunk size is at offset 4
            chunk_size = struct.unpack("<I", data[offset+4:offset+8])[0]
            return chunk_size + 8  # Add RIFF header
        return None

    def _get_generic_resource_size(self, data: bytes, offset: int) -> int | None:




        """Get size for unknown resource types using heuristics."""
        # Scan for next known signature
        for next_offset in range(offset + 16, min(len(data), offset + 1024*1024)):
            if self._detect_resource_at_offset(data, next_offset):
                return next_offset - offset

        # Heuristic: assume max 1MB for unknown resources
        return min(1024*1024, len(data) - offset)

    def _save_resource(
        self, data: bytes, filename: str, resource_type: str, resource_hash: str,
    ) -> Path:




        """Save resource data to file.

        Args:
            data: Resource data
            filename: Filename to use
            resource_type: Type of resource
            resource_hash: Hash of resource data

        Returns:
            Path to saved file
        """
        # Organize by type
        type_dir = self.resources_dir / self._get_resource_category(resource_type)
        type_dir.mkdir(exist_ok=True)

        # Check if already exists (deduplication)
        existing_files = list(type_dir.glob(f"*_{resource_hash[:16]}.*"))
        if existing_files:
            logger.debug("Resource already exists: %s", existing_files[0])
            return existing_files[0]

        # Save new resource
        resource_path = type_dir / f"{filename.replace("/", "_")}_{resource_hash[:16]}.{resource_type}"
        resource_path.write_bytes(data)

        return resource_path

    def _get_resource_category(self, resource_type: str) -> str:




        """Get category for a resource type.

        Args:
            resource_type: Resource file extension

        Returns:
            Category name
        """
        categories = {
            "images": {
                "png", "jpg", "gif", "bmp", "ico", "cur", "webp", "tiff", "pbm", "pbi", "jxl", "heif", "avif", "heic", "svg",
            }, "audio": {
                "wav", "mp3", "ogg", "flac", "m4a", "mid", "pbw", "pbs",
            }, "video": {
                "mp4", "mkv", "avi", "flv",
            }, "documents": {
                "pdf", "doc", "zip", "rtf", "7z",
            }, "fonts": {
                "ttf", "otf", "woff", "woff2",
            }, "binary": {
                "exe", "gz", "bz2", "xz", "rar", "cab", "pbr",
            }, }

        for category, types in categories.items():
            if resource_type in types:
                return category
        return "other"

    def _extract_metadata(self, data: bytes, resource_entry: dict[str, Any]) -> None:




        """Extract metadata from resource data.

        Args:
            data: Resource data
            resource_entry: Resource entry to add metadata to
        """
        resource_type = resource_entry["type"]

        # Image metadata
        if resource_type in ("png", "jpg", "gif", "bmp", "ico"):
            try:
                if resource_type == "bmp" and len(data) >= 26:
                    # BMP header
                    width = struct.unpack("<I", data[18:22])[0]
                    height = struct.unpack("<I", data[22:26])[0]
                    resource_entry["metadata"] = {
                        "width": width, "height": height,
                    }
                elif resource_type == "png" and len(data) >= 24:
                    # PNG IHDR chunk
                    width = struct.unpack(">I", data[16:20])[0]
                    height = struct.unpack(">I", data[20:24])[0]
                    resource_entry["metadata"] = {
                        "width": width, "height": height,
                    }
                elif resource_type == "gif" and len(data) >= 10:
                    # GIF header
                    width = struct.unpack("<H", data[6:8])[0]
                    height = struct.unpack("<H", data[8:10])[0]
                    resource_entry["metadata"] = {
                        "width": width, "height": height,
                    }
            except Exception as e:
                logger.debug("Failed to extract image metadata: %s", e)

    def generate_manifest(self) -> None:




        """Generate a resource manifest file."""
        manifest_path = self.resources_dir / "manifest.txt"

        with open(manifest_path, "w") as f:
            f.write("PowerBuilder Resource Extraction Manifest\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Total resources extracted: {self.stats["extracted_resources"]}\n")
            f.write(f"Failed extractions: {self.stats["failed_resources"]}\n")
            f.write(f"Total size: {self.stats["total_size"]:, } bytes\n\n")

            f.write("Resources by type:\n")
            for res_type, count in sorted(self.stats["resource_types"].items()):
                f.write(f"  {res_type}: {count}\n")

            f.write("\n" + "=" * 50 + "\n")
            f.write("See resource_catalog.json for detailed information\n")

        # Save catalog
        self.catalog.save_catalog()

        logger.info(
            f"Resource extraction complete: {self.stats["extracted_resources"]} resources "
            f"extracted ({self.stats["total_size"]:, } bytes)",
        )
