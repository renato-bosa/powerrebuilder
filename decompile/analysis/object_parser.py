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
        """Initialize PowerBuilder object."""
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
        """Return string representation of the object."""
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
            logger.error("Object data too small for %s: %s bytes", object_name, len(data))
            return None

        try:
            # Skip export header if present
            offset = cls._skip_export_header(data)

            # Get actual object data
            obj_data = data[offset:]
            if len(obj_data) < 16:
                logger.error("Object data too small after header for %s", object_name)
                return None

            # Create object based on format
            obj = cls._create_object(data, obj_data, object_name)

            cls._log_object_info(obj, object_name)

            # Find and set P-code section
            cls._set_pcode_section(obj, obj_data, offset, object_name)

            return obj

        except Exception:
            logger.exception("Failed to parse object %s", object_name)
            return None

    @classmethod
    def _skip_export_header(cls, data: bytes) -> int:
        """Skip export header if present and return offset."""
        if not data.startswith(b"HA$PBExportHeader$"):
            return 0

        header_end = data.find(b"\n$PBExportComments$\n")
        if header_end >= 0:
            return header_end + len(b"\n$PBExportComments$\n")

        # Fallback: find second newline
        first_nl = data.find(b"\n")
        if first_nl >= 0:
            second_nl = data.find(b"\n", first_nl + 1)
            if second_nl >= 0:
                return second_nl + 1

        return 0

    @classmethod
    def _create_object(cls, data: bytes, obj_data: bytes, object_name: str) -> PowerBuilderObject:
        """Create PowerBuilderObject based on data format."""
        if data.startswith(b"HA$PBExportHeader$"):
            # Export format - determine type from filename
            object_type = cls._get_object_type_from_filename(object_name)
            obj = PowerBuilderObject(object_name, object_type)
            obj.version = None
        else:
            # Binary format - parse header
            object_type = struct.unpack("<H", obj_data[2:4])[0]
            version_info = struct.unpack("<I", obj_data[4:8])[0]
            obj = PowerBuilderObject(object_name, object_type)
            obj.version = version_info

        return obj

    @classmethod
    def _log_object_info(cls, obj: PowerBuilderObject, object_name: str) -> None:
        """Log object parsing information."""
        logger.debug("Parsing object %s:", object_name)
        logger.debug("  Object type: 0x%04x", obj.object_type)
        if obj.version:
            logger.debug("  Version: 0x%08x", obj.version)

    @classmethod
    def _set_pcode_section(cls, obj: PowerBuilderObject, obj_data: bytes, offset: int, object_name: str) -> None:
        """Find and set P-code section in the object."""
        pcode_offset, pcode_length = cls._find_pcode_section(obj_data, obj)

        if pcode_offset >= 0:
            obj.pcode_offset = offset + pcode_offset
            obj.pcode_length = pcode_length
            obj.pcode_data = obj_data[pcode_offset : pcode_offset + pcode_length]
            logger.info(
                "Found P-code in %s at offset 0x%04x, length %d",
                object_name, pcode_offset, pcode_length,
            )
        else:
            logger.warning("No P-code found in %s", object_name)

    @classmethod
    def _find_pcode_section(
        cls, data: bytes, obj: PowerBuilderObject,
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
                    "Enhanced detector found P-code region at offset=0x%04x, length=%d",
                    offset, len(pcode_data),
                )
                return offset, len(pcode_data)
            logger.warning("Enhanced detector found no P-code regions")
        except (ImportError, AttributeError) as e:
            logger.warning(
                "Enhanced detector failed: %s, falling back to simple detection",
                e,
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
                "Returning object data region: offset=0x%04x, length=%d",
                pcode_start, length,
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
                    if data[j] == 0x00 and j + 4 < len(data) and all(
                        data[k] == 0x00 for k in range(j, min(j + 10, len(data)))
                    ):
                        return i, j - i

        return -1, 0

    @classmethod
    def _get_object_type_from_filename(cls, object_name: str) -> int:
        """Get object type constant from filename extension."""
        name_lower = object_name.lower()
        
        # Map of extensions to object types
        extension_map = {
            ".fun": cls.OBJECT_TYPE_FUNCTION,
            ".win": cls.OBJECT_TYPE_WINDOW,
            ".udo": cls.OBJECT_TYPE_USEROBJECT,
            ".str": cls.OBJECT_TYPE_STRUCTURE,
            ".men": cls.OBJECT_TYPE_MENU,
            ".dwo": cls.OBJECT_TYPE_DATAWINDOW,
            ".apl": cls.OBJECT_TYPE_APPLICATION,
            ".app": cls.OBJECT_TYPE_APPLICATION,
        }
        
        # Check each extension
        for ext, obj_type in extension_map.items():
            if name_lower.endswith(ext):
                return obj_type
        
        # Default to function for unknown extensions
        return cls.OBJECT_TYPE_FUNCTION

    @classmethod
    def _get_object_type_name(cls, object_type: int) -> str:
        """Convert object type code to name."""
        type_map = {
            cls.OBJECT_TYPE_FUNCTION: "function", cls.OBJECT_TYPE_WINDOW: "window", cls.OBJECT_TYPE_USEROBJECT: "userobject", cls.OBJECT_TYPE_STRUCTURE: "structure", cls.OBJECT_TYPE_MENU: "menu", cls.OBJECT_TYPE_DATAWINDOW: "datawindow", cls.OBJECT_TYPE_APPLICATION: "application", }
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
        valid_start_opcodes = {
            0x00, # RETURN (empty function)
            0x04, # JUMP
            0x29, # GLOBFUNCCALL
            0x32, # PUSH_CONST_INT
            0x65, # PUSH_LVALUE_INT
        }

        return first_byte in valid_start_opcodes

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
