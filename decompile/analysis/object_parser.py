"""PowerBuilder object parser for extracting P-code from object data.

This module parses PowerBuilder object structures to extract the actual
P-code sections for decompilation.
"""

import logging
import struct

logger = logging.getLogger(__name__)


class PowerBuilderObject:
    """Represents a parsed PowerBuilder object."""

    def __init__(self, object_name: str, object_type: int) -> None:
        self.object_name = object_name
        self.object_type = object_type
        self.version = None
        self.flags = None
        self.metadata = {}
        self.strings = []
        self.pcode_offset = -1
        self.pcode_length = 0
        self.pcode_data = b""

    def __repr__(self) -> str:
        return f"<PowerBuilderObject {self.object_name} type=0x{self.object_type:04x}>"


class ObjectParser:
    """Parser for PowerBuilder object data structures."""

    # Object type constants (base is 0x4077)
    OBJECT_TYPE_FUNCTION = 0x4077  # .fun
    OBJECT_TYPE_WINDOW = 0x4084  # .win (0x4077 + 13)
    OBJECT_TYPE_USEROBJECT = 0x407F  # .udo (0x4077 + 8)
    OBJECT_TYPE_STRUCTURE = 0x4078  # .str (0x4077 + 1)
    OBJECT_TYPE_MENU = 0x40AE  # .men (0x4077 + 55)
    OBJECT_TYPE_DATAWINDOW = 0x4089  # .dwo (0x4077 + 18)
    OBJECT_TYPE_APPLICATION = 0x4080  # .apl (0x4077 + 9)

    @classmethod
    def parse_object(cls, data: bytes, object_name: str) -> PowerBuilderObject | None:
        """Parse a PowerBuilder object from binary data.

        Args:
            data: Raw object data (after export header if present)
            object_name: Name of the object

        Returns:
            PowerBuilderObject instance or None if parsing fails
        """
        if len(data) < 16:
            logger.error(f"Object data too small for {object_name}: {len(data)} bytes")
            return None

        try:
            # Skip export header if present
            offset = 0
            if data.startswith(b"HA$PBExportHeader$"):
                header_end = data.find(b"\n$PBExportComments$\n")
                if header_end >= 0:
                    offset = header_end + len(b"\n$PBExportComments$\n")
                else:
                    # Fallback: find second newline
                    first_nl = data.find(b"\n")
                    if first_nl >= 0:
                        second_nl = data.find(b"\n", first_nl + 1)
                        if second_nl >= 0:
                            offset = second_nl + 1

            # Get actual object data
            obj_data = data[offset:]
            if len(obj_data) < 16:
                logger.error(f"Object data too small after header for {object_name}")
                return None

            # For export format files, determine object type from filename
            if data.startswith(b"HA$PBExportHeader$"):
                object_type = cls._get_object_type_from_filename(object_name)
                obj = PowerBuilderObject(object_name, object_type)
                obj.version = None  # Export format doesn't embed version in header
            else:
                # Parse object header for non-export format
                # Based on analysis, objects start with patterns like:
                # 03 00 76 40 01 00 10 00 ...

                # Read first few values to understand structure
                struct.unpack("<H", obj_data[0:2])[0]  # Often 0x0003
                object_type = struct.unpack("<H", obj_data[2:4])[0]  # e.g., 0x4076
                version_info = struct.unpack("<I", obj_data[4:8])[0]  # e.g., 0x00100001

                obj = PowerBuilderObject(object_name, object_type)
                obj.version = version_info

            logger.debug(f"Parsing object {object_name}:")
            logger.debug(f"  Object type: 0x{object_type:04x}")
            if obj.version:
                logger.debug(f"  Version: 0x{obj.version:08x}")

            # Find P-code section
            pcode_offset, pcode_length = cls._find_pcode_section(obj_data, obj)

            if pcode_offset >= 0:
                obj.pcode_offset = offset + pcode_offset
                obj.pcode_length = pcode_length
                obj.pcode_data = obj_data[pcode_offset : pcode_offset + pcode_length]
                logger.info(
                    f"Found P-code in {object_name} at offset 0x{pcode_offset:04x}, length {pcode_length}"
                )
            else:
                logger.warning(f"No P-code found in {object_name}")

            return obj

        except Exception as e:
            logger.exception(f"Failed to parse object {object_name}: {e}")
            return None

    @classmethod
    def _find_pcode_section(
        cls, data: bytes, obj: PowerBuilderObject
    ) -> tuple[int, int]:
        """Find the P-code section within object data.

        PowerBuilder objects appear to have P-code embedded throughout the
        structure rather than in a single contiguous block.

        Args:
            data: Object data (without export header)
            obj: PowerBuilderObject being parsed

        Returns:
            Tuple of (offset, length) or (-1, 0) if not found
        """
        # Try the enhanced detector first
        try:
            from decompile.analysis.pcode_detector_enhanced import (
                EnhancedPCodeDetectorV2 as EnhancedPCodeDetector,
            )

            # Determine object type from the object
            object_type = cls._get_object_type_name(obj.object_type)

            # Get the primary P-code region
            result = EnhancedPCodeDetector.get_primary_pcode_region(data, object_type)

            if result:
                pcode_data, offset = result
                logger.info(
                    f"Enhanced detector found P-code region at offset=0x{offset:04x}, length={len(pcode_data)}"
                )
                return offset, len(pcode_data)
            logger.warning("Enhanced detector found no P-code regions")
        except Exception as e:
            logger.warning(
                f"Enhanced detector failed: {e}, falling back to simple detection"
            )

        # Fallback to simple detection
        # Skip the initial object header (appears to be around 0x100 bytes)
        pcode_start = 0x100  # Start after initial metadata

        # Look for the end of the object data
        # Usually marked by long sequences of 0x00 or 0xFF
        pcode_end = len(data)

        # Find where the actual data ends (before padding)
        consecutive_nulls = 0
        for i in range(len(data) - 1, pcode_start, -1):
            if data[i] == 0x00 or data[i] == 0xFF:
                consecutive_nulls += 1
                if consecutive_nulls > 100:  # Found significant padding
                    pcode_end = i - consecutive_nulls + 1
                    break
            else:
                consecutive_nulls = 0

        # The P-code is mixed with data throughout this region
        # We'll return the whole region and let the decoder handle it
        length = pcode_end - pcode_start

        if length > 0:
            logger.info(
                f"Returning object data region: offset=0x{pcode_start:04x}, length={length}"
            )
            return pcode_start, length

        # Fallback: try to find any executable code patterns
        logger.warning("Using fallback P-code detection")
        return cls._find_pcode_fallback(data)

    @classmethod
    def _find_pcode_fallback(cls, data: bytes) -> tuple[int, int]:
        """Fallback method to find P-code using pattern matching."""
        # Look for common function prologue patterns
        for i in range(min(len(data) - 20, 0x1000)):
            # Check for function-like patterns
            if (
                data[i] == 0x32  # PUSH_CONST_INT
                or data[i] == 0x65  # PUSH_LVALUE_INT
                or data[i] == 0x29
            ):  # GLOBFUNCCALL
                # Found a potential start
                # Find the end by looking for RETURN followed by padding
                for j in range(i + 10, len(data)):
                    if data[j] == 0x00 and j + 4 < len(data):
                        # Check if followed by more nulls (end of function)
                        if all(
                            data[k] == 0x00 for k in range(j, min(j + 10, len(data)))
                        ):
                            return i, j - i

        return -1, 0

    @classmethod
    def _get_object_type_from_filename(cls, object_name: str) -> int:
        """Get object type constant from filename extension."""
        name_lower = object_name.lower()

        if name_lower.endswith(".fun"):
            return cls.OBJECT_TYPE_FUNCTION
        if name_lower.endswith(".win"):
            return cls.OBJECT_TYPE_WINDOW
        if name_lower.endswith(".udo"):
            return cls.OBJECT_TYPE_USEROBJECT
        if name_lower.endswith(".str"):
            return cls.OBJECT_TYPE_STRUCTURE
        if name_lower.endswith(".men"):
            return cls.OBJECT_TYPE_MENU
        if name_lower.endswith(".dwo"):
            return cls.OBJECT_TYPE_DATAWINDOW
        if name_lower.endswith((".apl", ".app")):
            return cls.OBJECT_TYPE_APPLICATION
        # Default to function for unknown extensions
        return cls.OBJECT_TYPE_FUNCTION

    @classmethod
    def _get_object_type_name(cls, object_type: int) -> str:
        """Convert object type code to name."""
        type_map = {
            cls.OBJECT_TYPE_FUNCTION: "function",
            cls.OBJECT_TYPE_WINDOW: "window",
            cls.OBJECT_TYPE_USEROBJECT: "userobject",
            cls.OBJECT_TYPE_STRUCTURE: "structure",
            cls.OBJECT_TYPE_MENU: "menu",
            cls.OBJECT_TYPE_DATAWINDOW: "datawindow",
            cls.OBJECT_TYPE_APPLICATION: "application",
        }
        return type_map.get(object_type, "unknown")

    @classmethod
    def _looks_like_pcode_start(cls, data: bytes) -> bool:
        """Check if data looks like the start of P-code."""
        if len(data) < 4:
            return False

        # Common P-code start patterns
        # Functions often start with parameter handling or jumps
        first_byte = data[0]

        # Valid starting opcodes
        VALID_START_OPCODES = {
            0x00,  # RETURN (empty function)
            0x04,  # JUMP
            0x29,  # GLOBFUNCCALL
            0x32,  # PUSH_CONST_INT
            0x65,  # PUSH_LVALUE_INT
        }

        return first_byte in VALID_START_OPCODES

    @classmethod
    def _find_pcode_end(cls, data: bytes, start: int) -> int:
        """Find where P-code ends."""
        i = start
        consecutive_zeros = 0

        while i < len(data):
            if data[i] == 0:
                consecutive_zeros += 1
                if consecutive_zeros >= 8:  # Multiple nulls indicate end
                    return i - consecutive_zeros + 1
            else:
                consecutive_zeros = 0

            i += 1

        return len(data)

    @classmethod
    def extract_strings(cls, data: bytes) -> list[str]:
        """Extract UTF-16 strings from object data."""
        strings = []
        i = 0

        while i < len(data) - 4:
            # Look for UTF-16 LE strings
            if i + 1 < len(data) and data[i + 1] == 0 and 32 <= data[i] < 127:
                string_bytes = []
                start = i

                while i + 1 < len(data):
                    if data[i + 1] == 0 and 32 <= data[i] < 127:
                        string_bytes.append(data[i])
                        i += 2
                    else:
                        break

                if len(string_bytes) >= 3:  # Minimum meaningful string
                    string_text = "".join(chr(b) for b in string_bytes)
                    strings.append((start, string_text))
            else:
                i += 1

        return strings
