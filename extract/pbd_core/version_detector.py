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


class VersionDetector:
    """Detects PowerBuilder version from PBD/PBL files."""

    # Known version signatures and patterns
    VERSION_SIGNATURES = {
        # PowerBuilder 5
        b'HDR\x00\x05\x00': PowerBuilderVersion(5, 0, False),
        # PowerBuilder 6
        b'HDR\x00\x06\x00': PowerBuilderVersion(6, 0, False),
        b'HDR\x00\x06\x05': PowerBuilderVersion(6, 5, False),
        # PowerBuilder 7
        b'HDR\x00\x07\x00': PowerBuilderVersion(7, 0, False),
        # PowerBuilder 8
        b'HDR\x00\x08\x00': PowerBuilderVersion(8, 0, False),
        # PowerBuilder 9
        b'HDR\x00\x09\x00': PowerBuilderVersion(9, 0, False),
        # PowerBuilder 10 (Unicode introduced)
        b'HDR*\x0A\x00': PowerBuilderVersion(10, 0, True),
        b'HDR*\x0A\x05': PowerBuilderVersion(10, 5, True),
        # PowerBuilder 11
        b'HDR*\x0B\x00': PowerBuilderVersion(11, 0, True),
        b'HDR*\x0B\x05': PowerBuilderVersion(11, 5, True),
        # PowerBuilder 12
        b'HDR*\x0C\x00': PowerBuilderVersion(12, 0, True),
        b'HDR*\x0C\x05': PowerBuilderVersion(12, 5, True),
        b'HDR*\x0C\x06': PowerBuilderVersion(12, 6, True),
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
            if header_bytes[:4] in [b'HDR\x00', b'HDR*']:
                is_unicode = header_bytes[3:4] == b'*'
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
    def detect_from_opcode_patterns(cls, pcode_bytes: bytes) -> PowerBuilderVersion | None:
        """Detect version from P-code opcode patterns.
        
        This is a fallback method that looks for version-specific opcode patterns.
        
        Args:
            pcode_bytes: P-code bytes to analyze
            
        Returns:
            Detected PowerBuilder version or None if unknown
        """
        # TODO: Implement opcode pattern detection
        # This would analyze opcode usage patterns to determine the version
        # For example:
        # - PB6 uses opcodes 0x00-0x100
        # - PB10+ uses extended opcodes up to 0x246
        # - Unicode versions have different string handling opcodes

        logger.debug("Opcode pattern detection not yet implemented")
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
