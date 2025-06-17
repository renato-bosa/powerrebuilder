"""Enhanced P-code detector with better boundary detection.

This module provides improved P-code detection that can identify
the actual executable code regions within PowerBuilder objects.
"""

import logging
import math
from collections import Counter

logger = logging.getLogger(__name__)


class PCodeRegion:
    """Represents a detected P-code region."""

    def __init__(self, offset: int, length: int, confidence: float = 1.0) -> None:
        self.offset = offset
        self.length = length
        self.confidence = confidence
        self.instructions = []

    def __repr__(self) -> str:
        return f"<PCodeRegion offset=0x{self.offset:04x} length={self.length} confidence={self.confidence:.2f}>"


class EnhancedPCodeDetectorV2:
    """Enhanced P-code detector that finds actual code regions."""

    # Known P-code opcodes from the YAML definitions
    VALID_OPCODES = {
        0x00,  # RETURN
        0x01,  # ADD
        0x02,  # SUB
        0x03,  # MULT
        0x04,  # DIV
        0x05,  # MOD
        0x06,  # NEGATE
        0x07,  # POWER
        0x08,  # EQ
        0x09,  # NE
        0x0A,  # GT
        0x0B,  # LT
        0x0C,  # GE
        0x0D,  # LE
        0x0E,  # AND
        0x0F,  # OR
        0x10,  # NOT
        0x11,  # CAT
        0x14,  # PUSH_CONST_UINT
        0x15,  # PUSH_CONST_INT
        0x16,  # PUSH_CONST_ULONG
        0x17,  # PUSH_CONST_LONG
        0x18,  # PUSH_CONST_REAL
        0x19,  # PUSH_CONST_DOUBLE
        0x1A,  # PUSH_CONST_DEC
        0x1D,  # PUSH_CONST_NULL
        0x1E,  # PUSH_CONST_REF
        0x1F,  # JUMP
        0x20,  # JUMPTRUE
        0x21,  # JUMPFALSE
        0x23,  # DUP
        0x24,  # POP
        0x25,  # CALL
        0x26,  # RETURN_SUB
        0x27,  # PUSH_ARG
        0x28,  # PUSH_LOCAL_VAR
        0x29,  # GLOBFUNCCALL
        0x2A,  # CALL_SUPER
        0x32,  # PUSH_INSTANCE_VAR
        0x33,  # PUSH_SHARED_VAR
        0x34,  # PUSH_GLOBAL_VAR
        0x35,  # PUSH_LOCAL_REF
        0x38,  # POP_INSTANCE_VAR
        0x39,  # POP_SHARED_VAR
        0x3A,  # POP_GLOBAL_VAR
        0x4A,  # STORE_RETURN_VAL
        0x65,  # PUSH_LVALUE_INT
        0x94,  # EVENTCALL
        0x9C,  # CNV_INT_TO_UINT
        0x9E,  # CNV_UINT_TO_INT
        0xA2,  # CNV_LONG_TO_ULONG
        0xA3,  # CNV_ULONG_TO_LONG
        0xA6,  # CNV_INT_TO_LONG
        0xA7,  # CNV_UINT_TO_ULONG
        0xB0,  # CNV_INT_TO_REAL
        0xB5,  # CNV_LONG_TO_DOUBLE
        0xB8,  # CNV_ULONG_TO_DOUBLE
        0xBA,  # CNV_REAL_TO_DOUBLE
        0xBE,  # CNV_DOUBLE_TO_REAL
        0xBF,  # CNV_INT_TO_DOUBLE
        0xC0,  # CNV_INT_TO_DEC
        0xC3,  # CNV_LONG_TO_DEC
        0xC8,  # CNV_REAL_TO_DEC
        0xC9,  # CNV_DOUBLE_TO_DEC
        0xE0,  # DBSTART
        0xE1,  # DBFETCH
        0xE2,  # DBCOMMIT
        0xE3,  # DBROLLBACK
        # Extended opcodes for arithmetic
        0xF0,  # SUB_UINT
        0xF1,  # SUB_INT
        0xF2,  # SUB_ULONG
        0xF3,  # SUB_LONG
        0xF4,  # SUB_FLOAT
        0xF5,  # SUB_DOUBLE
        0xF6,  # MULT_UINT
        0xF7,  # MULT_INT
        0xF8,  # MULT_ULONG
        0xF9,  # MULT_LONG
        0xFA,  # MULT_FLOAT
        0xFB,  # MULT_DOUBLE
        0xFC,  # MULT_DEC
        0xFD,  # DIV_UINT
        0xFE,  # DIV_INT
        0xFF,  # DIV_ULONG
    }

    # Opcodes that commonly start functions
    FUNCTION_START_OPCODES = {
        0x27,  # PUSH_ARG (getting function arguments)
        0x32,  # PUSH_INSTANCE_VAR
        0x1F,  # JUMP (sometimes functions start with a jump)
        0x00,  # RETURN (empty functions)
        0x15,  # PUSH_CONST_INT
        0x14,  # PUSH_CONST_UINT
    }

    # Opcodes that commonly end functions
    FUNCTION_END_OPCODES = {
        0x00,  # RETURN
        0x26,  # RETURN_SUB
    }

    @classmethod
    def find_pcode_regions(cls, data: bytes, object_type: str) -> list[PCodeRegion]:
        """Find all P-code regions in the object data.

        Args:
            data: Raw object data
            object_type: Type of object (function, window, etc.)

        Returns:
            List of detected P-code regions
        """
        regions = []

        # Log file characteristics for debugging
        cls._log_data_characteristics(data, object_type)

        # Skip initial header based on object type
        if object_type == "function":
            # Functions typically have metadata at the beginning
            start_offset = cls._find_first_code_offset(data, 0x100)
        else:
            start_offset = cls._find_first_code_offset(data, 0x200)

        if start_offset < 0:
            logger.warning("No P-code regions found")
            return regions

        # Scan for code regions, skipping null-heavy areas
        current_offset = start_offset
        while current_offset < len(data) - 10:
            # Skip large null sequences (padding)
            null_seq_len = cls._count_null_sequence(data, current_offset)
            if null_seq_len > 50:  # Skip large null sequences
                logger.debug(
                    f"Skipping {null_seq_len} null bytes at offset 0x{current_offset:04x}"
                )
                current_offset += null_seq_len
                continue

            # Look for a function start
            if cls._looks_like_function_start(data, current_offset):
                # Find the end of this function
                end_offset = cls._find_function_end(data, current_offset)

                if end_offset > current_offset:
                    length = end_offset - current_offset
                    region_data = data[current_offset:end_offset]

                    # Skip regions that are mostly null bytes
                    if cls._is_mostly_nulls(region_data):
                        logger.debug(
                            f"Skipping null-heavy region at 0x{current_offset:04x}"
                        )
                        current_offset = end_offset
                        continue

                    # Validate the region
                    confidence = cls._calculate_region_confidence(region_data)

                    if confidence > 0.3:  # Lower threshold for mixed-content files
                        region = PCodeRegion(current_offset, length, confidence)
                        regions.append(region)
                        logger.debug("Found P-code region: %s", region)

                    current_offset = end_offset
                else:
                    current_offset += 1
            else:
                current_offset += 1

        return regions

    @classmethod
    def _find_first_code_offset(cls, data: bytes, start_search: int) -> int:
        """Find the first likely P-code instruction."""
        for i in range(start_search, min(len(data) - 10, start_search + 0x1000)):
            if data[i] in cls.FUNCTION_START_OPCODES:
                # Verify it's not in the middle of data
                if cls._looks_like_valid_instruction_sequence(data, i):
                    return i
        return -1

    @classmethod
    def _looks_like_function_start(cls, data: bytes, offset: int) -> bool:
        """Check if this offset looks like the start of a function."""
        if offset >= len(data):
            return False

        # Check for function start patterns
        opcode = data[offset]

        # Common function starts
        if opcode in cls.FUNCTION_START_OPCODES:
            return True

        # Check for jump table at start (common pattern)
        if opcode == 0x1F:  # JUMP
            return True

        return False

    @classmethod
    def _find_function_end(cls, data: bytes, start_offset: int) -> int:
        """Find the end of a function starting at the given offset."""
        offset = start_offset
        consecutive_returns = 0
        last_valid_instruction = start_offset

        while offset < len(data) - 10:
            opcode = data[offset]

            # Track RETURN instructions
            if opcode == 0x00:  # RETURN
                consecutive_returns += 1
                # Multiple consecutive RETURNs usually indicate end of code
                if consecutive_returns > 3:
                    # Check if followed by non-code data
                    if not cls._looks_like_valid_instruction_sequence(data, offset + 1):
                        return last_valid_instruction + 1
            else:
                consecutive_returns = 0

            # Check if this looks like a valid instruction
            if opcode in cls.VALID_OPCODES:
                last_valid_instruction = offset
                # Skip to next instruction (simplified - assumes 1 byte for now)
                offset += 1
            # Hit non-code data
            elif offset - start_offset > 10:  # At least some code found
                return last_valid_instruction + 1
            else:
                return start_offset

        return min(last_valid_instruction + 1, len(data))

    @classmethod
    def _looks_like_valid_instruction_sequence(cls, data: bytes, offset: int) -> bool:
        """Check if this looks like a valid sequence of instructions."""
        valid_count = 0
        invalid_count = 0

        for i in range(min(10, len(data) - offset)):
            if offset + i < len(data):
                if data[offset + i] in cls.VALID_OPCODES:
                    valid_count += 1
                else:
                    invalid_count += 1

        return valid_count > invalid_count

    @classmethod
    def _calculate_region_confidence(cls, region_data: bytes) -> float:
        """Calculate confidence that this region contains valid P-code."""
        if len(region_data) == 0:
            return 0.0

        valid_opcodes = 0
        total_bytes = len(region_data)

        for byte in region_data:
            if byte in cls.VALID_OPCODES:
                valid_opcodes += 1

        # Basic confidence based on valid opcode ratio
        confidence = valid_opcodes / total_bytes

        # Boost confidence if it starts with a function start opcode
        if region_data[0] in cls.FUNCTION_START_OPCODES:
            confidence = min(1.0, confidence + 0.2)

        # Boost confidence if it ends with RETURN
        if region_data[-1] == 0x00:
            confidence = min(1.0, confidence + 0.1)

        return confidence

    @classmethod
    def is_pcode_object(cls, object_name: str) -> bool:
        """Check if an object type typically contains P-code.

        Args:
            object_name: Name of the object (with extension)

        Returns:
            True if the object type typically has P-code
        """
        name_lower = object_name.lower()

        # Object types that contain P-code
        pcode_extensions = [
            ".fun",  # Functions
            ".sru",  # User objects
            ".srw",  # Windows
            ".srm",  # Menus
            ".sra",  # Applications
            ".str",  # Structures (sometimes have constructor/destructor)
            ".men",  # Old menu format
            ".win",  # Old window format
            ".udo",  # Old user object format
        ]

        return any(name_lower.endswith(ext) for ext in pcode_extensions)

    @classmethod
    def _log_data_characteristics(cls, data: bytes, object_type: str) -> None:
        """Log characteristics of the data for debugging.

        Args:
            data: Raw object data
            object_type: Type of object being processed
        """
        if len(data) == 0:
            return

        null_count = data.count(0)
        null_ratio = null_count / len(data)
        entropy = cls._calculate_entropy(data)
        unique_bytes = len(set(data))

        # Check for DataWindow keywords
        datawindow_keywords = cls._count_datawindow_keywords(data)

        logger.debug("Processing %s object:", object_type)
        logger.debug("  Size: %s bytes", len(data))
        logger.debug("  Null ratio: %.1f%%", null_ratio * 100)
        logger.debug("  Entropy: %.2f bits/byte", entropy)
        logger.debug("  Unique bytes: %s", unique_bytes)
        if datawindow_keywords > 0:
            logger.debug("  DataWindow keywords: %s", datawindow_keywords)

    @classmethod
    def _count_null_sequence(cls, data: bytes, start_offset: int) -> int:
        """Count consecutive null bytes starting at offset.

        Args:
            data: Input data
            start_offset: Starting position

        Returns:
            Number of consecutive null bytes
        """
        count = 0
        for i in range(start_offset, len(data)):
            if data[i] == 0:
                count += 1
            else:
                break
        return count

    @classmethod
    def _is_mostly_nulls(cls, data: bytes, threshold: float = 0.7) -> bool:
        """Check if data is mostly null bytes.

        Args:
            data: Input data
            threshold: Null ratio threshold (default 70%)

        Returns:
            True if data is mostly nulls
        """
        if len(data) == 0:
            return True

        null_count = data.count(0)
        null_ratio = null_count / len(data)
        return null_ratio > threshold

    @classmethod
    def _count_datawindow_keywords(cls, data: bytes) -> int:
        """Count DataWindow-related keywords in data.

        Args:
            data: Input data

        Returns:
            Number of DataWindow keywords found
        """
        try:
            # Try to decode as text
            text_data = data.decode("utf-16le", errors="ignore").lower()
        except UnicodeDecodeError:
            try:
                text_data = data.decode("utf-8", errors="ignore").lower()
            except UnicodeDecodeError:
                text_data = data.decode("latin-1", errors="ignore").lower()

        datawindow_keywords = [
            "column",
            "table",
            "retrieve",
            "datawindow",
            "control",
            "header",
            "detail",
            "footer",
            "border",
            "background",
            "band",
        ]

        return sum(1 for keyword in datawindow_keywords if keyword in text_data)

    @classmethod
    def _calculate_entropy(cls, data: bytes) -> float:
        """Calculate Shannon entropy of data.

        Args:
            data: Input data

        Returns:
            Shannon entropy in bits/byte
        """
        if len(data) == 0:
            return 0.0

        # Count frequency of each byte value
        counter = Counter(data)

        # Calculate entropy
        entropy = 0.0
        for count in counter.values():
            probability = count / len(data)
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy

    @classmethod
    def get_primary_pcode_region(
        cls, data: bytes, object_type: str
    ) -> tuple[bytes, int] | None:
        """Get the primary P-code region for decoding.

        Args:
            data: Raw object data
            object_type: Type of object

        Returns:
            Tuple of (pcode_data, offset) or None
        """
        # Check for PowerBuilder export format header first
        if data.startswith(b"HA$PBExportHeader$"):
            # This is a PowerBuilder export format file
            # The format is:
            # HA$PBExportHeader$<objectname>\n
            # $PBExportComments$\n
            # <binary p-code data>

            # Find the first newline (end of header line)
            first_newline = data.find(b"\n")
            if first_newline < 0:
                logger.warning("Malformed PowerBuilder export header - no newline")
                return None

            # Find the second newline (end of comments line)
            second_newline = data.find(b"\n", first_newline + 1)
            if second_newline < 0:
                logger.warning(
                    "Malformed PowerBuilder export header - no second newline"
                )
                return None

            # P-code starts after the second newline
            pcode_start = second_newline + 1

            # The P-code section is the rest of the file
            pcode_data = data[pcode_start:]

            logger.debug(
                f"Export format detected. P-code starts at offset {pcode_start} (0x{pcode_start:04x})"
            )
            return pcode_data, pcode_start

        # For non-export format, use region detection
        regions = cls.find_pcode_regions(data, object_type)

        if not regions:
            return None

        # Return the largest region with highest confidence
        best_region = max(regions, key=lambda r: r.length * r.confidence)

        pcode_data = data[best_region.offset : best_region.offset + best_region.length]
        return pcode_data, best_region.offset
