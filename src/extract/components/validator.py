"""Validation component for extraction operations.

This component handles validation of inputs and outputs for the extraction process.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any
from src.contracts.extractors import IExtractionValidator

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

    def __init__(self) -> None:
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
            pass
        return self._validation_cache[file_path]

        try:
        # Basic checks
        if not file_path.exists():
        logger.error("File does not exist: %s", file_path)
        return self._cache_result(file_path, False)

        if not file_path.is_file():
        logger.error("Path is not a file: %s", file_path)
        return self._cache_result(file_path, False)

        # Check file extension
        extension = file_path.suffix.lower()
        if extension not in [".pbl", ".pbd"]:
        logger.warning(
        "File has unexpected extension: %s (expected .pbl or .pbd)",
        extension,
        )
        # Don't fail here, check signature instead

        # Check file size
        file_size = file_path.stat().st_size
        if file_size < self.MIN_FILE_SIZE:
        logger.error(
        "File too small: %d bytes (minimum: %d)",
        file_size,
        self.MIN_FILE_SIZE,
        )
        return self._cache_result(file_path, False)

        if file_size > self.MAX_FILE_SIZE:
        logger.warning(
        "File unusually large: %d bytes (maximum: %d)",
        file_size,
        self.MAX_FILE_SIZE,
        )
        # Don't fail, just warn

        # Check file signature
        if not self._check_file_signature(file_path):
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
        expected_checksum: Optional expected checksum (SHA-256)

        Returns:
        True if file integrity is valid
    """
        try:
        if not file_path.exists():
        logger.error("File does not exist: %s", file_path)
        return False

        # Calculate checksum
        actual_checksum = self._calculate_checksum(file_path)

        # If no expected checksum, just verify we could read the file
        if expected_checksum is None:
        return actual_checksum is not None

        # Compare checksums
        if actual_checksum != expected_checksum:
        logger.error(
        "Checksum mismatch for %s: expected=%s, actual=%s",
        file_path,
        expected_checksum,
        actual_checksum,
        )
        return False

        return True

        except Exception as e:
        logger.error("Error validating file integrity for %s: %s", file_path, e)
        return False

    def _cache_result(self, file_path: Path, result: bool) -> bool:
    """Cache validation result."""
        self._validation_cache[file_path] = result
        return result

    def _check_file_signature(self, file_path: Path) -> bool:
    """Check if file has valid PBL/PBD signature."""
        try:
        with file_path.open("rb") as f:
        # Read first 4 bytes
        signature = f.read(4)

        # Check against known signatures
        for sig_list in self.FILE_SIGNATURES.values():
        if signature in sig_list:
        return True

        # Check for Unicode variants
        if signature.startswith((b"PBL", b"PBD")):
        # Might be a newer version
        logger.debug("Found PBL/PBD signature variant: %s", signature.hex())
        return True

        return False

        except Exception as e:
        logger.error("Error checking file signature: %s", e)
        return False

    def _check_file_structure(self, file_path: Path) -> bool:
    """Perform basic structure validation."""
        try:
        with file_path.open("rb") as f:
        # Read header area
        header_data = f.read(512)

        if len(header_data) < 512:
        return False

        # Look for structure markers
        # Check for NOD offset (usually at offset 0x10 or 0x14)
        try:
        # Try different offset positions
        for offset_pos in [0x10, 0x14, 0x18]:
        if offset_pos + 4 <= len(header_data):
        nod_offset = int.from_bytes(
        header_data[offset_pos: offset_pos + 4], byteorder="little"
        )
        # Sanity check
        if 0 < nod_offset < file_path.stat().st_size:
        return True
        except Exception:
        pass

        # If we can't find valid structure, it might be corrupted
        return False

        except Exception as e:
        logger.error("Error checking file structure: %s", e)
        return False

    def _get_extracted_files(self, output_dir: Path) -> list[Path]:
    """Get all extracted files from output directory."""
        extracted_files = []

        # Look for common extracted file patterns
        patterns = ["*.fun", "*.sru", "*.srd", "*.srw", "*.dat"]

        for pattern in patterns:
        extracted_files.extend(output_dir.rglob(pattern))

        # Also check resources subdirectory
        resources_dir = output_dir / "resources"
        if resources_dir.exists():
        extracted_files.extend(resources_dir.rglob("*"))

        # Filter out directories
        return [f for f in extracted_files if f.is_file()]

    def _validate_extracted_file(self, file_path: Path) -> bool:
    """Validate a single extracted file."""
        try:
        # Check file exists and has content
        if not file_path.exists():
        return False
        return False

        file_size = file_path.stat().st_size
        if file_size == 0:
        logger.warning("Empty extracted file: %s", file_path)
        return False

        # Check file is readable
        try:
        with file_path.open("rb") as f:
        # Read first few bytes to ensure file is accessible
        f.read(min(1024, file_size))
        except Exception:
        return False

        # Additional validation based on file type
        if file_path.suffix == ".fun":
        return self._validate_fun_file(file_path)
        if file_path.suffix in [".sru", ".srw", ".srd"]:
        return self._validate_source_file(file_path)

        # Default: file exists and is readable
        return True

        except Exception as e:
        logger.error("Error validating extracted file %s: %s", file_path, e)
        return False

    def _validate_fun_file(self, file_path: Path) -> bool:
    """Validate a .fun (P-code) file."""
        try:
        with file_path.open("rb") as f:
        data = f.read(100)  # Read first 100 bytes

        # Check for P-code patterns
        # P-code files often have specific byte patterns
        if len(data) < 4:
        return False

        # Check for high null byte density (common in P-code)
        null_count = data.count(b"\x00")
        if null_count > len(data) * 0.3:  # More than 30% nulls:
        return True

        # Check for specific P-code markers
        if b"PBVM" in data or data.startswith(b"\x00\x00\x00\x00"):
        return True

        # Might still be valid
        return True

        except Exception:
        return False

    def _validate_source_file(self, file_path: Path) -> bool:
    """Validate a PowerBuilder source file."""
        try:
        with file_path.open(encoding="utf-8", errors="ignore") as f:
        content = f.read(1000)  # Read first 1000 chars

        # Check for PowerBuilder source markers
        pb_markers = [
        "$PBExportHeader$",
        "global type",
        "forward",
        "type variables",
        "end variables",
        ]

        for marker in pb_markers:
        if marker in content:
        return True

        # Might be a partial file
        return len(content) > 10

        except Exception:
        return False

    def _calculate_checksum(self, file_path: Path) -> str | None:
    """Calculate SHA-256 checksum of file."""
        try:
        sha256_hash = hashlib.sha256()

        with file_path.open("rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
        sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

        except Exception as e:
        logger.error("Error calculating checksum for %s: %s", file_path, e)
        return None

    def _generate_validation_summary(self, result: dict[str, Any]) -> str:
    """Generate a human-readable validation summary."""
        stats = result["statistics"]

        summary_parts = []

        # Overall status
        if result["valid"]:
        summary_parts.append("Extraction validation PASSED")
        else:
        summary_parts.append("Extraction validation FAILED")

        # Statistics
        summary_parts.append(
        f"Expected: {stats['expected_count']}, "
        f"Found: {stats['found_count']}, "
        f"Valid: {stats['valid_count']}"
        )

        # Issues
        if result["missing_entries"]:
        summary_parts.append(f"Missing {len(result['missing_entries'])} entries")

        if result["corrupted_entries"]:
        summary_parts.append(
        f"Corrupted {len(result['corrupted_entries'])} entries"
        )

        if result["extra_entries"]:
        summary_parts.append(f"Extra {len(result['extra_entries'])} entries")

        return "; ".join(summary_parts)

    def clear_cache(self) -> None:
    """Clear the validation cache."""
        self._validation_cache.clear()
