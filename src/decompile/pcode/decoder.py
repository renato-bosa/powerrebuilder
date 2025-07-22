"""PowerBuilder P-code binary decoder with version awareness.

This module implements a version-aware decoder for PowerBuilder P-code binary format,
using version-specific opcode tables as recommended in the decompiler guide.
"""

import logging
import struct
from dataclasses import dataclass, field
from typing import Any, BinaryIO
from src.extract.pbd.version_detection import PBVersionDetector as VersionDetector
from src.extract.pbd.version_detection import PowerBuilderVersion
from src.decompile.pcode.detector import EnhancedPCodeDetector
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
        # Detect version if not provided
        if self.version is None:
        self.version = VersionDetector.detect_from_file(
        pbd_handle)
        if self.version is None:
        logger.warning(
        "Could not detect version, using default")
        self.version = VersionDetector.get_default_version()

        # Load version-specific opcode table
        version_str = f"pb{
        self.version.major}_{
        self.version.minor}"
        self.opcode_table = get_opcodes_for_version(
        version_str)
        logger.info(
        "Using opcode table for %s", self.version)

        # Seek to object data
        pbd_handle.seek(entry_offset)
        object_data = pbd_handle.read(entry_size)

        # Detect object type
        object_type = self._detect_object_type(
        object_name)

        # Parse object header to find P-code
        pcode_offset, pcode_size = self._find_pcode_in_object(
        object_data,
        object_type,
        )

        if pcode_offset >= 0 and pcode_size > 0:
        pcode_bytes = object_data[pcode_offset: pcode_offset + pcode_size]
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
        pcode_info: Any = None,
        ) -> DecodedObject:
    """Decode a P-code section from extracted file data.

        Args:
        pcode_bytes: Raw P-code bytes from the detected offset
        object_name: Name of the object
        pcode_info: Optional P-code detection info

        Returns:
        Decoded object with instructions
    """
        # Detect version if not provided
        if self.version is None:
        logger.warning("No version specified, using default")
        self.version = PowerBuilderVersion(10, 5, True)

        # Load version-specific opcode table
        version_str = f"pb{self.version.major}_{self.version.minor}"
        self.opcode_table = get_opcodes_for_version(version_str)
        logger.debug(
        "Loaded opcode table for %s with %d opcodes",
        version_str,
        len(self.opcode_table),
        )

        # Check if we have multiple P-code sections from enhanced detection
        all_instructions = []

        # If pcode_info contains section information, use it
        if pcode_info and hasattr(pcode_info, "sections") and pcode_info.sections:
        logger.info(
        "Using enhanced detection: found %d P-code sections",
        len(pcode_info.sections),
        )
        # Log the total pcode_bytes length
        logger.debug("Total P-code data length: %d bytes", len(pcode_bytes))

        # Decode all sections
        for idx, section in enumerate(pcode_info.sections):
        logger.info(
        "Decoding section %d: offset = 0x%04x, length=%d, confidence=%.2f",
        idx + 1,
        section.offset,
        section.length,
        section.confidence,
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

        if len(section_data) > 0:
        # Log first few bytes of section data
        logger.debug(
        "Section %d first 16 bytes: %s",
        idx + 1,
        section_data[:16].hex()
        if len(section_data) >= 16:
        else section_data.hex(), :
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
        else:
        logger.warning("Section %d has no data", idx + 1)

        instructions = all_instructions
        else:
        # No section info - decode as single block
        logger.info("No section info available, decoding as single block")
        instructions = self.decode_pcode(pcode_bytes, 0, validate=True)

        logger.info("Total instructions decoded: %d", len(instructions))

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

        # Quick check: if the data starts with obvious non-P-code patterns, skip it
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
        if self.current_offset < len(pcode_bytes):
        else 0xFF, :
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
        next_bytes = pcode[self.current_offset: self.current_offset + 8]
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
        if len(self.instructions) < 10:
        logger.debug(
        "Decoding instruction %d at offset 0x%04x: opcode = 0x%02x",
        len(self.instructions) + 1,
        self.current_offset,
        op_byte,
        )

        # Check if this address is a jump target
        if address in self.labels:
        # We'll add the label in formatting
        pass

        # Check for variant opcodes first (DBFETCH, DBINSERT, etc.)
        if op_byte in [0x0E, 0x0F]:  # Known variant opcodes:
        variant_info = handle_variant_opcode(op_byte, pcode, self.current_offset)
        if variant_info:
        mnemonic, total_bytes, operand_values = variant_info

        # Move offset past the entire instruction
        self.current_offset += total_bytes

        # Extract operand bytes for display
        operand_bytes = pcode[address + 1: address + total_bytes]

        # Format instruction
        text_format = self._format_variant_instruction(
        address,
        mnemonic,
        operand_values,
        operand_bytes,
        )

        return PCodeInstruction(
        address = address,
        opcode = bytes([op_byte]),
        opcode_name = mnemonic,
        operands = operand_bytes,
        operand_values = operand_values,
        text_format = text_format,
        opcode_value = op_byte,
        )

        # Look up opcode from consolidated definitions
        opcode_info = get_opcode_info(op_byte)

        if opcode_info:
        mnemonic, operand_len, operand_hint = opcode_info

        self.current_offset += 1

        # Read operands
        operand_bytes = b""
        operand_values = []

        # The operand_len in the table includes the opcode byte
        # So actual operand bytes = operand_len - 1
        actual_operand_len = operand_len - 1

        if actual_operand_len > 0:
        if self.current_offset + actual_operand_len <= len(pcode):
        operand_bytes = pcode[
        self.current_offset : self.current_offset + actual_operand_len
        ]
        operand_values = self._decode_operands(operand_bytes, operand_hint)
        self.current_offset += actual_operand_len
        else:
        logger.warning("Insufficient bytes for operands at %04X", address)
        return None

        # Format instruction
        text_format = self._format_instruction(
        address,
        mnemonic,
        operand_values,
        operand_bytes,
        )

        return PCodeInstruction(
        address = address,
        opcode = bytes([op_byte]),
        opcode_name = mnemonic,
        operands = operand_bytes,
        operand_values = operand_values,
        text_format = text_format,
        opcode_value = op_byte,
        )

        # Truly unknown opcode - only mark as unknown if not in OPCODE_TABLE
        logger.debug(
        "Unknown opcode 0x%02X at %04X in %s", op_byte, address, self.version
        )

        # For unknown opcodes, try to make an educated guess about the length
        # Most PowerBuilder opcodes are 1-5 bytes
        # We'll assume 1 byte for now but could be smarter about this
        assumed_length = 1

        # Check if next bytes look like operands (usually small values)
        if (:
        self.current_offset + 1 < len(pcode)
        and pcode[self.current_offset + 1] < 0x10
        ):
        # Might have a single byte operand
        assumed_length = 2

        self.current_offset += assumed_length

        return PCodeInstruction(
        address = address,
        opcode = bytes([op_byte]),
        opcode_name = f"UNK_{op_byte:02X}",
        operands = pcode[
        self.current_offset - assumed_length + 1 : self.current_offset
        ]
        if assumed_length > 1:
        else b"", :
        operand_values=[],
        text_format= f"{address:04X}: DATA_{assumed_length} 0x{op_byte:02X}  ; Unknown opcode, assumed {assumed_length} bytes",
        opcode_value= op_byte,
        )

    def _decode_operands(self, operand_bytes: bytes, hint: str | None) -> list[Any]:
    """Decode operand bytes based on hint."""
        if not hint or not operand_bytes:
        return [operand_bytes.hex()]
        return [operand_bytes.hex()]

        try:
        if hint == "uint8":
        return [operand_bytes[0]]
        if hint == "int8":
        return [struct.unpack("b", operand_bytes)[0]]
        if hint == "uint16le":
        return [struct.unpack("<H", operand_bytes)[0]]
        if hint == "int16le":
        return [struct.unpack("<h", operand_bytes)[0]]
        if hint == "uint32le":
        return [struct.unpack("<I", operand_bytes)[0]]
        if hint == "int32le":
        return [struct.unpack("<i", operand_bytes)[0]]
        if hint == "relative_offset_byte":
        offset = struct.unpack("b", operand_bytes)[0]
        return [offset]
        if hint == "relative_offset_short":
        offset = struct.unpack("<h", operand_bytes)[0]
        return [offset]
        if hint == "relative_offset_int":
        offset = struct.unpack("<i", operand_bytes)[0]
        return [offset]
        if hint in ["string_index", "var_index", "method_index", "field_index"]:
        # These are typically 16-bit indices
        if len(operand_bytes) >= 2:
        return [struct.unpack("<H", operand_bytes[:2])[0]]
        return [operand_bytes[0]]
        # Unknown hint, return hex
        return [operand_bytes.hex()]
        except struct.error as e:
        logger.debug(
        "Failed to decode operands with hint '%s': %s, bytes: %s", hint, e, operand_bytes.hex()
        )
        return [operand_bytes.hex()]

    def _format_variant_instruction(
        self,
        address: int,
        mnemonic: str,
        operand_values: list[Any],
        _operand_bytes: bytes = b"",
        ) -> str:
    """Format variant instruction for output."""
        # Add label if this is a jump target
        prefix = ""
        if address in self.labels:
        prefix = f"\n{self.labels[address]}:\n"

        # Format the instruction with variant info
        operand_str = ", ".join(str(v) for v in operand_values)

        return f"{prefix}{address:04X}: {mnemonic:<12} {operand_str}"

    def _format_instruction(
        self,
        address: int,
        mnemonic: str,
        operand_values: list[Any],
        operand_bytes: bytes = b"",
        ) -> str:
    """Format instruction for output."""
        # Add label if this is a jump target
        prefix = ""
        if address in self.labels:
        prefix = f"\n{self.labels[address]}:\n"

        # Format operands
        if operand_values:
        # Special handling for jump targets
        if mnemonic in ["JUMP", "JUMPTRUE", "JUMPFALSE", "BRFALSE", "BRTRUE"]:
        if operand_values and isinstance(operand_values[0], int):
        # Calculate instruction length based on actual operand size
        inst_len = 1 + len(operand_bytes)
        target = address + inst_len + operand_values[0]
        if target in self.labels:
        operand_str = self.labels[target]
        else:
        operand_str = f"0x{target:04X}"
        else:
        operand_str = ", ".join(str(v) for v in operand_values)
        else:
        operand_str = ", ".join(str(v) for v in operand_values)

        return f"{prefix}{address:04X}: {mnemonic} {operand_str}"
        return f"{prefix}{address:04X}: {mnemonic}"

    def _identify_jump_targets(self, pcode: bytes, base_offset: int) -> None:
    """First pass to identify jump targets for labels."""
        offset = 0
        while offset < len(pcode):
        if offset < len(pcode):
        op_byte = pcode[offset]

        # Look up opcode from consolidated definitions
        opcode_info = get_opcode_info(op_byte)

        if opcode_info:
        mnemonic, operand_len, operand_hint = opcode_info

        # Check if it's a jump instruction
        if mnemonic in [:
        "JUMP",
        "JUMPTRUE",
        "JUMPFALSE",
        "BRFALSE",
        "BRTRUE",
        ]:
        actual_operand_len = operand_len - 1
        if (:
        offset + 1 + actual_operand_len <= len(pcode)
        and actual_operand_len > 0
        ):
        operand_bytes = pcode[
        offset + 1 : offset + 1 + actual_operand_len
        ]
        operand_values = self._decode_operands(
        operand_bytes,
        operand_hint,
        )

        if operand_values and isinstance(operand_values[0], int):
        # Calculate target address
        current_addr = base_offset + offset
        target = current_addr + operand_len + operand_values[0]

        # Add label for target
        if 0 <= target - base_offset < len(pcode):
        self.labels[target] = f"L_{target:04X}"

        offset += operand_len
        else:
        offset += 1

    def _find_pcode_in_object(
        self,
        object_data: bytes,
        object_type: str,
        ) -> tuple[int, int]:
    """Find P-code offset and size within object data.

        Args:
        object_data: Raw object data from PBD
        object_type: Type of object (function, window, etc.)

        Returns:
        Tuple of (pcode_offset, pcode_size), or (-1, 0) if not found
    """
        # Use the enhanced PCodeDetector for improved detection
        return EnhancedPCodeDetector.find_pcode_section(object_data, object_type)

    def _detect_object_type(self, object_name: str) -> str:
    """Detect object type from name."""
        name_lower = object_name.lower()

        # Check extension first
        if name_lower.endswith(".win"):
        return "window"
        if name_lower.endswith(".dwo"):
        return "datawindow"
        if name_lower.endswith(".udo"):
        return "userobject"
        if name_lower.endswith((".app", ".apl")):
        return "application"
        if name_lower.endswith(".men"):
        return "menu"
        if name_lower.endswith(".str"):
        return "structure"

        # For .fun files, check the prefix to determine the actual type
        if name_lower.endswith(".fun"):
        base_name = name_lower.split(".")[0]
        if base_name.startswith("w_"):
        return "window"
        if base_name.startswith(("u_", "n_")):
        return "userobject"
        if base_name.startswith("m_"):
        return "menu"
        if base_name.startswith(("f_", "of_")):
        return "function"
        # Default .fun to userobject since it's most common
        return "userobject"

        return "unknown"

    def _validate_instruction_sequence(
        self,
        instructions: list[PCodeInstruction],
        ) -> bool:
    """Validate that the decoded instruction sequence is reasonable.

        Args:
        instructions: List of decoded instructions

        Returns:
        True if the sequence passes validation
    """
        if not instructions:
        return False

        if len(instructions) < 3:  # Too few instructions:
        return True  # Allow short sequences

        # Count instruction types
        instruction_counts = {}
        unknown_count = 0
        for inst in instructions:
        opcode = inst.opcode_name
        instruction_counts[opcode] = instruction_counts.get(opcode, 0) + 1
        # Count unknown opcodes
        if opcode.startswith(("UNK_", "DATA_")):
        unknown_count += 1

        total_instructions = len(instructions)

        # If more than 50% of instructions are unknown, it's likely not P-code
        if unknown_count > total_instructions * 0.5:
        logger.warning(
        "Too many unknown opcodes: %d/%d "
        "(%.1f%%) - likely not P-code data",
        unknown_count, total_instructions, unknown_count / total_instructions * 100
        )
        return False

        # Check for excessive repetition of any single instruction
        for opcode, count in instruction_counts.items():
        repetition_ratio = count / total_instructions

        # If more than 90% of instructions are the same, it's likely wrong
        # (increased from 70% to allow for functions with many similar operations)
        if repetition_ratio > 0.9:
        logger.warning(
        "Excessive repetition: %s appears %d/%d times "
        "(%.1f%%)",
        opcode, count, total_instructions, repetition_ratio * 100
        )
        return False

        # Check for suspicious patterns that suggest we're decoding null bytes
        return_count = instruction_counts.get("RETURN", 0)
        if return_count > 0:
        return_ratio = return_count / total_instructions

        # Check for excessive consecutive RETURN statements (common with null padding)
        consecutive_returns = self._count_consecutive_returns(instructions)
        max_consecutive = max(consecutive_returns) if consecutive_returns else 0

        # If we see more than 3 consecutive returns, that's suspicious
        # (reduced from 50 to catch bad data earlier)
        if max_consecutive > 3:
        logger.warning(
        "Found %d consecutive RETURN instructions - likely padding/non-P-code data", max_consecutive
        )
        return False

        # If more than 50% are RETURN instructions, that's very suspicious
        # (reduced from 70% to be more strict)
        if return_ratio > 0.5:
        logger.warning(
        "High RETURN ratio: %d/%d "
        "(%.1f%%) - likely decoding non-P-code data",
        return_count, total_instructions, return_ratio * 100
        )
        return False

        return True

    def _count_consecutive_returns(
        self,
        instructions: list[PCodeInstruction],
        ) -> list[int]:
    """Count consecutive RETURN statements in instruction sequence.

        Args:
        instructions: List of decoded instructions

        Returns:
        List of consecutive RETURN sequence lengths
    """
        consecutive_sequences = []
        current_sequence = 0

        for inst in instructions:
        if inst.opcode_name == "RETURN":
        current_sequence += 1
        elif current_sequence > 0:
        consecutive_sequences.append(current_sequence)
        current_sequence = 0

        # Don't forget the last sequence
        if current_sequence > 0:
        consecutive_sequences.append(current_sequence)

        return consecutive_sequences
