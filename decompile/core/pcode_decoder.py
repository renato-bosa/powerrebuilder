"""PowerBuilder P-code binary decoder with version awareness.

This module implements a version-aware decoder for PowerBuilder P-code binary format,
using version-specific opcode tables as recommended in the decompiler guide.
"""

import logging
import struct
from dataclasses import dataclass, field
from typing import Any, BinaryIO

from decompile.analysis.pcode_detector import EnhancedPCodeDetector
from decompile.opcodes import OpcodeManager, get_opcode_info
from extract.pbd.utils.version_detector import PBVersionDetector as VersionDetector
from extract.pbd.utils.version_detector import PowerBuilderVersion

logger = logging.getLogger(__name__)


@dataclass
class PCodeInstruction:
    """Represents a single P-code instruction."""

    address: int
    opcode: bytes
    opcode_name: str
    operands: bytes
    operand_values: list[Any]
    text_format: str
    opcode_value: int | None = None


@dataclass
class DecodedObject:
    """Represents a decoded PowerBuilder object."""

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
        self, pbd_handle: BinaryIO, entry_offset: int, entry_size: int, object_name: str
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
                self.version = VersionDetector.detect_from_file(pbd_handle)
                if self.version is None:
                    logger.warning("Could not detect version, using default")
                    self.version = VersionDetector.get_default_version()

            # Load version-specific opcode table
            self.opcode_table = OpcodeManager.get_opcode_table(self.version)
            logger.info(f"Using opcode table for {self.version}")

            # Seek to object data
            pbd_handle.seek(entry_offset)
            object_data = pbd_handle.read(entry_size)

            # Detect object type
            object_type = self._detect_object_type(object_name)

            # Parse object header to find P-code
            pcode_offset, pcode_size = self._find_pcode_in_object(
                object_data, object_type
            )

            if pcode_offset >= 0 and pcode_size > 0:
                pcode_bytes = object_data[pcode_offset : pcode_offset + pcode_size]
                instructions = self.decode_pcode(
                    pcode_bytes, entry_offset + pcode_offset
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
        self, pcode_bytes: bytes, object_name: str, pcode_info: Any = None
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
        self.opcode_table = OpcodeManager.get_opcode_table(self.version)

        # Decode the P-code
        instructions = self.decode_pcode(pcode_bytes, 0)

        # Determine object type from name
        object_type = self._detect_object_type(object_name)
        logger.debug(f"Detected object type '{object_type}' for '{object_name}'")

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
        self, pcode_bytes: bytes, base_offset: int = 0
    ) -> list[PCodeInstruction]:
        """Decode P-code bytes into instructions.

        Args:
            pcode_bytes: Raw P-code bytes
            base_offset: Base offset for addresses

        Returns:
            List of decoded instructions
        """
        self.reset()
        self.current_offset = 0

        # First pass - identify jump targets
        self._identify_jump_targets(pcode_bytes, base_offset)

        # Second pass - decode instructions
        self.current_offset = 0
        while self.current_offset < len(pcode_bytes):
            instruction = self._decode_next_instruction(pcode_bytes, base_offset)
            if instruction:
                self.instructions.append(instruction)

        # Validate the decoded instruction sequence
        if not self._validate_instruction_sequence(self.instructions):
            logger.warning("Decoded instruction sequence failed validation")
            return []

        return self.instructions

    def _decode_next_instruction(
        self, pcode: bytes, base_offset: int
    ) -> PCodeInstruction | None:
        """Decode the next instruction at current offset."""
        if self.current_offset >= len(pcode):
            return None

        address = base_offset + self.current_offset
        op_byte = pcode[self.current_offset]

        # Check if this address is a jump target
        if address in self.labels:
            # We'll add the label in formatting
            pass

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
                    logger.warning(f"Insufficient bytes for operands at {address:04X}")
                    return None

            # Format instruction
            text_format = self._format_instruction(
                address, mnemonic, operand_values, operand_bytes
            )

            return PCodeInstruction(
                address=address,
                opcode=bytes([op_byte]),
                opcode_name=mnemonic,
                operands=operand_bytes,
                operand_values=operand_values,
                text_format=text_format,
                opcode_value=op_byte,
            )
        # Fall back to version-specific table if not in YAML
        if op_byte in self.opcode_table:
            mnemonic, operand_len, operand_hint = self.opcode_table[op_byte]
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
                    logger.warning(f"Insufficient bytes for operands at {address:04X}")
                    return None

            # Format instruction
            text_format = self._format_instruction(
                address, mnemonic, operand_values, operand_bytes
            )

            return PCodeInstruction(
                address=address,
                opcode=bytes([op_byte]),
                opcode_name=mnemonic,
                operands=operand_bytes,
                operand_values=operand_values,
                text_format=text_format,
                opcode_value=op_byte,
            )
        # Unknown opcode
        logger.warning(
            f"Unknown opcode 0x{op_byte:02X} at {address:04X} in {self.version}"
        )
        self.current_offset += 1

        return PCodeInstruction(
            address=address,
            opcode=bytes([op_byte]),
            opcode_name=f"UNK_{op_byte:02X}",
            operands=b"",
            operand_values=[],
            text_format=f"{address:04X}: DATA 0x{op_byte:02X}  ; Unknown opcode",
            opcode_value=op_byte,
        )

    def _decode_operands(self, operand_bytes: bytes, hint: str | None) -> list[Any]:
        """Decode operand bytes based on hint."""
        if not hint or not operand_bytes:
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
                f"Failed to decode operands with hint '{hint}': {e}, bytes: {operand_bytes.hex()}"
            )
            return [operand_bytes.hex()]

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
                    if mnemonic in [
                        "JUMP",
                        "JUMPTRUE",
                        "JUMPFALSE",
                        "BRFALSE",
                        "BRTRUE",
                    ]:
                        actual_operand_len = operand_len - 1
                        if (
                            offset + 1 + actual_operand_len <= len(pcode)
                            and actual_operand_len > 0
                        ):
                            operand_bytes = pcode[
                                offset + 1 : offset + 1 + actual_operand_len
                            ]
                            operand_values = self._decode_operands(
                                operand_bytes, operand_hint
                            )

                            if operand_values and isinstance(operand_values[0], int):
                                # Calculate target address
                                current_addr = base_offset + offset
                                target = current_addr + operand_len + operand_values[0]

                                # Add label for target
                                if 0 <= target - base_offset < len(pcode):
                                    self.labels[target] = f"L_{target:04X}"

                    offset += operand_len
                elif op_byte in self.opcode_table:
                    mnemonic, operand_len, operand_hint = self.opcode_table[op_byte]

                    # Check if it's a jump instruction
                    if mnemonic in [
                        "JUMP",
                        "JUMPTRUE",
                        "JUMPFALSE",
                        "BRFALSE",
                        "BRTRUE",
                    ]:
                        actual_operand_len = operand_len - 1
                        if (
                            offset + 1 + actual_operand_len <= len(pcode)
                            and actual_operand_len > 0
                        ):
                            operand_bytes = pcode[
                                offset + 1 : offset + 1 + actual_operand_len
                            ]
                            operand_values = self._decode_operands(
                                operand_bytes, operand_hint
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
        self, object_data: bytes, object_type: str
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

    def _validate_instruction_sequence(self, instructions: list[PCodeInstruction]) -> bool:
        """Validate that the decoded instruction sequence is reasonable.
        
        Args:
            instructions: List of decoded instructions
            
        Returns:
            True if the sequence passes validation
        """
        if not instructions:
            return False
            
        if len(instructions) < 3:  # Too few instructions
            return True  # Allow short sequences
            
        # Count instruction types
        instruction_counts = {}
        for inst in instructions:
            opcode = inst.opcode_name
            instruction_counts[opcode] = instruction_counts.get(opcode, 0) + 1
            
        total_instructions = len(instructions)
        
        # Check for excessive repetition of any single instruction
        for opcode, count in instruction_counts.items():
            repetition_ratio = count / total_instructions
            
            # If more than 70% of instructions are the same, it's likely wrong
            if repetition_ratio > 0.7:
                logger.warning(
                    f"Excessive repetition: {opcode} appears {count}/{total_instructions} times "
                    f"({repetition_ratio:.1%})"
                )
                return False
                
        # Check for suspicious patterns that suggest we're decoding null bytes
        return_count = instruction_counts.get("RETURN", 0)
        if return_count > 0:
            return_ratio = return_count / total_instructions
            
            # Check for excessive consecutive RETURN statements (common with null padding)
            consecutive_returns = self._count_consecutive_returns(instructions)
            max_consecutive = max(consecutive_returns) if consecutive_returns else 0
            
            # If we have many consecutive returns AND high return ratio, it's likely null decoding
            if return_ratio > 0.5 and max_consecutive > 20:
                logger.warning(
                    f"Suspicious RETURN pattern: {return_count}/{total_instructions} "
                    f"({return_ratio:.1%}) with {max_consecutive} consecutive - likely null bytes"
                )
                return False
                
            # Very high return ratio (>80%) is almost certainly wrong
            if return_ratio > 0.8:
                logger.warning(
                    f"Excessive RETURN statements: {return_count}/{total_instructions} "
                    f"({return_ratio:.1%}) - likely decoding null bytes"
                )
                return False
                
        return True

    def _count_consecutive_returns(self, instructions: list[PCodeInstruction]) -> list[int]:
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
            else:
                if current_sequence > 0:
                    consecutive_sequences.append(current_sequence)
                    current_sequence = 0
                    
        # Don't forget the last sequence
        if current_sequence > 0:
            consecutive_sequences.append(current_sequence)
            
        return consecutive_sequences
