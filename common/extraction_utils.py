"""Common extraction utilities for PowerBuilder decompilation.

This module consolidates common extraction patterns used across the codebase:
- File content extraction (PBD, PDW, PBL)
- P-code extraction and processing
- Binary data parsing
- Content transformation utilities
"""

import hashlib
import struct
from pathlib import Path
from typing import Any, BinaryIO

from src.common.exceptions import ExtractionError
from src.common.utils.logging import get_logger

logger = get_logger(__name__)


class BinaryReader:
    """Utility class for reading binary data with various formats."""

    def __init__(self, data: bytes) -> None:
        """Initialize binary reader with data."""
        self.data = data
        self.pos = 0

    def read_bytes(self, count: int) -> bytes:
        """Read specified number of bytes."""
        if self.pos + count > len(self.data):
            raise ExtractionError(f"Attempt to read {count} bytes beyond data boundary")
        result = self.data[self.pos : self.pos + count]
        self.pos += count
        return result

    def read_uint8(self) -> int:
        """Read unsigned 8-bit integer."""
        return struct.unpack("<B", self.read_bytes(1))[0]

    def read_uint16(self) -> int:
        """Read unsigned 16-bit integer (little-endian)."""
        return struct.unpack("<H", self.read_bytes(2))[0]

    def read_uint32(self) -> int:
        """Read unsigned 32-bit integer (little-endian)."""
        return struct.unpack("<I", self.read_bytes(4))[0]

    def read_int16(self) -> int:
        """Read signed 16-bit integer (little-endian)."""
        return struct.unpack("<h", self.read_bytes(2))[0]

    def read_int32(self) -> int:
        """Read signed 32-bit integer (little-endian)."""
        return struct.unpack("<i", self.read_bytes(4))[0]

    def read_string(self, encoding: str = "utf-16-le") -> str:
        """Read null-terminated string."""
        chars = []
        while True:
            if encoding == "utf-16-le":
                char_bytes = self.read_bytes(2)
                if char_bytes == b"\x00\x00":
                    break
                chars.append(char_bytes)
            else:
                char_byte = self.read_bytes(1)
                if char_byte == b"\x00":
                    break
                chars.append(char_byte)
        
        if chars:
            return b"".join(chars).decode(encoding, errors="replace")
        return ""

    def read_fixed_string(self, length: int, encoding: str = "utf-16-le") -> str:
        """Read fixed-length string."""
        data = self.read_bytes(length)
        # Remove null terminators
        if encoding == "utf-16-le":
            data = data.rstrip(b"\x00\x00")
        else:
            data = data.rstrip(b"\x00")
        return data.decode(encoding, errors="replace")

    @property
    def remaining(self) -> int:
        """Get number of remaining bytes."""
        return len(self.data) - self.pos

    def seek(self, position: int) -> None:
        """Seek to specific position."""
        if position < 0 or position > len(self.data):
            raise ExtractionError(f"Invalid seek position: {position}")
        self.pos = position


def extract_pcode_section(data: bytes, offset: int, size: int) -> bytes | None:
    """Extract P-code section from binary data.
    
    Args:
        data: Binary data containing P-code
        offset: Starting offset of P-code section
        size: Size of P-code section
        
    Returns:
        Extracted P-code bytes or None if invalid
    """
    try:
        if offset < 0 or size < 0:
            logger.error(f"Invalid P-code offset/size: {offset}/{size}")
            return None
            
        if offset + size > len(data):
            logger.error(f"P-code section exceeds data bounds: {offset}+{size} > {len(data)}")
            return None
            
        pcode_data = data[offset : offset + size]
        
        # Validate P-code data (basic checks)
        if not pcode_data:
            logger.warning("Empty P-code section")
            return None
            
        # Check for valid P-code signature patterns
        if len(pcode_data) >= 4:
            # Common P-code starts with specific opcodes
            first_byte = pcode_data[0]
            if first_byte not in {0x01, 0x02, 0x03, 0x10, 0x20, 0x30}:
                logger.debug(f"Unusual P-code start byte: 0x{first_byte:02x}")
        
        return pcode_data
        
    except Exception as e:
        logger.error(f"Error extracting P-code: {e}")
        return None


def calculate_checksum(data: bytes) -> str:
    """Calculate SHA-256 checksum of data."""
    return hashlib.sha256(data).hexdigest()


def read_variable_length_int(reader: BinaryReader) -> int:
    """Read variable-length integer (used in some P-code formats)."""
    result = 0
    shift = 0
    
    while True:
        byte = reader.read_uint8()
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
        
    return result


