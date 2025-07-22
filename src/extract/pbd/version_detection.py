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
                    logger.info("Detected %s from header signature", version)
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
                    logger.info("Detected %s from header bytes", version)
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
    def _analyze_opcodes(cls, pcode_bytes: bytes) -> tuple[dict, int, bool, bool]:
        """Analyze opcodes and return histogram, max opcode, has_extended, has_unicode."""
        from src.decompile.opcodes import OPCODE_TABLE

        opcode_histogram = {}
        max_opcode = 0
        has_extended_opcodes = False
        has_unicode_patterns = False

        i = 0
        while i < len(pcode_bytes) - 1:
            opcode = pcode_bytes[i]

            # Track opcode usage
            opcode_histogram[opcode] = opcode_histogram.get(opcode, 0) + 1
            max_opcode = max(max_opcode, opcode)

            # Check for extended opcodes
            if not has_extended_opcodes and opcode in OPCODE_TABLE:
                opcode_name = OPCODE_TABLE[opcode][0]
                if any(keyword in opcode_name for keyword in ["LONGLONG", "BYTE"]):
                    has_extended_opcodes = True
                    logger.debug(
                        "Found PB 8.0+ opcode: 0x%02X (%s)", opcode, opcode_name
                    )

            # Check for Unicode patterns
            if (
                not has_unicode_patterns
                and opcode == 0x3B
                and i + 10 < len(pcode_bytes)
            ):
                sample = pcode_bytes[i + 2 : i + 10]
                if sum(1 for b in sample if b == 0) >= 3:
                    has_unicode_patterns = True
                    logger.debug("Found Unicode pattern at offset %s", i)

            i += 1

        return opcode_histogram, max_opcode, has_extended_opcodes, has_unicode_patterns

    @classmethod
    def _detect_minimum_version(cls, opcode_histogram: dict) -> int:
        """Detect minimum version based on specific opcodes."""
        version_indicators = {
            0xEB: 8,  # CNV_INT_TO_LONGLONG conceptually
            0xF0: 8,  # Extended opcodes region
            0xFA: 8,  # Extended arithmetic
            0xA0: 7,  # Later conversion opcodes
            0xB0: 7,  # Extended comparison opcodes
        }

        detected_min_version = 6
        for opcode, min_version in version_indicators.items():
            if opcode in opcode_histogram and min_version > detected_min_version:
                detected_min_version = min_version
                logger.debug(
                    "Found opcode 0x%02X indicating PB %s.0+", opcode, min_version
                )

        return detected_min_version

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

        # Analyze opcodes
        opcode_histogram, max_opcode, has_extended, has_unicode = cls._analyze_opcodes(
            pcode_bytes
        )

        logger.info(
            "Opcode analysis: max = 0x%02X, extended=%s, unicode=%s",
            max_opcode,
            has_extended,
            has_unicode,
        )
        logger.debug(
            "Top opcodes: %s",
            sorted(opcode_histogram.items(), key=lambda x: x[1], reverse=True)[:10],
        )

        # Detect minimum version
        detected_min_version = cls._detect_minimum_version(opcode_histogram)

        # Determine version based on analysis
        if has_extended or detected_min_version >= 8:
            return (
                PowerBuilderVersion(10, 5, True)
                if has_unicode
                else PowerBuilderVersion(8, 0, False)
            )
        if detected_min_version >= 7:
            return PowerBuilderVersion(7, 0, False)
        return PowerBuilderVersion(6, 0, False)

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
