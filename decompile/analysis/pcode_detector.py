"""Enhanced P-code detection for PowerBuilder objects.

This module provides improved P-code detection that understands
PowerBuilder object structures better.
"""

from typing import Any, Dict, List, Optional, Union

import logging

logger = logging.getLogger(__name__)


class EnhancedPCodeDetector:
    """Enhanced P-code detector for PowerBuilder objects."""

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
    def find_pcode_in_function(cls, data: bytes) -> tuple[int, int]:
        """Find P-code in a PowerBuilder function object.

        PowerBuilder function format:
        1. Header/metadata
        2. Optional source code
        3. P-code section

        Args:
            data: Raw function data (from DAT blocks)

        Returns:
            Tuple of (offset, length) for P-code section, or (-1, 0) if not found
        """
        if len(data) < 16:
            return -1, 0

        # Check for PowerBuilder export format header
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
                return -1, 0

            # Find the second newline (end of comments line)
            second_newline = data.find(b"\n", first_newline + 1)
            if second_newline < 0:
                logger.warning(
                    "Malformed PowerBuilder export header - no second newline"
                )
                return -1, 0

            # P-code starts after the second newline
            pcode_start = second_newline + 1

            # The P-code section is the rest of the file
            pcode_length = len(data) - pcode_start

            logger.debug(
                f"Export format detected. P-code starts at offset {pcode_start} (0x{pcode_start:04x})"
            )
            return pcode_start, pcode_length

        # Strategy 1: Look for P-code header patterns
        # P-code often starts with specific patterns after metadata

        # Common P-code start patterns in functions
        PCODE_PATTERNS = [
            # Pattern: length prefix followed by instruction bytes
            b"\x00\x00\x00\x00",  # Null header
            b"\x04\x00",  # JUMP instruction (0x04)
            b"\x00\x00",  # RETURN at start (0x00)
            b"\x05\x00",  # DBSTART (0x05)
            b"\x29\x00",  # GLOBFUNCCALL (0x29)
            b"\x2c\x00",  # DOTFUNCCALL (0x2C)
        ]

        # Scan for P-code start
        pcode_start = -1
        for i in range(min(len(data) - 4, 1024)):  # Limit scan to first 1KB
            # Check if we have a potential P-code start

            # Method 1: Look for sequences of valid opcodes
            if cls._looks_like_pcode(data[i : i + 20]):
                logger.debug("Found P-code by opcode pattern at offset %s", i)
                pcode_start = i
                break

            # Method 2: Look for specific patterns
            for pattern in PCODE_PATTERNS:
                if data[i : i + len(pattern)] == pattern:
                    # Verify it's actually P-code by checking surrounding bytes
                    if cls._verify_pcode_context(data, i):
                        logger.debug(
                            f"Found P-code by pattern {pattern.hex()} at offset {i}"
                        )
                        pcode_start = i
                        break

            if pcode_start >= 0:
                break

        # Strategy 2: Look for transition from text to binary
        if pcode_start < 0:
            text_end = cls._find_text_to_binary_transition(data)
            if text_end > 0:
                logger.debug("Found P-code after text transition at offset %s", text_end)
                pcode_start = text_end

        if pcode_start < 0:
            logger.warning("Could not find P-code in function data")
            return -1, 0

        # Now find the end of executable P-code
        # Look for patterns that indicate end of code:
        # - Multiple RETURNs in a row
        # - Long sequences of 0x00 or 0xFF
        # - Invalid opcode sequences
        pcode_end = cls._find_pcode_end(data, pcode_start)

        return pcode_start, pcode_end - pcode_start

    @classmethod
    def _looks_like_pcode(cls, data: bytes) -> bool:
        """Check if data looks like P-code instructions."""
        if len(data) < 10:
            return False

        # P-code characteristics:
        # 1. Has valid opcodes (0x00-0xFF)
        # 2. Has reasonable instruction sequences
        # 3. Contains non-printable bytes

        # Count valid looking opcodes
        valid_opcodes = 0
        i = 0

        # Known valid opcodes (partial list)
        VALID_OPCODES = {
            0x00,  # RETURN
            0x01,  # STORE_RETURN_VAL
            0x02,  # JUMPTRUE
            0x03,  # JUMPFALSE
            0x04,  # JUMP
            0x05,  # DBSTART
            0x06,  # DBCOMMIT
            0x07,  # DBROLLBACK
            0x08,  # DBSTOP
            0x09,  # DBCLOSE
            0x0A,  # DBOPEN
            0x15,  # DBEXECUTEDYN
            0x29,  # GLOBFUNCCALL
            0x2C,  # DOTFUNCCALL
            0x32,  # PUSH_CONST_INT
            0x40,  # CNV_INT_TO_ULONG
            0xFF,  # DECR_LONG
        }

        while i < min(len(data), 10):
            if data[i] in VALID_OPCODES:
                valid_opcodes += 1
            i += 1

        # If we have several valid opcodes, it's likely P-code
        return valid_opcodes >= 3

    @classmethod
    def _verify_pcode_context(cls, data: bytes, offset: int) -> bool:
        """Verify that the context around offset looks like P-code."""
        # Check bytes before and after
        start = max(0, offset - 4)
        end = min(len(data), offset + 20)

        context = data[start:end]

        # Count non-printable bytes (P-code has many)
        non_printable = sum(1 for b in context if b < 32 or b > 126)

        # P-code should have significant non-printable content
        return non_printable > len(context) * 0.5

    @classmethod
    def _find_text_to_binary_transition(cls, data: bytes) -> int:
        """Find where text/metadata ends and binary P-code begins."""
        # Look for runs of printable ASCII followed by binary data

        in_text = True
        text_run = 0
        binary_run = 0

        for i in range(len(data)):
            if 32 <= data[i] <= 126 or data[i] in [
                9,
                10,
                13,
            ]:  # Printable or whitespace
                if in_text:
                    text_run += 1
                # Transition from binary back to text
                elif binary_run < 4:
                    # Short binary run, probably still in text
                    in_text = True
                    text_run = 1
                    binary_run = 0
            # Non-printable
            elif in_text and text_run > 20:
                # We've had a good run of text, now hitting binary
                in_text = False
                binary_run = 1

                # Check if this looks like P-code start
                if cls._looks_like_pcode(data[i : i + 20]):
                    return i
            elif not in_text:
                binary_run += 1

        return -1

    @classmethod
    def find_pcode_section(
        cls, data: bytes, object_type: str = "function"
    ) -> tuple[int, int]:
        """Main entry point for P-code detection.

        Args:
            data: Raw object data
            object_type: Type of object (function, window, etc.)

        Returns:
            Tuple of (offset, length) for P-code section, or (-1, 0) if not found
        """
        if object_type == "function":
            return cls.find_pcode_in_function(data)
        # For other object types, use the same detection method
        # (could be extended in the future for type-specific detection)
        return cls.find_pcode_in_function(data)

    def detect_pcode(self, data: bytes, object_name: str) -> "PCodeInfo":
        """Detect P-code in raw binary data.

        Args:
            data: Raw binary data from extracted file
            object_name: Name of the object

        Returns:
            PCodeInfo object with detection results
        """
        # Determine object type from name/extension
        object_type = "function"  # Default
        if object_name.lower().endswith(".str"):
            object_type = "structure"
        elif object_name.lower().endswith(".men"):
            object_type = "menu"

        # Find P-code section
        offset, length = self.find_pcode_section(data, object_type)

        # Create info object
        class PCodeInfo:
            def __init__(self) -> None:
                self.pcode_offset = offset
                self.pcode_length = length
                self.object_type = object_type
                self.confidence = "high" if offset >= 0 else "none"

        return PCodeInfo()

    @classmethod
    def _find_pcode_end(cls, data: bytes, start_offset: int) -> int:
        """Find the end of executable P-code.

        Args:
            data: Full data buffer
            start_offset: Where P-code starts

        Returns:
            Offset where P-code ends
        """
        # Start scanning from P-code start
        i = start_offset
        consecutive_returns = 0
        consecutive_nulls = 0
        consecutive_ff = 0
        last_valid_offset = start_offset

        while i < len(data):
            opcode = data[i] if i < len(data) else 0

            # Check for multiple RETURNs
            if opcode == 0x00:  # RETURN
                consecutive_returns += 1
                if consecutive_returns >= 3:
                    # Three or more RETURNs in a row - likely end of code
                    logger.debug(
                        f"Found {consecutive_returns} consecutive RETURNs at {i:04X}"
                    )
                    return last_valid_offset + 1
            else:
                if consecutive_returns > 0:
                    # Reset counter but remember we had RETURNs
                    last_valid_offset = i - 1
                consecutive_returns = 0

            # Check for padding patterns
            if opcode == 0x00:
                consecutive_nulls += 1
            else:
                consecutive_nulls = 0

            if opcode == 0xFF:
                consecutive_ff += 1
            else:
                consecutive_ff = 0

            # If we see long runs of padding, we're past code
            if consecutive_nulls >= 8 or consecutive_ff >= 8:
                logger.debug("Found padding at %04X", i)
                return last_valid_offset + 1

            # Try to decode instruction to advance properly
            # This is a simplified check - just advance by 1 for now
            # In a real implementation, we'd decode the full instruction
            i += 1

            # Update last valid position if this looks like real code
            if opcode not in {0, 255}:
                last_valid_offset = i

        # If we reached end of data, return full length
        return len(data)
