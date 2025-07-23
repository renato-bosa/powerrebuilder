"""Validation component for extraction operations.

This component handles validation of inputs and outputs for the extraction process.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any

from src.contracts.extractors import IExtractionValidator

logger = logging.getLogger(__name__)


class ExtractionValidator(IExtractionValidator):
    """Validator for extraction inputs and outputs.
    
    This component ensures that input files are valid PBL/PBD files and that
    extraction results meet expected criteria.
    """
    
    # PBL/PBD file signatures
    FILE_SIGNATURES = {
        "pbl": [
            b"PBL\x00",
            b"PBL\x05", 
            b"PBL\x06",
            b"HDR*",  # PowerBuilder 6+ header
        ],
        "pbd": [
            b"PBD\x00",
            b"PBD\x05",
            b"PBD\x06", 
            b"HDR*",  # PowerBuilder 6+ header
        ],
    }
    
    # Maximum reasonable file size (500MB)
    MAX_FILE_SIZE = 500 * 1024 * 1024
    
    # Minimum file size (header + at least one entry)
    MIN_FILE_SIZE = 512
    
    def __init__(self):
        """Initialize the validator."""
        self._validation_cache: dict[Path, bool] = {}
    
    def validate_input_file(self, file_path: Path) -> bool:
        """Validate that input file is a valid PBL/PBD file.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check cache first
        if file_path in self._validation_cache:
            return self._validation_cache[file_path]
        
        try:
            # Basic file checks
            if not file_path.exists():
                logger.error("File does not exist: %s", file_path)
                return self._cache_result(file_path, False)
            
            if not file_path.is_file():
                logger.error("Path is not a file: %s", file_path)
                return self._cache_result(file_path, False)
            
            # Size checks
            file_size = file_path.stat().st_size
            if file_size < self.MIN_FILE_SIZE:
                logger.error("File too small (%d bytes): %s", file_size, file_path)
                return self._cache_result(file_path, False)
            
            if file_size > self.MAX_FILE_SIZE:
                logger.error("File too large (%d bytes): %s", file_size, file_path)
                return self._cache_result(file_path, False)
            
            # Check file extension
            ext = file_path.suffix.lower().lstrip(".")
            if ext not in self.FILE_SIGNATURES:
                logger.error("Unknown file extension: %s", ext)
                return self._cache_result(file_path, False)
            
            # Validate file signature
            with file_path.open("rb") as f:
                header = f.read(64)
                
            valid_signature = any(
                header.startswith(sig) for sig in self.FILE_SIGNATURES[ext]
            )
            
            if not valid_signature:
                logger.error("Invalid file signature for: %s", file_path)
                return self._cache_result(file_path, False)
            
            # Additional structure checks
            if not self._check_file_structure(file_path):
                logger.warning("File structure validation failed for: %s", file_path)
                # Don't fail completely, file might be corrupted but recoverable
            
            return self._cache_result(file_path, True)
            
        except Exception as e:
            logger.error("Error validating file %s: %s", file_path, e)
            return self._cache_result(file_path, False)
    
    def validate_extraction_result(
        self, output_dir: Path, expected_entries: list[str]
    ) -> dict[str, Any]:
        """Validate extraction results.
        
        Args:
            output_dir: Directory containing extracted files
            expected_entries: List of expected entry names
            
        Returns:
            Validation results with missing/extra entries
        """
        result = {
            "valid": True,
            "missing_entries": [],
            "extra_entries": [],
            "corrupted_entries": [],
            "statistics": {
                "expected_count": len(expected_entries),
                "found_count": 0,
                "valid_count": 0,
                "corrupted_count": 0,
            },
        }
        
        try:
            # Get all extracted files
            extracted_files = self._get_extracted_files(output_dir)
            extracted_names = {f.stem for f in extracted_files}
            
            # Convert expected entries to set
            expected_set = set(expected_entries)
            
            # Find missing entries
            result["missing_entries"] = list(expected_set - extracted_names)
            
            # Find extra entries
            result["extra_entries"] = list(extracted_names - expected_set)
            
            # Validate each extracted file
            for file_path in extracted_files:
                if not self._validate_extracted_file(file_path):
                    result["corrupted_entries"].append(file_path.name)
                    result["statistics"]["corrupted_count"] += 1
                else:
                    result["statistics"]["valid_count"] += 1
            
            # Update statistics
            result["statistics"]["found_count"] = len(extracted_files)
            
            # Determine overall validity
            result["valid"] = (
                len(result["missing_entries"]) == 0
                and len(result["corrupted_entries"]) == 0
            )
            
            # Add summary
            result["summary"] = self._generate_validation_summary(result)
            
        except Exception as e:
            logger.error("Error validating extraction results: %s", e)
            result["valid"] = False
            result["error"] = str(e)
        
        return result
    
    def validate_file_integrity(
        self, file_path: Path, expected_checksum: str | None = None
    ) -> bool:
        """Validate file integrity.
        
        Args:
            file_path: Path to file to validate
            expected_checksum: Expected checksum (optional)
            
        Returns:
            True if file is intact
        """
        try:
            if not file_path.exists():
                return False
            
            # Check file can be read
            with file_path.open("rb") as f:
                data = f.read()
            
            # Verify checksum if provided
            if expected_checksum:
                actual_checksum = hashlib.sha256(data).hexdigest()
                if actual_checksum != expected_checksum:
                    logger.error(
                        "Checksum mismatch for %s: expected %s, got %s",
                        file_path,
                        expected_checksum,
                        actual_checksum,
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Error validating file integrity for %s: %s", file_path, e)
            return False
    
    def validate_entry_header(self, header_data: bytes) -> bool:
        """Validate entry header structure.
        
        Args:
            header_data: Raw header bytes
            
        Returns:
            True if header is valid
        """
        if len(header_data) < 16:
            return False
        
        # Check for known header patterns
        # This is a simplified check - real implementation would be more thorough
        return True
    
    def _cache_result(self, file_path: Path, valid: bool) -> bool:
        """Cache validation result."""
        self._validation_cache[file_path] = valid
        return valid
    
    def _check_file_structure(self, file_path: Path) -> bool:
        """Perform deeper structure validation."""
        # This would check internal structures, but for now just return True
        # Real implementation would validate:
        # - Header structure
        # - Entry table
        # - Data blocks
        return True
    
    def _get_extracted_files(self, output_dir: Path) -> list[Path]:
        """Get all extracted files from output directory."""
        if not output_dir.exists():
            return []
        
        # Look for PowerBuilder source files
        extensions = [".sru", ".srw", ".srd", ".srm", ".sra", ".srf", ".src"]
        files = []
        
        for ext in extensions:
            files.extend(output_dir.glob(f"*{ext}"))
        
        return files
    
    def _validate_extracted_file(self, file_path: Path) -> bool:
        """Validate individual extracted file."""
        try:
            # Check file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return False
            
            # Check file size
            if file_path.stat().st_size == 0:
                return False
            
            # Try to read file
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                content = f.read(1024)  # Read first 1KB
                
            # Check for PowerBuilder markers
            pb_markers = ["forward", "global", "end forward", "$PBExport"]
            return any(marker in content for marker in pb_markers)
            
        except Exception as e:
            logger.warning("Error validating extracted file %s: %s", file_path, e)
            return False
    
    def _generate_validation_summary(self, result: dict[str, Any]) -> str:
        """Generate human-readable summary of validation results."""
        stats = result["statistics"]
        
        summary_parts = [
            f"Found {stats['found_count']} of {stats['expected_count']} expected files",
        ]
        
        if result["missing_entries"]:
            summary_parts.append(f"Missing: {len(result['missing_entries'])} files")
        
        if result["extra_entries"]:
            summary_parts.append(f"Extra: {len(result['extra_entries'])} files")
        
        if result["corrupted_entries"]:
            summary_parts.append(f"Corrupted: {stats['corrupted_count']} files")
        
        return "; ".join(summary_parts)