"""PowerBuilder object parser for extracting P-code from object data.

This module parses PowerBuilder object structures to extract the actual
P-code sections for decompilation.
"""

import struct

from src.decompile.pcode.detector import EnhancedPCodeDetector

"""Represents a PowerBuilder object with P-code."""

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
self.pcode_sections = []  # List of PCodeSection objects

"""Return string representation of the object."""
return (
f"<PowerBuilderObject {self.object_name} type = 0x{self.object_type:04x}>"
)

"""Get P-code data from all detected sections.

List of P-code data bytes, one for each section
"""
if not self.pcode_sections:
    # Fallback to single section if no sections stored
    if self.pcode_data:
        return [self.pcode_data]
        return []

        # Extract data for each section
        pcode_chunks = []
        for section in self.pcode_sections:
            # Extract data for this specific section
            if hasattr(section, "data") and section.data:
                pcode_chunks.append(section.data)
                elif self.pcode_data and section.offset >= 0 and section.length > 0:
                    # Extract from the full P-code data based on relative offsets
                    rel_offset = section.offset - self.pcode_sections[0].offset
                    chunk = self.pcode_data[rel_offset : rel_offset + section.length]
                    pcode_chunks.append(chunk)

                    return pcode_chunks

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

                        data: Raw object data (after export header if present)
                        object_name: Name of the object

                        PowerBuilderObject instance or None if parsing fails
                        """
                        if len(data) < 16:
                            logger.error(
                            "Object data too small for %s: %s bytes", object_name, len(data)
                            )
                            return None

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

                            first_nl = data.find(b"\n")
                            if first_nl >= 0:
                                second_nl = data.find(b"\n", first_nl + 1)
                                if second_nl >= 0:
                                    return second_nl + 1

                                    return 0

                                @classmethod
                                    def _create_object(
                                        cls, data: bytes, obj_data: bytes, object_name: str
                                        ) -> PowerBuilderObject:
                                            """Create PowerBuilderObject based on data format."""
                                            if data.startswith(b"HA$PBExportHeader$"):
                                                # Export format - determine type from filename
                                                object_type = cls._get_object_type_from_filename(object_name)
                                                obj = PowerBuilderObject(object_name, object_type)
                                                obj.version = None                                                    # Binary format - parse header
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
                                            def _set_pcode_section(
                                                cls, obj: PowerBuilderObject, obj_data: bytes, offset: int, object_name: str
                                                ) -> None:
                                                    """Find and set P-code section in the object."""
                                                    # Get all P-code sections from the enhanced detector
                                                    try:
                                                        from src.decompile.pcode.detector import EnhancedPCodeDetector

                                                        object_type = cls._get_object_type_name(obj.object_type)
                                                        sections = EnhancedPCodeDetector.find_all_pcode_sections(
                                                        obj_data, object_type
                                                        )

                                                        # Store all sections for detailed analysis
                                                        obj.pcode_sections = sections

                                                        # Set the primary P-code data (backward compatibility)
                                                        # This includes all P-code from first section to last
                                                        first_section = sections[0]
                                                        last_section = sections[-1]

                                                        obj.pcode_offset = offset + first_section.offset
                                                        obj.pcode_length = (
                                                        last_section.offset + last_section.length
                                                        ) - first_section.offset

                                                        # Extract the full P-code data - from first section to end of last section
                                                        pcode_start = first_section.offset
                                                        pcode_end = last_section.offset + last_section.length
                                                        obj.pcode_data = obj_data[pcode_start:pcode_end]

                                                        logger.info(
                                                        "Found %d P-code section(s) in %s, total P-code: offset = 0x%04x, length=%d bytes",
                                                        len(sections),
                                                        object_name,
                                                        obj.pcode_offset,
                                                        obj.pcode_length,
                                                        )

                                                        # Log individual sections for debugging
                                                        for idx, section in enumerate(sections):
                                                            logger.debug(
                                                            "  Section %d: offset = 0x%04x, length=%d, confidence=%.2f",
                                                            idx + 1,
                                                            section.offset,
                                                            section.length,
                                                            section.confidence,
                                                            )                                                                logger.warning("No P-code sections found in %s", object_name)

                                                                logger.error("Failed to use enhanced detector: %s", e)
                                                                # Fall back to legacy detection
                                                                pcode_offset, pcode_length = cls._find_pcode_section(obj_data, obj)

                                                                obj.pcode_offset = offset + pcode_offset
                                                                obj.pcode_length = pcode_length
                                                                obj.pcode_data = obj_data[pcode_offset : pcode_offset + pcode_length]
                                                                logger.info(
                                                                "Found P-code in %s at offset 0x%04x, length %d (legacy detection)",
                                                                object_name,
                                                                pcode_offset,
                                                                pcode_length,
                                                                )                                                                    logger.warning("No P-code found in %s", object_name)

                                                                @classmethod
                                                                    def _find_pcode_section(
                                                                        cls,
                                                                        data: bytes,
                                                                        obj: PowerBuilderObject,
                                                                        ) -> tuple[int, int]:
                                                                            """Find the P-code section within object data.

                                                                            PowerBuilder objects may have P-code in multiple sections throughout the
                                                                            structure. This method uses the enhanced detector to find all sections
                                                                            and merges them as needed.

                                                                            data: Object data (without export header)
                                                                            obj: PowerBuilderObject being parsed

                                                                            Tuple of (offset, length) or (-1, 0) if not found
                                                                            """
                                                                            try:
                                                                                # Determine object type from the object
                                                                                object_type = cls._get_object_type_name(obj.object_type)

                                                                                # Find all P-code sections using the enhanced detector
                                                                                sections = EnhancedPCodeDetector.find_all_pcode_sections(data, object_type)

                                                                                logger.warning(
                                                                                "Enhanced detector found no P-code sections in %s", obj.object_name
                                                                                )
                                                                                return -1, 0

                                                                    # Log what was found
                                                                    logger.info(
                                                                    "Enhanced detector found %d P-code section(s) in %s:",
                                                                    len(sections),
                                                                    obj.object_name,
                                                                    )
                                                                    for idx, section in enumerate(sections):
                                                                        logger.info(
                                                                        "  Section %d: offset = 0x%04x, length=%d bytes, confidence=%.2f",
                                                                        idx + 1,
                                                                        section.offset,
                                                                        section.length,
                                                                        section.confidence,
                                                                        )

                                                                        # If we have multiple sections, we need to decide how to handle them
                                                                        if len(sections) == 1:
                                                                            # Single section - simple case
                                                                            section = sections[0]
                                                                            return section.offset, section.length
                                                                            # Multiple sections - find the span from first to last
                                                                            first_offset = sections[0].offset
                                                                            last_section = sections[-1]
                                                                            last_end = last_section.offset + last_section.length
                                                                            total_length = last_end - first_offset

                                                                            logger.info(
                                                                            "Multiple P-code sections found. Returning span from 0x%04x to 0x%04x (length=%d)",
                                                                            first_offset,
                                                                            last_end,
                                                                            total_length,
                                                                            )

                                                                            # The P-code decoder should be able to handle mixed data.
                                                                            return first_offset, total_length

                                                                            logger.error(
                                                                            "Failed to import or use EnhancedPCodeDetector: %s",
                                                                            e,
                                                                            )
                                                                            return -1, 0

                                                                        @classmethod
                                                                            def _find_pcode_fallback(cls, data: bytes) -> tuple[int, int]:
                                                                                """Fallback method to find P-code using pattern matching."""
                                                                                # Look for common function prologue patterns
                                                                                for i in range(min(len(data) - 20, 0x1000)):
                                                                                    # Check for function-like patterns
                                                                                    if (
                                                                                    data[i] == 0x32  # PUSH_CONST_INT
                                                                                    or data[i] == 0x65  # PUSH_LVALUE_INT
                                                                                    or data[i] == 0x29  # GLOBFUNCCALL
                                                                                    ):
                                                                                        # Found a potential start
                                                                                        # Find the end by looking for RETURN followed by padding
                                                                                        for j in range(i + 10, len(data)):
                                                                                            if (
                                                                                            data[j] == 0x00
                                                                                            and j + 4 < len(data)
                                                                                            and all(
                                                                                            data[k] == 0x00 for k in range(j, min(j + 10, len(data)))
                                                                                            )
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
                                                                            valid_start_opcodes = {
                                                                            0x00,  # RETURN (empty function)
                                                                            0x04,  # JUMP
                                                                            0x29,  # GLOBFUNCCALL
                                                                            0x32,  # PUSH_CONST_INT
                                                                            0x65,  # PUSH_LVALUE_INT
                                                                            }

                                                                            return first_byte in valid_start_opcodes

                                                                        @classmethod
                                                                            def _find_pcode_end(cls, data: bytes, start: int) -> int:
                                                                                """Find where P-code ends."""
                                                                                i = start
                                                                                consecutive_zeros = 0

                                                                                if data[i] == 0:
                                                                                    consecutive_zeros += 1
                                                                                    if consecutive_zeros >= 8:  # Multiple nulls indicate end:
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

                                                                                    # Look for UTF-16 LE strings
                                                                                    if i + 1 < len(data) and data[i + 1] == 0 and 32 <= data[i] < 127:
                                                                                        string_bytes = []
                                                                                        start = i

                                                                                        if data[i + 1] == 0 and 32 <= data[i] < 127:
                                                                                            string_bytes.append(data[i])
                                                                                            i += 2                                                                                                break

                                                                                string_text = "".join(chr(b) for b in string_bytes)
                                                                                strings.append((start, string_text))                                                                                    i += 1

                                                                                    return strings
