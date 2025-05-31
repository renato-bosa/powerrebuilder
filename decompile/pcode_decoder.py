"""PowerBuilder P-code binary decoder.

This module implements a decoder for PowerBuilder P-code binary format,
converting binary opcodes into readable text format for decompile_structured.py.
"""

import logging
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

# Import from the opcodes module
from extract.pbd_core.opcodes import (
    attempt_symbolic_fallback,
    get_opcode_info,
    load_opcodes,
    log_unknown_opcode,
)

logger = logging.getLogger(__name__)


@dataclass
class PCodeInstruction:
    """Represents a single P-code instruction."""
    address: int
    opcode: bytes
    opcode_name: str
    operands: bytes
    operand_values: list[Any]
    text_format: str  # Format for decompile_structured.py


class PCodeDecoder:
    """Decoder for PowerBuilder P-code binary format."""

    def __init__(self) -> None:
        """Initialize the decoder."""
        # Use the opcodes module to load definitions
        self.opcodes = load_opcodes()
        self.reset()
        self.current_file = None  # Track current file for logging

    def reset(self) -> None:
        """Reset decoder state."""
        self.instructions = []
        self.strings = {}
        self.current_offset = 0
        self.labels = {}  # For jump targets

    def decode_file(self, file_path: Path) -> List[str]:
        """Decode a P-code file and return as text lines.
        
        Args:
            file_path: Path to the P-code file
            
        Returns:
            List of text lines representing the decoded P-code
        """
        print(f"  Reading file: {file_path}")
        with open(file_path, 'rb') as f:
            data = f.read()
        
        print(f"  File size: {len(data)} bytes")
        
        # Find the start of P-code
        pcode_start = self._find_pcode_start(data)
        if pcode_start == -1:
            logger.warning(f"No P-code marker found in {file_path}")
            return []
        
        print(f"  P-code starts at offset: {pcode_start}")
        
        # Extract P-code section
        pcode = data[pcode_start:]
        print(f"  P-code size: {len(pcode)} bytes")
        
        # Decode the P-code
        print("  Decoding instructions...")
        instructions = self.decode_pcode(pcode, pcode_start)
        print(f"  Decoded {len(instructions)} instructions")
        
        # Format as text
        print("  Formatting as text...")
        text_lines = self._format_instructions_as_text(instructions)
        print(f"  Formatted {len(text_lines)} lines")
        
        return text_lines

    def _find_pcode_start(self, data: bytes) -> int:
        """Find the start of P-code after headers."""
        header2 = b'$PBExportComments$'
        pos = data.find(header2)
        if pos >= 0:
            # Find end of header line
            end = data.find(b'\n', pos)
            if end >= 0:
                return end + 1
        return -1

    def _detect_string(self, pcode: bytes, offset: int) -> tuple[str, int] | None:
        """Detect if there's an ASCII or UTF-8 string at the current offset.

        Args:
            pcode: The P-code bytes
            offset: Current offset

        Returns:
            Tuple of (string, length) if a string is detected, None otherwise
        """
        # Check if we have at least 4 consecutive printable ASCII chars
        if offset + 4 > len(pcode):
            return None

        # First check for UTF-8 strings (common Chinese/Japanese/Korean characters)
        # UTF-8 3-byte sequences often start with E4-E9 for CJK
        if offset + 3 <= len(pcode):
            byte1 = pcode[offset]
            if 0xE4 <= byte1 <= 0xE9:  # Common CJK UTF-8 range
                try:
                    # Try to decode as UTF-8
                    test_len = min(30, len(pcode) - offset)  # Test up to 30 bytes
                    test_bytes = pcode[offset:offset + test_len]

                    # Find the end of valid UTF-8
                    valid_len = 0
                    i = 0
                    while i < len(test_bytes):
                        try:
                            # Decode one character at a time
                            char_len = 1
                            if test_bytes[i] & 0x80:  # Multi-byte
                                if test_bytes[i] & 0xE0 == 0xC0:
                                    char_len = 2
                                elif test_bytes[i] & 0xF0 == 0xE0:
                                    char_len = 3
                                elif test_bytes[i] & 0xF8 == 0xF0:
                                    char_len = 4

                            if i + char_len <= len(test_bytes):
                                test_bytes[i:i+char_len].decode('utf-8')
                                valid_len = i + char_len
                                i += char_len
                            else:
                                break
                        except:
                            break

                    if valid_len >= 3:  # At least one UTF-8 character
                        utf8_string = pcode[offset:offset + valid_len].decode('utf-8', errors='ignore')
                        if len(utf8_string) >= 1:  # Valid UTF-8 string
                            return f"UTF8:{utf8_string}", valid_len
                except:
                    pass

        # Look for sequences of printable ASCII followed by null terminator
        string_chars = []
        i = offset

        while i < len(pcode):
            byte = pcode[i]
            # Check for printable ASCII (space to ~)
            if 32 <= byte <= 126:
                string_chars.append(chr(byte))
                i += 1
            elif byte == 0 and len(string_chars) >= 3:  # Null terminator after at least 3 chars
                # Found a null-terminated string
                return ''.join(string_chars), i - offset + 1
            else:
                # Not a string or string ended without null terminator
                break

        # Check if we found a reasonable string (at least 4 chars)
        if len(string_chars) >= 4:
            # Even without null terminator, could be a string constant
            return ''.join(string_chars), len(string_chars)

        return None

    def decode_pcode(self, pcode: bytes, base_offset: int = 0) -> list[PCodeInstruction]:
        """Decode P-code bytes into instructions.

        Args:
            pcode: P-code bytes to decode
            base_offset: Base offset for addresses

        Returns:
            List of decoded instructions
        """
        self.reset()
        self.current_offset = 0

        # First pass - identify jump targets
        self._identify_jump_targets(pcode, base_offset)

        # Second pass - decode instructions
        self.current_offset = 0
        while self.current_offset < len(pcode):
            instruction = self._decode_next_instruction(pcode, base_offset)
            if instruction:
                self.instructions.append(instruction)
            else:
                # Skip unknown byte
                self.current_offset += 1

        return self.instructions

    def _identify_jump_targets(self, pcode: bytes, base_offset: int) -> None:
        """First pass to identify jump targets for labels."""
        offset = 0
        while offset < len(pcode):
            if offset + 1 < len(pcode):
                opcode = pcode[offset]

                # Check for jump instructions
                if opcode == 0xD4 and offset + 1 < len(pcode) and pcode[offset + 1] == 0x80:
                    # JUMP instruction - read target
                    if offset + 5 < len(pcode):
                        target = struct.unpack('<I', pcode[offset + 2:offset + 6])[0]
                        if target < len(pcode):
                            self.labels[base_offset + target] = f"L_{target:04X}"
                        offset += 6
                        continue

                elif opcode == 0xE0 and offset + 1 < len(pcode):
                    variant = pcode[offset + 1]
                    if variant in [0xB4, 0xBC]:  # JUMP_IF_FALSE, JUMP_IF_TRUE
                        if offset + 5 < len(pcode):
                            target = struct.unpack('<I', pcode[offset + 2:offset + 6])[0]
                            if target < len(pcode):
                                self.labels[base_offset + target] = f"L_{target:04X}"
                            offset += 6
                            continue

            offset += 1

    def _decode_next_instruction(self, pcode: bytes, base_offset: int) -> PCodeInstruction | None:
        """Decode the next instruction at current offset."""
        if self.current_offset >= len(pcode):
            return None

        address = base_offset + self.current_offset
        remaining = pcode[self.current_offset:]

        # First check if this is the start of a string
        string_result = self._detect_string(pcode, self.current_offset)
        if string_result:
            string_text, string_len = string_result
            self.current_offset += string_len

            # Create a STRING pseudo-instruction
            return PCodeInstruction(
                address=address,
                opcode=b'',  # No actual opcode for strings
                opcode_name="STRING",
                operands=pcode[self.current_offset - string_len:self.current_offset],
                operand_values=[string_text],
                text_format=f"{address:04X}: STRING \"{string_text}\"",
            )

        # Try to decode based on opcode definitions
        opcode_byte = remaining[0]

        # Use get_opcode_info from opcodes module
        opcode_info = get_opcode_info(opcode_byte)

        if opcode_info:
            # Check if it's a single-byte opcode
            if 'mnemonic' in opcode_info:
                return self._decode_simple_opcode(address, opcode_byte, opcode_info, remaining)

            # Check for variant opcodes
            if 'variants' in opcode_info and len(remaining) > 1:
                variant_byte = remaining[1]

                # Debug logging for E6 B8
                if opcode_byte == 0xE6 and variant_byte == 0xB8:
                    logger.debug(f"DEBUG: Found E6 B8 at {address:04X}")
                    logger.debug(f"  Variants in opcode_info: {list(opcode_info['variants'].keys())}")
                    logger.debug(f"  Looking for variant: {variant_byte} (0x{variant_byte:02X})")

                if variant_byte in opcode_info['variants']:
                    variant_def = opcode_info['variants'][variant_byte]
                    return self._decode_variant_opcode(address, bytes([opcode_byte, variant_byte]),
                                                     variant_def, remaining[2:])
                # Debug for unrecognized variants
                if opcode_byte == 0xE6:
                    logger.debug(f"DEBUG: E6 variant {variant_byte:02X} not found in variants")

        # Unknown opcode - log it and create generic instruction
        return self._decode_unknown_opcode(address, remaining, pcode)

    def _decode_simple_opcode(self, address: int, opcode: int, definition: dict,
                             data: bytes) -> PCodeInstruction:
        """Decode a simple single-byte opcode."""
        self.current_offset += 1

        mnemonic = definition['mnemonic']
        operands = []
        operand_bytes = b''

        # No operands for simple opcodes like NOP, MARKER, etc.
        text_format = f"{address:04X}: {mnemonic}"

        return PCodeInstruction(
            address=address,
            opcode=bytes([opcode]),
            opcode_name=mnemonic,
            operands=operand_bytes,
            operand_values=operands,
            text_format=text_format,
        )

    def _decode_variant_opcode(self, address: int, opcode: bytes, definition: dict,
                              data: bytes) -> PCodeInstruction:
        """Decode an opcode with variants."""
        self.current_offset += 2  # Base + variant byte

        mnemonic = definition['mnemonic']
        operands = []
        operand_bytes = b''

        # Decode operands based on definition
        if 'operands' in definition and definition['operands']:
            for operand_type in definition['operands']:
                if operand_type == 'byte_value' and len(data) >= 1:
                    operand_bytes = data[0:1]
                    operands.append(data[0])
                    self.current_offset += 1

                elif operand_type == 'int16_value' and len(data) >= 2:
                    operand_bytes = data[0:2]
                    value = struct.unpack('<H', data[0:2])[0]
                    operands.append(value)
                    self.current_offset += 2

                elif operand_type == 'int32_value' and len(data) >= 4:
                    operand_bytes = data[0:4]
                    value = struct.unpack('<I', data[0:4])[0]
                    operands.append(value)
                    self.current_offset += 4

                elif operand_type == 'target_offset' and len(data) >= 4:
                    operand_bytes = data[0:4]
                    target = struct.unpack('<I', data[0:4])[0]
                    # Use label if available
                    if address + target in self.labels:
                        operands.append(self.labels[address + target])
                    else:
                        operands.append(f"0x{target:04X}")
                    self.current_offset += 4

                elif operand_type in ['var_index', 'field_index', 'string_index',
                                    'object_index', 'array_ref']:
                    if len(data) >= 2:
                        operand_bytes = data[0:2]
                        value = struct.unpack('<H', data[0:2])[0]
                        operands.append(value)
                        self.current_offset += 2

        # Format for decompile_structured.py
        if operands:
            operand_str = ', '.join(str(op) for op in operands)
            text_format = f"{address:04X}: {mnemonic} {operand_str}"
        else:
            text_format = f"{address:04X}: {mnemonic}"

        return PCodeInstruction(
            address=address,
            opcode=opcode,
            opcode_name=mnemonic,
            operands=operand_bytes,
            operand_values=operands,
            text_format=text_format,
        )

    def _decode_unknown_opcode(self, address: int, data: bytes, full_pcode: bytes) -> PCodeInstruction:
        """Handle unknown opcodes with logging."""
        opcode = bytes([data[0]])
        opcode_value = data[0]

        # Don't log ASCII characters as unknown opcodes
        if 32 <= opcode_value <= 126:
            # This is likely part of a string that wasn't detected
            # Don't log it, just create a DATA instruction
            self.current_offset += 1
            return PCodeInstruction(
                address=address,
                opcode=opcode,
                opcode_name="CHAR",
                operands=b'',
                operand_values=[chr(opcode_value)],
                text_format=f"{address:04X}: DATA 0x{opcode[0]:02X}  ; '{chr(opcode_value)}'",
            )

        self.current_offset += 1

        # Get context bytes for logging (3 before, opcode, 3 after)
        context_start = max(0, self.current_offset - 4)  # -4 because we already incremented
        context_end = min(len(full_pcode), self.current_offset + 3)
        context_bytes = full_pcode[context_start:context_end]

        # Log the unknown opcode
        log_unknown_opcode(
            opcode_value=opcode_value,
            context_bytes_around=context_bytes,
            stream_position=address,
            source_object_name=self.current_file or "unknown",
            note=f"Unknown opcode encountered in {self.current_file}",
        )

        # Try symbolic fallback
        attempt_symbolic_fallback(
            opcode_value=opcode_value,
            operand_bytes=data[1:5] if len(data) > 1 else None,
            source_object_name=self.current_file,
        )

        # Create a generic instruction
        text_format = f"{address:04X}: DATA 0x{opcode[0]:02X}"

        return PCodeInstruction(
            address=address,
            opcode=opcode,
            opcode_name=f"UNK_{opcode[0]:02X}",
            operands=b'',
            operand_values=[],
            text_format=text_format,
        )

    def _format_instructions_as_text(self, instructions: list[PCodeInstruction]) -> list[str]:
        """Format instructions as text for decompile_structured.py."""
        lines = []

        for inst in instructions:
            # Add label if this address is a jump target
            if inst.address in self.labels:
                lines.append(f"{self.labels[inst.address]}:")

            lines.append(inst.text_format)

        return lines


def decode_and_save(input_file: Path, output_file: Path):
    """Decode a P-code file and save the results."""
    print(f"Starting decode of {input_file.name}...")
    
    # Initialize decoder
    decoder = PCodeDecoder()
    
    # Decode the file
    print("Decoding P-code...")
    try:
        output_lines = decoder.decode_file(input_file)
        print(f"Decoded {len(output_lines)} lines")
    except Exception as e:
        print(f"Error during decoding: {e}")
        raise
    
    # Save to output file
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"✅ Decode complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python pcode_decoder.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    decode_and_save(input_file, output_file)
