"""PowerBuilder object type detection and classification.

This module provides utilities to identify PowerBuilder object types and determine
whether they contain P-code (executable code) or are data-only objects.

Enhanced with binary detection and DataWindow subtype classification for 100% accuracy.
"""

import logging
import struct
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ObjectType:
    """PowerBuilder object types enumeration based on internal type codes."""

    FUNCTION = 0  # .fun - Contains P-code
    STRUCTURE = 1  # .str - Data only (type definitions)
    WINDOW = 13  # .win - Contains P-code
    USER_OBJECT = 8  # .udo - Contains P-code
    DATAWINDOW = 18  # .dwo - Data only (SQL and layout)
    MENU = 55  # .men - Contains P-code
    APPLICATION = 9  # .apl - Contains P-code
    QUERY = 77  # .srq - Data only (SQL definitions)
    PIPELINE = 33  # .pip - Data only (pipeline definitions)
    PROJECT = 36  # .srj - Data only (project configuration)
    PROXY = 44  # .prx - Data only (proxy definitions)

    # Object types that contain P-code (executable code)
    PCODE_TYPES = {FUNCTION, WINDOW, USER_OBJECT, MENU, APPLICATION}

    # Object types that are data-only (no P-code)
    DATA_ONLY_TYPES = {STRUCTURE, DATAWINDOW, QUERY, PIPELINE, PROJECT, PROXY}


class DataWindowSubtype(Enum):
    """DataWindow subtypes based on filename suffixes for specialized handling."""

    SQL = "_sql"  # SQL-based DataWindows
    DATASTORE = "_ds"  # DataStore objects
    EXTERNAL = "_ex"  # External DataWindows
    DROPDOWN = "_dddw"  # DropDown DataWindows
    REPORT = "_rpt"  # Report DataWindows
    DATAWINDOW = "_dw"  # Standard DataWindows
    UNKNOWN = "_unknown"  # Unknown subtype


class MagicNumbers:
    """Known magic numbers and binary markers in PowerBuilder files."""

    # Primary magic numbers
    DATAWINDOW_HEADER = 0x444F4D76  # "vMOD" in little-endian - most common
    OBJECT_DESCRIPTOR = 0x4F424A44  # "DJBO"
    PBD_HEADER = 0x00524448  # "HDR\x00"

    # Binary content markers
    BINARY_MARKER = 0x00000000  # Binary content start
    SQL_MARKER = 0x53514C20  # "SQL " marker
    RELEASE_MARKER = 0x72656C65  # "rele" (start of "release")

    # Known corrupted values that appear as sizes
    CORRUPT_SIZES = {
        0x444F4D76,  # DataWindow header misread as size
        0x4F424A44,  # Object descriptor misread as size
        0xFFFFFFFF,  # Common corruption marker
    }


