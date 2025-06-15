"""PowerBuilder version detection module.

This module implements version detection for PowerBuilder PBD/PBL files
based on header signatures, entry formats, and opcode patterns.
"""

import logging
from dataclasses import dataclass
from typing import BinaryIO

logger = logging.getLogger(__name__)


@dataclass
class PowerBuilderVersion:
    """Represents a detected PowerBuilder version."""

    major: int
    minor: int
    is_unicode: bool

    def __str__(self) -> str:
        """Return version string like 'pb10_5'."""
        return f"pb{self.major}_{self.minor}"

    def __repr__(self) -> str:
        """Return detailed version representation."""
        unicode_str = " (Unicode)" if self.is_unicode else ""
        return f"PowerBuilder {self.major}.{self.minor}{unicode_str}"


class PBVersionDetector:
    """Detects PowerBuilder version from PBD/PBL files."""

    # Known version signatures and patterns
    VERSION_SIGNATURES = {
        # PowerBuilder 5
        b"HDR\x00\x05\x00": PowerBuilderVersion(5, 0, False),
        # PowerBuilder 6
        b"HDR\x00\x06\x00": PowerBuilderVersion(6, 0, False),
        b"HDR\x00\x06\x05": PowerBuilderVersion(6, 5, False),
        # PowerBuilder 7
        b"HDR\x00\x07\x00": PowerBuilderVersion(7, 0, False),
        # PowerBuilder 8
        b"HDR\x00\x08\x00": PowerBuilderVersion(8, 0, False),
        # PowerBuilder 9
        b"HDR\x00\x09\x00": PowerBuilderVersion(9, 0, False),
        # PowerBuilder 10 (Unicode introduced)
        b"HDR*\x0a\x00": PowerBuilderVersion(10, 0, True),
        b"HDR*\x0a\x05": PowerBuilderVersion(10, 5, True),
        # PowerBuilder 11
        b"HDR*\x0b\x00": PowerBuilderVersion(11, 0, True),
        b"HDR*\x0b\x05": PowerBuilderVersion(11, 5, True),
        # PowerBuilder 12
        b"HDR*\x0c\x00": PowerBuilderVersion(12, 0, True),
        b"HDR*\x0c\x05": PowerBuilderVersion(12, 5, True),
        b"HDR*\x0c\x06": PowerBuilderVersion(12, 6, True),
    }

    @classmethod
    def detect_from_header(cls, header_bytes: bytes) -> PowerBuilderVersion | None:
        """Detect version from header bytes.

        Args:
            header_bytes: First 6-8 bytes of the PBD/PBL file

        Returns:
            Detected PowerBuilder version or None if unknown
        """
        # Check known signatures
        for sig_len in [6, 8]:  # Try different signature lengths
            if len(header_bytes) >= sig_len:
                sig = header_bytes[:sig_len]
                if sig in cls.VERSION_SIGNATURES:
                    version = cls.VERSION_SIGNATURES[sig]
                    logger.info(f"Detected {version} from header signature")
                    return version

        # Fallback: Try to parse version bytes manually
        if len(header_bytes) >= 6:
            # Check for HDR\0 or HDR*
            if header_bytes[:4] in [b"HDR\x00", b"HDR*"]:
                is_unicode = header_bytes[3:4] == b"*"
                # Version bytes are at offset 4-5
                if len(header_bytes) >= 6:
                    major = header_bytes[4]
                    minor = header_bytes[5]
                    version = PowerBuilderVersion(major, minor, is_unicode)
                    logger.info(f"Detected {version} from header bytes")
                    return version

        logger.warning("Could not detect PowerBuilder version from header")
        return None

    @classmethod
    def detect_from_file(cls, file_handle: BinaryIO) -> PowerBuilderVersion | None:
        """Detect version from an open file handle.

        Args:
            file_handle: Open binary file handle

        Returns:
            Detected PowerBuilder version or None if unknown
        """
        # Save current position
        original_pos = file_handle.tell()

        try:
            # Read header bytes
            file_handle.seek(0)
            header_bytes = file_handle.read(8)

            return cls.detect_from_header(header_bytes)

        finally:
            # Restore original position
            file_handle.seek(original_pos)

    @classmethod
    def detect_from_opcode_patterns(
        cls, pcode_bytes: bytes
    ) -> PowerBuilderVersion | None:
        """Detect version from P-code opcode patterns.

        This is a fallback method that looks for version-specific opcode patterns.

        Args:
            pcode_bytes: P-code bytes to analyze

        Returns:
            Detected PowerBuilder version or None if unknown
        """
        if not pcode_bytes or len(pcode_bytes) < 4:
            return None
            
        # Import here to avoid circular dependency
        from decompile.opcodes import OPCODE_TABLE
        
        # Scan through opcodes looking for version-specific patterns
        max_opcode = 0
        has_extended_opcodes = False  # Opcodes that indicate PB 8.0+
        has_unicode_patterns = False
        opcode_histogram = {}
        
        i = 0
        while i < len(pcode_bytes) - 1:
            opcode = pcode_bytes[i]
            
            # Track opcode usage
            opcode_histogram[opcode] = opcode_histogram.get(opcode, 0) + 1
            
            # Track the highest opcode seen
            if opcode > max_opcode:
                max_opcode = opcode
                
            # Check if this is a known opcode that only exists in PB 8.0+
            if opcode in OPCODE_TABLE:
                opcode_name = OPCODE_TABLE[opcode][0]
                # These opcodes were added in PB 8.0 for LongLong support
                if any(keyword in opcode_name for keyword in ['LONGLONG', 'BYTE']):
                    has_extended_opcodes = True
                    logger.debug(f"Found PB 8.0+ opcode: 0x{opcode:02X} ({opcode_name})")
                    
            # Check for Unicode string patterns
            # Unicode strings often have null bytes between characters
            if opcode == 0x3B:  # PUSH_CONST_STRING
                # Check if there's a pattern of alternating nulls (Unicode)
                if i + 10 < len(pcode_bytes):
                    sample = pcode_bytes[i+2:i+10]
                    null_count = sum(1 for b in sample if b == 0)
                    if null_count >= 3:  # At least 3 nulls in 8 bytes suggests Unicode
                        has_unicode_patterns = True
                        logger.debug(f"Found Unicode pattern at offset {i}")
                        
            # Move to next instruction
            # This is simplified - real P-code would need proper instruction length calculation
            i += 1
            
        # Analyze opcode patterns
        logger.info(f"Opcode analysis: max=0x{max_opcode:02X}, extended={has_extended_opcodes}, unicode={has_unicode_patterns}")
        logger.debug(f"Top opcodes: {sorted(opcode_histogram.items(), key=lambda x: x[1], reverse=True)[:10]}")
        
        # Look for specific version indicators
        # Check for opcodes that are specific to certain versions
        version_indicators = {
            # Extended type conversion opcodes (PB 8.0+)
            0xEB: 8,  # Would map to CNV_INT_TO_LONGLONG conceptually
            0xF0: 8,  # Extended opcodes region
            0xFA: 8,  # Extended arithmetic
            # Any opcode that wouldn't exist in PB 6.0
            0xA0: 7,  # Later conversion opcodes
            0xB0: 7,  # Extended comparison opcodes
        }
        
        detected_min_version = 6
        for opcode, min_version in version_indicators.items():
            if opcode in opcode_histogram and min_version > detected_min_version:
                detected_min_version = min_version
                logger.debug(f"Found opcode 0x{opcode:02X} indicating PB {min_version}.0+")
        
        # Determine version based on analysis
        if has_extended_opcodes or detected_min_version >= 8:
            # Definitely PB 8.0 or later
            if has_unicode_patterns:
                # Unicode suggests PB 10.0+
                return PowerBuilderVersion(10, 5, True)
            else:
                # Non-Unicode PB 8.0/9.0
                return PowerBuilderVersion(8, 0, False)
                
        elif detected_min_version >= 7:
            # PB 7.0
            return PowerBuilderVersion(7, 0, False)
            
        else:
            # PB 6.0 (default for simple opcodes)
            return PowerBuilderVersion(6, 0, False)
            
        # Unable to determine (shouldn't reach here)
        logger.warning(f"Could not determine version from opcode patterns (max opcode: 0x{max_opcode:02X})")
        return None

    @classmethod
    def get_default_version(cls, is_unicode: bool = False) -> PowerBuilderVersion:
        """Get default version when detection fails.

        Args:
            is_unicode: Whether the file uses Unicode encoding

        Returns:
            Default PowerBuilder version
        """
        if is_unicode:
            # Default to PB 10.5 for Unicode files
            return PowerBuilderVersion(10, 5, True)
        # Default to PB 6.0 for non-Unicode files
        return PowerBuilderVersion(6, 0, False)


# Convenience function for backward compatibility
def detect_pb_version(file_handle: BinaryIO) -> PowerBuilderVersion | None:
    """Detect PowerBuilder version from file handle.

    Args:
        file_handle: Open binary file handle

    Returns:
        Detected PowerBuilder version or None if unknown
    """
    return PBVersionDetector.detect_from_file(file_handle)