def decode_powerbuilder_string(data: bytes, offset: int = 0) -> tuple[str, int]:
    """Decode PowerBuilder string from binary data.
    
    Args:
        data: Binary data containing string
        offset: Starting offset
        
    Returns:
        Tuple of (decoded_string, bytes_consumed)
    """
    reader = BinaryReader(data[offset:])
    
    # PowerBuilder strings can be encoded in different ways
    # Try to detect the encoding
    if reader.remaining >= 2:
        first_two = reader.data[:2]
        if first_two == b"\xff\xfe":  # UTF-16 LE BOM
            reader.read_bytes(2)  # Skip BOM
            string_data = reader.read_string("utf-16-le")
            return string_data, reader.pos + offset
    
    # Default to UTF-16 LE without BOM
    string_data = reader.read_string("utf-16-le")
    return string_data, reader.pos


def extract_metadata_from_header(data: bytes) -> dict[str, Any]:
    """Extract metadata from PowerBuilder file header.
    
    Args:
        data: File header data
        
    Returns:
        Dictionary containing extracted metadata
    """
    metadata = {}
    
    try:
        reader = BinaryReader(data)
        
        # Common PowerBuilder file header structure
        if reader.remaining >= 4:
            signature = reader.read_bytes(4)
            metadata["signature"] = signature.hex()
            
        if reader.remaining >= 4:
            version = reader.read_uint32()
            metadata["version"] = version
            
        if reader.remaining >= 4:
            file_type = reader.read_uint32()
            metadata["file_type"] = file_type
            
        # Read creation timestamp if present
        if reader.remaining >= 8:
            timestamp = reader.read_uint32()
            metadata["timestamp"] = timestamp
            
    except Exception as e:
        logger.debug(f"Error extracting metadata: {e}")
        
    return metadata


def find_pcode_markers(data: bytes) -> list[int]:
    """Find potential P-code section markers in binary data.
    
    Args:
        data: Binary data to search
        
    Returns:
        List of offsets where P-code sections might start
    """
    markers = []
    
    # Common P-code section markers
    pcode_signatures = [
        b"PCOD",  # P-code marker
        b"FUNC",  # Function marker
        b"METH",  # Method marker
        b"\x01\x00\x00\x00",  # Common P-code start
        b"\x02\x00\x00\x00",  # Alternative start
    ]
    
    for signature in pcode_signatures:
        offset = 0
        while True:
            pos = data.find(signature, offset)
            if pos == -1:
                break
            markers.append(pos)
            offset = pos + 1
            
    # Remove duplicates and sort
    markers = sorted(set(markers))
    
    return markers


def validate_pcode_structure(pcode_data: bytes) -> bool:
    """Validate P-code structure for basic integrity.
    
    Args:
        pcode_data: P-code bytes to validate
        
    Returns:
        True if structure appears valid
    """
    if not pcode_data or len(pcode_data) < 4:
        return False
        
    try:
        reader = BinaryReader(pcode_data)
        
        # Check for valid opcode at start
        first_opcode = reader.read_uint8()
        if first_opcode == 0x00 or first_opcode > 0xFE:
            return False
            
        # Try to parse a few instructions
        instruction_count = 0
        while reader.remaining > 0 and instruction_count < 10:
            opcode = reader.read_uint8()
            
            # Skip operands based on opcode (simplified)
            if opcode in {0x01, 0x02, 0x03}:  # No operands
                pass
            elif opcode in {0x10, 0x11, 0x12}:  # 1 byte operand
                if reader.remaining < 1:
                    return False
                reader.read_uint8()
            elif opcode in {0x20, 0x21, 0x22}:  # 2 byte operand
                if reader.remaining < 2:
                    return False
                reader.read_uint16()
            elif opcode in {0x30, 0x31, 0x32}:  # 4 byte operand
                if reader.remaining < 4:
                    return False
                reader.read_uint32()
            else:
                # Unknown opcode structure
                pass
                
            instruction_count += 1
            
        return True
        
    except Exception:
        return False


def extract_file_safely(file_path: Path, output_dir: Path) -> Path | None:
    """Safely extract file content to output directory.
    
    Args:
        file_path: Source file path
        output_dir: Output directory
        
    Returns:
        Path to extracted file or None on error
    """
    try:
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe output filename
        safe_name = file_path.name.replace("..", "_")
        output_path = output_dir / safe_name
        
        # Read and write file
        with open(file_path, "rb") as f:
            content = f.read()
            
        with open(output_path, "wb") as f:
            f.write(content)
            
        logger.debug(f"Extracted {file_path} to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to extract {file_path}: {e}")
        return None