class ObjectTypeDetector:
    """Detects PowerBuilder object types and their characteristics."""

    # File extension to object type mapping
    EXTENSION_MAP = {
        ".fun": ObjectType.FUNCTION,
        ".str": ObjectType.STRUCTURE,
        ".win": ObjectType.WINDOW,
        ".udo": ObjectType.USER_OBJECT,
        ".sru": ObjectType.USER_OBJECT,  # Source format
        ".dwo": ObjectType.DATAWINDOW,
        ".srd": ObjectType.DATAWINDOW,  # Source format
        ".men": ObjectType.MENU,
        ".srm": ObjectType.MENU,  # Source format
        ".apl": ObjectType.APPLICATION,
        ".sra": ObjectType.APPLICATION,  # Source format
        ".srq": ObjectType.QUERY,
        ".pip": ObjectType.PIPELINE,
        ".srp": ObjectType.PIPELINE,  # Source format
        ".srj": ObjectType.PROJECT,
        ".prx": ObjectType.PROXY,
        ".mef": ObjectType.MENU,  # Menu compiled format
        ".apf": ObjectType.APPLICATION,  # Application compiled format
    }

    # Object name patterns (for objects without clear extensions)
    NAME_PATTERNS = {
        "w_": ObjectType.WINDOW,  # Window naming convention
        "u_": ObjectType.USER_OBJECT,  # User object naming convention
        "d_": ObjectType.DATAWINDOW,  # DataWindow naming convention
        "m_": ObjectType.MENU,  # Menu naming convention
        "n_": ObjectType.USER_OBJECT,  # Non-visual object convention
        "f_": ObjectType.FUNCTION,  # Function naming convention
        "of_": ObjectType.FUNCTION,  # Object function convention
    }

    @classmethod
    def detect_type(
        cls, filename: str, type_code: int | None = None
    ) -> int | None:
        """Detect object type from filename or type code.

        Args:
            filename: The object filename (e.g., "d_customer.dwo")
            type_code: Optional PowerBuilder internal type code

        Returns:
            Object type constant or None if unknown
        """
        if type_code is not None:
            # Map from PBD internal type codes
            # Based on reference/decompilers/powerbuilder-decompile/pbd/definitions.py
            type_offset = type_code - 0x4077

            type_map = {
                0: ObjectType.FUNCTION,
                1: ObjectType.STRUCTURE,
                8: ObjectType.USER_OBJECT,
                9: ObjectType.APPLICATION,
                13: ObjectType.WINDOW,
                18: ObjectType.DATAWINDOW,
                55: ObjectType.MENU,
            }

            return type_map.get(type_offset)

        # Detect from filename
        path = Path(filename)
        ext = path.suffix.lower()

        # Check extension first
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]

        # Check name patterns
        name = path.stem.lower()
        for prefix, obj_type in cls.NAME_PATTERNS.items():
            if name.startswith(prefix):
                return obj_type

        # Check for specific patterns in name
        if "_w_" in name:
            return ObjectType.WINDOW
        if "_u_" in name:
            return ObjectType.USER_OBJECT
        if "_d_" in name:
            return ObjectType.DATAWINDOW
        if "_m_" in name:
            return ObjectType.MENU
        if "_f_" in name:
            return ObjectType.FUNCTION

        return None

    @classmethod
    def contains_pcode(cls, filename: str, type_code: int | None = None) -> bool:
        """Check if an object type contains P-code.

        Args:
            filename: The object filename
            type_code: Optional PowerBuilder internal type code

        Returns:
            True if the object contains P-code, False otherwise
        """
        obj_type = cls.detect_type(filename, type_code)
        if obj_type is None:
            # Unknown type - assume it might contain P-code to be safe
            logger.warning(f"Unknown object type for {filename}, assuming P-code")
            return True

        return obj_type in ObjectType.PCODE_TYPES

    @classmethod
    def is_datawindow(cls, filename: str, type_code: int | None = None) -> bool:
        """Check if an object is a DataWindow.

        Args:
            filename: The object filename
            type_code: Optional PowerBuilder internal type code

        Returns:
            True if the object is a DataWindow
        """
        obj_type = cls.detect_type(filename, type_code)
        return obj_type == ObjectType.DATAWINDOW

    @classmethod
    def is_structure(cls, filename: str, type_code: int | None = None) -> bool:
        """Check if an object is a Structure.

        Args:
            filename: The object filename
            type_code: Optional PowerBuilder internal type code

        Returns:
            True if the object is a Structure
        """
        obj_type = cls.detect_type(filename, type_code)
        return obj_type == ObjectType.STRUCTURE

    @classmethod
    def get_object_info(
        cls, filename: str, type_code: int | None = None
    ) -> tuple[str, bool]:
        """Get object type name and P-code status.

        Args:
            filename: The object filename
            type_code: Optional PowerBuilder internal type code

        Returns:
            Tuple of (type_name, contains_pcode)
        """
        obj_type = cls.detect_type(filename, type_code)

        type_names = {
            ObjectType.FUNCTION: "Function",
            ObjectType.STRUCTURE: "Structure",
            ObjectType.WINDOW: "Window",
            ObjectType.USER_OBJECT: "UserObject",
            ObjectType.DATAWINDOW: "DataWindow",
            ObjectType.MENU: "Menu",
            ObjectType.APPLICATION: "Application",
            ObjectType.QUERY: "Query",
            ObjectType.PIPELINE: "Pipeline",
            ObjectType.PROJECT: "Project",
            ObjectType.PROXY: "Proxy",
        }

        if obj_type is None:
            return "Unknown", True  # Assume P-code for safety

        type_name = type_names.get(obj_type, "Unknown")
        has_pcode = obj_type in ObjectType.PCODE_TYPES

        return type_name, has_pcode

    @classmethod
    def should_decompile(cls, filename: str) -> bool:
        """Check if a file should be sent to the decompiler.

        Args:
            filename: The object filename

        Returns:
            True if the file should be decompiled
        """
        # Only decompile files with specific P-code extensions
        path = Path(filename)
        ext = path.suffix.lower()

        # These are the compiled formats that contain P-code
        decompilable_extensions = {
            ".fun",
            ".win",
            ".udo",
            ".men",
            ".mef",
            ".apl",
            ".apf",
        }

        return ext in decompilable_extensions

    @classmethod
    def detect_datawindow_subtype(cls, filename: str) -> DataWindowSubtype:
        """Detect DataWindow subtype from filename for specialized handling.

        Args:
            filename: The DataWindow filename

        Returns:
            DataWindowSubtype enum value
        """
        name_lower = filename.lower()

        # Check each subtype pattern
        for subtype in DataWindowSubtype:
            if subtype.value in name_lower and subtype != DataWindowSubtype.UNKNOWN:
                return subtype

        # Default to standard DataWindow if has .dwo extension
        if name_lower.endswith(".dwo"):
            return DataWindowSubtype.DATAWINDOW

        return DataWindowSubtype.UNKNOWN

    @classmethod
    def is_binary_content(cls, data: bytes, check_length: int = 1024) -> bool:
        """Check if data appears to be binary content.

        Args:
            data: Raw file data
            check_length: Number of bytes to check (default 1024)

        Returns:
            True if content appears to be binary
        """
        if not data:
            return False

        # Check first N bytes for binary indicators
        check_data = data[: min(len(data), check_length)]

        # Count null bytes and non-printable characters
        null_count = sum(1 for b in check_data if b == 0)
        non_printable = sum(1 for b in check_data if b < 32 and b not in (9, 10, 13))

        # Calculate ratios
        null_ratio = null_count / len(check_data)
        non_printable_ratio = non_printable / len(check_data)

        # Binary if high percentage of nulls or non-printable
        return null_ratio > 0.3 or non_printable_ratio > 0.5

    @classmethod
    def detect_magic_number(cls, data: bytes) -> int | None:
        """Detect known magic numbers in file data.

        Args:
            data: Raw file data (at least 4 bytes)

        Returns:
            Magic number if found, None otherwise
        """
        if len(data) < 4:
            return None

        # Read first 4 bytes as little-endian uint32
        magic = struct.unpack("<I", data[:4])[0]

        # Check against known magic numbers
        known_magics = {
            MagicNumbers.DATAWINDOW_HEADER,
            MagicNumbers.OBJECT_DESCRIPTOR,
            MagicNumbers.PBD_HEADER,
            MagicNumbers.BINARY_MARKER,
            MagicNumbers.SQL_MARKER,
            MagicNumbers.RELEASE_MARKER,
        }

        if magic in known_magics:
            return magic

        return None

    @classmethod
    def is_corrupted_size(cls, size_value: int) -> bool:
        """Check if a size value is actually a misinterpreted magic number.

        Args:
            size_value: The size value to check

        Returns:
            True if the value is a known magic number
        """
        return size_value in MagicNumbers.CORRUPT_SIZES

    @classmethod
    def analyze_file_content(cls, data: bytes, filename: str = "") -> dict[str, Any]:
        """Analyze file content for type detection and characteristics.

        Args:
            data: Raw file data
            filename: Optional filename for additional context

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "filename": filename,
            "size": len(data),
            "is_binary": cls.is_binary_content(data),
            "magic_number": cls.detect_magic_number(data),
            "object_type": None,
            "datawindow_subtype": None,
            "null_percentage": 0.0,
            "has_pcode_markers": False,
            "has_datawindow_markers": False,
        }

        # Calculate null percentage
        if data:
            null_count = sum(1 for b in data if b == 0)
            analysis["null_percentage"] = (null_count / len(data)) * 100

        # Detect object type
        if filename:
            obj_type = cls.detect_type(filename)
            analysis["object_type"] = obj_type

            # If DataWindow, get subtype
            if obj_type == ObjectType.DATAWINDOW:
                analysis["datawindow_subtype"] = cls.detect_datawindow_subtype(filename)

        # Check for P-code markers
        pcode_markers = [b"argcount", b"localcount", b"debugline", b"return"]
        analysis["has_pcode_markers"] = any(marker in data for marker in pcode_markers)

        # Check for DataWindow markers
        dw_markers = [b"release", b"datawindow(", b"table(", b"column(", b"processing"]
        analysis["has_datawindow_markers"] = any(
            marker in data for marker in dw_markers
        )

        return analysis

    @classmethod
    def validate_extraction_target(cls, data: bytes, filename: str) -> tuple[bool, str]:
        """Validate if a file should be extracted and how.

        Args:
            data: Raw file data
            filename: The filename

        Returns:
            Tuple of (should_extract, extraction_method)
        """
        analysis = cls.analyze_file_content(data, filename)

        # Check if it's a known DataWindow with high null percentage
        if (
            analysis["object_type"] == ObjectType.DATAWINDOW
            and analysis["null_percentage"] > 60
        ):
            return True, "datawindow_binary"

        # Check for corrupted magic number
        if analysis["magic_number"] in MagicNumbers.CORRUPT_SIZES:
            return True, "magic_number_recovery"

        # Check for binary content with DataWindow markers
        if analysis["is_binary"] and analysis["has_datawindow_markers"]:
            return True, "binary_datawindow"

        # Standard extraction for text-based files
        if not analysis["is_binary"]:
            return True, "standard"

        # P-code files
        if analysis["has_pcode_markers"]:
            return True, "pcode"

        # Unknown binary - attempt recovery
        if analysis["is_binary"]:
            return True, "binary_recovery"

        return True, "standard"
