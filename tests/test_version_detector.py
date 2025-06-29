#!/usr/bin/env python3
"""Test PowerBuilder version detection including opcode patterns."""


from src.extract.utils.version import PBVersionDetector, PowerBuilderVersion


class TestVersionDetection:
    """Test version detection from headers."""

    def test_detect_pb6_header(self):




        """Test detection of PowerBuilder 6.0 from header."""
        header = b"HDR\x00\x06\x00"
        version = PBVersionDetector.detect_from_header(header)

        assert version is not None
        assert version.major == 6
        assert version.minor == 0
        assert not version.is_unicode

    def test_detect_pb10_unicode_header(self):




        """Test detection of PowerBuilder 10.0 Unicode from header."""
        header = b"HDR*\x0a\x00"
        version = PBVersionDetector.detect_from_header(header)

        assert version is not None
        assert version.major == 10
        assert version.minor == 0
        assert version.is_unicode

    def test_detect_pb12_6_header(self):




        """Test detection of PowerBuilder 12.6 from header."""
        header = b"HDR*\x0c\x06"
        version = PBVersionDetector.detect_from_header(header)

        assert version is not None
        assert version.major == 12
        assert version.minor == 6
        assert version.is_unicode

    def test_detect_unknown_header(self):




        """Test handling of unknown header."""
        header = b"XXX\x00\x00\x00"
        version = PBVersionDetector.detect_from_header(header)

        assert version is None

    def test_detect_manual_parse(self):




        """Test manual header parsing fallback."""
        # Header with unrecognized exact signature but valid format
        header = b"HDR\x00\x07\x05"  # PB 7.5 (not in exact table)
        version = PBVersionDetector.detect_from_header(header)

        assert version is not None
        assert version.major == 7
        assert version.minor == 5
        assert not version.is_unicode


class TestOpcodePatternDetection:
    """Test version detection from opcode patterns."""

    def test_detect_pb6_opcodes(self):




        """Test detection of PB 6.0 from basic opcodes."""
        # Simulate P-code with only basic opcodes (< 0xFF)
        pcode = bytes([
            0x00,  # RETURN
            0x1E, 0x01,  # PUSH_LOCAL_VAR 1
            0x32, 0x0A, 0x00,  # PUSH_CONST_INT 10
            0xA6,  # EQ_INT
            0x03, 0x05,  # JUMPFALSE +5
            0x3B, 0x00, 0x00,  # PUSH_CONST_STRING
            0x00,  # RETURN
        ])

        version = PBVersionDetector.detect_from_opcode_patterns(pcode)

        assert version is not None
        assert version.major == 6
        assert version.minor == 0
        assert not version.is_unicode

    def test_detect_pb8_opcodes(self):




        """Test detection of PB 8.0 from extended opcodes."""
        # Simulate P-code with opcodes that indicate PB 8.0+
        pcode = bytes([
            0x00,  # RETURN
            0xEB,  # Extended opcode region (indicates PB 8.0+)
            0x00,
            0xF0,  # Extended opcode region  
            0x00,
            0xFA,  # Extended arithmetic region
            0x00,
        ])

        version = PBVersionDetector.detect_from_opcode_patterns(pcode)

        assert version is not None
        assert version.major == 8  # Should detect as 8.0 due to extended opcodes
        assert version.minor == 0
        assert not version.is_unicode

    def test_detect_pb6_with_unicode_data(self):




        """Test detection of PB 6.0 even with Unicode-like data patterns."""
        # Simulate P-code with Unicode-like patterns but only basic opcodes
        # This tests that we don't misidentify based on data alone
        pcode = bytes([
            0x00,  # RETURN
            0x3B, 0x00, 0x00,  # PUSH_CONST_STRING
            0x48, 0x00, 0x65, 0x00, 0x6C, 0x00, 0x6C, 0x00,  # "Hell" in UTF-16
            0x80,  # Basic opcode (ASSIGN_INT)
            0x00,
        ])

        version = PBVersionDetector.detect_from_opcode_patterns(pcode)

        assert version is not None
        assert version.major == 6  # Only basic opcodes = PB 6.0
        assert version.minor == 0
        assert not version.is_unicode  # Despite Unicode-like data

    def test_detect_pb10_extended_with_unicode(self):




        """Test detection of PB 10+ from extended opcodes with Unicode."""
        # Simulate P-code with extended opcodes and Unicode patterns
        pcode = bytes([
            0x00,  # RETURN
            0xEB,  # Extended opcode (PB 8.0+)
            0x00,
            0x3B, 0x00, 0x00,  # PUSH_CONST_STRING
            0x00, 0x41, 0x00, 0x42, 0x00, 0x43, 0x00, 0x00,  # Unicode pattern
            0xF0,  # Another extended opcode
            0x00,
        ])

        version = PBVersionDetector.detect_from_opcode_patterns(pcode)

        assert version is not None
        assert version.major == 10  # Extended + Unicode = PB 10+
        assert version.minor == 5
        assert version.is_unicode

    def test_detect_pb7_opcodes(self):




        """Test detection of PB 7.0 from intermediate opcodes."""
        # P-code with opcodes that indicate PB 7.0
        pcode = bytes([
            0x00,  # RETURN
            0xA0,  # CNV_DOUBLE_TO_DEC (indicates PB 7.0+)
            0x00,
            0xB0,  # EQ_TIME (extended comparison)
            0x00,
            0x80,  # ASSIGN_INT
            0x01,
            0x00,
        ])

        version = PBVersionDetector.detect_from_opcode_patterns(pcode)

        assert version is not None
        assert version.major == 7  # PB 7.0
        assert version.minor == 0
        assert not version.is_unicode

    def test_detect_mixed_version_indicators(self):




        """Test detection with mixed version indicators."""
        # P-code with various opcodes from different versions
        pcode = bytes([
            0x32,  # PUSH_CONST_INT (basic)
            0x10, 0x00,
            0xA6,  # EQ_INT (basic comparison)
            0x00,
            0xF0,  # Extended region (PB 8.0+ indicator)
            0x00,
            0xEB,  # Another PB 8.0+ indicator
            0x00,
        ])

        version = PBVersionDetector.detect_from_opcode_patterns(pcode)

        assert version is not None
        assert version.major == 8  # Should detect highest version indicated

    def test_empty_pcode(self):




        """Test handling of empty P-code."""
        version = PBVersionDetector.detect_from_opcode_patterns(b"")
        assert version is None

    def test_short_pcode(self):




        """Test handling of very short P-code."""
        version = PBVersionDetector.detect_from_opcode_patterns(b"\x00\x01")
        assert version is None


class TestDefaultVersion:
    """Test default version fallback."""

    def test_default_non_unicode(self):




        """Test default version for non-Unicode files."""
        version = PBVersionDetector.get_default_version(is_unicode=False)

        assert version.major == 6
        assert version.minor == 0
        assert not version.is_unicode

    def test_default_unicode(self):




        """Test default version for Unicode files."""
        version = PBVersionDetector.get_default_version(is_unicode=True)

        assert version.major == 10
        assert version.minor == 5
        assert version.is_unicode


class TestVersionString:
    """Test version string formatting."""

    def test_version_str(self):




        """Test version string representation."""
        version = PowerBuilderVersion(10, 5, True)
        assert str(version) == "pb10_5"

    def test_version_repr(self):




        """Test version detailed representation."""
        version = PowerBuilderVersion(6, 0, False)
        assert repr(version) == "PowerBuilder 6.0"

        version_unicode = PowerBuilderVersion(12, 6, True)
        assert repr(version_unicode) == "PowerBuilder 12.6 (Unicode)"
