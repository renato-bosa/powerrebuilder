"""PowerBuilder P-code binary decoder with version awareness.

This module implements a version-aware decoder for PowerBuilder P-code binary format,
using version-specific opcode tables as recommended in the decompiler guide.
"""

import logging
import struct
from dataclasses import dataclass, field
from typing import Any, BinaryIO

from src.decompile.pcode.detector import PCodeDetector
from src.decompile.pcode.opcodes.definitions import get_opcodes_for_version
from src.extract.pbd.version_detection import PBVersionDetector as VersionDetector
from src.extract.pbd.version_detection import PowerBuilderVersion

logger = logging.getLogger(__name__)


@dataclass
class PCodeInstruction:
    """Represents a decoded P-code instruction."""

    offset: int
    opcode: int
    opcode_name: str
    operands: list[Any] = field(default_factory=list)
    raw_bytes: bytes = field(default_factory=bytes)
    comment: str | None = None


@dataclass
class DecodedObject:
    """Represents a fully decoded PowerBuilder object."""

    name: str
    type: str
    version: PowerBuilderVersion
    instructions: list[PCodeInstruction] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PCodeDecoderV2:
    """Version-aware decoder for PowerBuilder P-code binary format."""

    def __init__(self, version: PowerBuilderVersion | None = None) -> None:
        """Initialize the decoder.

        Args:
            version: PowerBuilder version (auto-detected if None)
        """
        self.version = version
        self.opcode_table: dict[int, tuple[str, int, str | None]] = {}
        self.reset()

    def reset(self) -> None:
        """Reset decoder state."""
        self.instructions = []
        self.strings = {}
        self.current_offset = 0
        self.labels = {}
        self.metadata = {}

    def decode_pbd_object(
        self,
        pbd_handle: BinaryIO,
        entry_offset: int,
        entry_size: int,
        object_name: str,
    ) -> DecodedObject:
        """Decode a specific object from a PBD file.

        Args:
            pbd_handle: Open PBD file handle
            entry_offset: Offset to the object's data in the PBD
            entry_size: Size of the object's data
            object_name: Name of the object

        Returns:
            Decoded object with instructions and metadata
        """
        # Save current position
        original_pos = pbd_handle.tell()

        try:
            # Auto-detect version if not set
            if not self.version:
                detector = VersionDetector()
                pbd_handle.seek(0)
                self.version = detector.detect_from_file(pbd_handle)
                logger.info("Auto-detected PowerBuilder version: %s", self.version)

            # Load version-specific opcode table
            version_str = f"pb{self.version.major}_{self.version.minor}"
            self.opcode_table = get_opcodes_for_version(version_str)
            logger.info("Using opcode table for %s", self.version)

            # Seek to object data
            pbd_handle.seek(entry_offset)
            object_data = pbd_handle.read(entry_size)

            # Detect object type
            object_type = self._detect_object_type(object_name)

            # Parse object header to find P-code
            pcode_offset, pcode_size = self._find_pcode_in_object(
                object_data,
                object_type,
            )

            if pcode_offset and pcode_size:
                pcode_bytes = object_data[pcode_offset : pcode_offset + pcode_size]
                instructions = self.decode_pcode(
                    pcode_bytes,
                    entry_offset + pcode_offset,
                )
            else:
                instructions = []

            # Create decoded object
            return DecodedObject(
                name=object_name,
                type=object_type,
                version=self.version,
                instructions=instructions,
                metadata=self.metadata,
            )

        finally:
            # Restore original position
            pbd_handle.seek(original_pos)

    def decode_pcode_section(
        self,
        pcode_bytes: bytes,
        object_name: str,
        pcode_info: Any | None = None,
    ) -> DecodedObject:
        """Decode a P-code section with optional section information.

        Args:
            pcode_bytes: Raw P-code bytes
            object_name: Name of the object being decoded
            pcode_info: Optional P-code section information

        Returns:
            Decoded object with instructions
        """
        logger.info(
            "Decoding P-code for '%s' (%d bytes, sections: %s)",
            object_name,
            len(pcode_bytes),
            bool(pcode_info and hasattr(pcode_info, "sections")),
        )

        # Initialize opcode table if not already loaded
        if not self.opcode_table:
            # Set default version if not set
            if not self.version:
                self.version = PowerBuilderVersion(10, 5, True)  # Default to PB 10.5 Unicode
                logger.info("Using default PowerBuilder version: %s", self.version)

            # Load version-specific opcode table
            version_str = str(self.version)  # PowerBuilderVersion.__str__ returns "pb10_5" format
            self.opcode_table = get_opcodes_for_version(version_str)
            logger.info("Loaded opcode table for %s (%d opcodes)", self.version, len(self.opcode_table))

        # Handle sectioned P-code
        if pcode_info and hasattr(pcode_info, "sections") and pcode_info.sections:
            logger.info("P-code has %d sections", len(pcode_info.sections))
            all_instructions = []

            for idx, section in enumerate(pcode_info.sections):
                logger.info(
                    "Processing section %d: offset=0x%04x, length=%d",
                    idx + 1,
                    section.offset,
                    section.length,
                )

                # The pcode_bytes should already contain all the P-code data
                # Extract the section based on relative offsets
                if idx == 0:
                    # First section starts at beginning of pcode_bytes
                    section_start = 0
                else:
                    # Calculate relative offset from first section
                    section_start = section.offset - pcode_info.sections[0].offset

                section_end = section_start + section.length
                section_data = pcode_bytes[section_start:section_end]

                logger.debug(
                    "Section %d: extracting bytes [%d:%d] from pcode_bytes",
                    idx + 1,
                    section_start,
                    section_end,
                )

                # Log first few bytes of section data
                logger.debug(
                    "Section %d first 16 bytes: %s",
                    idx + 1,
                    section_data[:16].hex()
                    if len(section_data) >= 16
                    else section_data.hex(),
                )

                # Decode this section with less strict validation
                section_instructions = self.decode_pcode(
                    section_data, section.offset, validate=False
                )
                logger.info(
                    "Section %d yielded %d instructions",
                    idx + 1,
                    len(section_instructions),
                )
                all_instructions.extend(section_instructions)

            instructions = all_instructions
        else:
            # No section info - decode as single block
            logger.info("No section info available, decoding as single block")
            instructions = self.decode_pcode(pcode_bytes, 0, validate=True)

        # Determine object type from name
        object_type = self._detect_object_type(object_name)
        logger.debug("Detected object type '%s' for '%s'", object_type, object_name)

        # Store any metadata from pcode_info
        metadata = {}
        if pcode_info and hasattr(pcode_info, "__dict__"):
            metadata = {
                k: v for k, v in pcode_info.__dict__.items() if not k.startswith("_")
            }

        return DecodedObject(
            name=object_name,
            type=object_type,
            version=self.version,
            instructions=instructions,
            metadata=metadata,
        )

    def decode_pcode(
        self,
        pcode_bytes: bytes,
        base_offset: int = 0,
        validate: bool = True,
    ) -> list[PCodeInstruction]:
        """Decode P-code bytes into instructions.

        Args:
            pcode_bytes: Raw P-code bytes
            base_offset: Base offset for addresses
            validate: Whether to validate the instruction sequence

        Returns:
            List of decoded instructions
        """
        self.reset()
        self.current_offset = 0

        logger.info(
            "Decoding %d bytes of P-code starting at offset 0x%04x",
            len(pcode_bytes),
            base_offset,
        )

        if len(pcode_bytes) >= 16:
            # Check for common non-P-code patterns at the start
            if pcode_bytes[:8] == b"\x00" * 8:
                logger.info("Data starts with null bytes, likely not P-code")
                return []
            if pcode_bytes[:8] == b"\xff" * 8:
                logger.info("Data starts with 0xFF bytes, likely not P-code")
                return []
            # Check if first few bytes are all the same (common in padding/headers)
            if len(set(pcode_bytes[:16])) == 1:
                logger.info(
                    "First 16 bytes are all the same value (0x%02x), likely not P-code",
                    pcode_bytes[0],
                )
                return []

        # First pass - identify jump targets
        self._identify_jump_targets(pcode_bytes, base_offset)

        # Second pass - decode instructions
        self.current_offset = 0
        consecutive_returns = 0
        max_consecutive_returns = 5  # Stop if we see more than 5 RETURNs in a row

        while self.current_offset < len(pcode_bytes):
            prev_offset = self.current_offset
            instruction = self._decode_next_instruction(pcode_bytes, base_offset)

            if instruction:
                # Check for consecutive RETURN instructions
                if instruction.opcode_name == "RETURN":
                    consecutive_returns += 1
                    if consecutive_returns > max_consecutive_returns:
                        logger.info(
                            "Stopping decode: found %d consecutive RETURN instructions at offset 0x%04x "
                            "(likely reached non-P-code data)",
                            consecutive_returns,
                            base_offset + self.current_offset,
                        )
                        break
                else:
                    consecutive_returns = 0  # Reset counter

                self.instructions.append(instruction)
            else:
                # If we couldn't decode an instruction, log it and skip the byte
                logger.warning(
                    "Failed to decode instruction at offset 0x%04x (byte 0x%02x), skipping",
                    base_offset + self.current_offset,
                    pcode_bytes[self.current_offset]
                    if self.current_offset < len(pcode_bytes)
                    else 0xFF,
                )
                self.current_offset += 1
                consecutive_returns = 0  # Reset counter on failed decode

            # Safety check to prevent infinite loops
            if self.current_offset == prev_offset:
                logger.error(
                    "Decoder stuck at offset 0x%04x, stopping",
                    base_offset + self.current_offset,
                )
                break

        logger.info(
            "Decoded %d instructions from %d bytes",
            len(self.instructions),
            len(pcode_bytes),
        )

        # Validate the decoded instruction sequence if requested
        if validate and not self._validate_instruction_sequence(self.instructions):
            logger.warning(
                "Decoded instruction sequence failed validation - returning instructions anyway"
            )
            # Return instructions anyway - let the caller decide what to do

        return self.instructions

    def _decode_next_instruction(
        self,
        pcode: bytes,
        base_offset: int,
    ) -> PCodeInstruction | None:
        """Decode the next instruction at current offset."""
        if self.current_offset >= len(pcode):
            return None

        address = base_offset + self.current_offset
        op_byte = pcode[self.current_offset]

        # Early detection of non-P-code data patterns
        # Check for sequences that indicate we're not in P-code anymore
        if self.current_offset + 8 < len(pcode):
            # Check if we have a sequence of null bytes (common padding)
            next_bytes = pcode[self.current_offset : self.current_offset + 8]
            if next_bytes == b"\x00" * 8:
                logger.info(
                    "Detected sequence of null bytes at offset 0x%04x, likely end of P-code",
                    self.current_offset,
                )
                return None

            # Check for sequences of 0xFF (another common padding pattern)
            if next_bytes == b"\xff" * 8:
                logger.info(
                    "Detected sequence of 0xFF bytes at offset 0x%04x, likely end of P-code",
                    self.current_offset,
                )
                return None

        # Log first few instructions for debugging
        if len(self.instructions) < 5:
            logger.debug(
                "Decoding instruction #%d at offset 0x%04x (byte 0x%02x)",
                len(self.instructions) + 1,
                address,
                op_byte,
            )

        # Look up opcode in version-specific table
        opcode_info = self.opcode_table.get(op_byte)
        if not opcode_info:
            logger.debug(
                "Unknown opcode 0x%02x at offset 0x%04x",
                op_byte,
                address,
            )
            return None

        opcode_name, operand_count, description = opcode_info

        # Start building instruction
        instruction = PCodeInstruction(
            offset=address,
            opcode=op_byte,
            opcode_name=opcode_name,
            operands=[],
            raw_bytes=bytes([op_byte]),
            comment=description,
        )

        # Advance past opcode byte
        self.current_offset += 1

        # Decode operands based on opcode type
        try:
            self._decode_operands(pcode, instruction, operand_count)
        except Exception as e:
            logger.warning(
                "Failed to decode operands for %s at offset 0x%04x: %s",
                opcode_name,
                address,
                e,
            )
            return None

        return instruction

    def _decode_operands(
        self,
        pcode: bytes,
        instruction: PCodeInstruction,
        expected_count: int,
    ) -> None:
        """Decode operands for an instruction."""
        # Handle different operand types based on the opcode
        opcode = instruction.opcode
        
        # Most PowerBuilder opcodes have specific operand patterns
        for i in range(expected_count):
            if self.current_offset >= len(pcode):
                raise ValueError("Insufficient bytes for operand")

            # Determine operand size based on opcode and position
            operand_size = self._get_operand_size(opcode, i)
            
            if self.current_offset + operand_size > len(pcode):
                raise ValueError(f"Insufficient bytes for {operand_size}-byte operand")

            if operand_size == 1:
                # 8-bit operand
                operand = pcode[self.current_offset]
                instruction.operands.append(operand)
                instruction.raw_bytes += pcode[self.current_offset:self.current_offset + 1]
                self.current_offset += 1
            elif operand_size == 2:
                # 16-bit operand (little endian)
                operand = struct.unpack_from("<H", pcode, self.current_offset)[0]
                instruction.operands.append(operand)
                instruction.raw_bytes += pcode[self.current_offset:self.current_offset + 2]
                self.current_offset += 2
            else:
                raise ValueError(f"Unsupported operand size: {operand_size}")

    def _get_operand_size(self, opcode: int, operand_index: int) -> int:
        """Get the size of an operand for a specific opcode.
        
        Args:
            opcode: The instruction opcode
            operand_index: Which operand (0-based)
            
        Returns:
            Size in bytes (1 or 2)
        """
        # Most PowerBuilder operands are 8-bit for simple instructions
        # and 16-bit for complex instructions with addresses/indices
        
        # Instructions that typically use 16-bit operands
        sixteen_bit_opcodes = {
            0x20,  # PUSH_CONST_REF
            0x29,  # GLOBFUNCCALL
            0x2A,  # CALL_FUNCTION
            0x2B,  # DLLFUNCCALL
            0x2C,  # DOTFUNCCALL
            0x2D,  # PUSH_GLOBAL_VAR
            0x2E,  # ARRAYLIST
        }
        
        if opcode in sixteen_bit_opcodes:
            return 2
        
        # Default to 8-bit operands for most instructions
        return 1

    def _identify_jump_targets(self, pcode_bytes: bytes, base_offset: int) -> None:
        """Identify jump targets in the code for labeling."""
        # This would analyze jump instructions and mark their targets

    def _validate_instruction_sequence(
        self, instructions: list[PCodeInstruction]
    ) -> bool:
        """Validate that the decoded instructions form a valid sequence."""
        if not instructions:
            return False

        # Basic validation - check for reasonable patterns
        # Real implementation would be more sophisticated
        return True

    def _detect_object_type(self, object_name: str) -> str:
        """Detect object type from name."""
        name_lower = object_name.lower()
        if name_lower.startswith("w_"):
            return "window"
        if name_lower.startswith("u_"):
            return "userobject"
        if name_lower.startswith("f_"):
            return "function"
        if name_lower.startswith("n_"):
            return "nonvisualobject"
        if name_lower.startswith("m_"):
            return "menu"
        if name_lower.startswith("d_"):
            return "datawindow"
        return "unknown"

    def _find_pcode_in_object(
        self,
        object_data: bytes,
        object_type: str,
    ) -> tuple[int | None, int | None]:
        """Find P-code section within object data."""
        # Use the enhanced detector to find P-code
        detector = PCodeDetector()
        pcode_info = detector.find_pcode_in_data(object_data)

        if pcode_info and hasattr(pcode_info, "offset") and hasattr(pcode_info, "size"):
            return pcode_info.offset, pcode_info.size

        return None, None
