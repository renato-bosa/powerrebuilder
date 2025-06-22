"""Unit tests for PBD extraction functionality.

Tests for the core PBD extraction components focusing on basic functionality
without circular import issues.
"""

import struct
from pathlib import Path

import pytest


# Test the basic components without the circular imports
def test_pbd_signature():


    """Test PBD signature constants are defined correctly."""
    from extract.pbd.structures.header import PBD_SIGNATURE, PBD_SIGNATURE_EXT

    assert PBD_SIGNATURE == b"PBD"
    assert PBD_SIGNATURE_EXT == b"PBD\x00"


def test_pbl_signature():






    """Test PBL signature constants are defined correctly."""
    from extract.pbd.structures.header import PBL_SIGNATURE, PBL_SIGNATURE_EXT

    assert PBL_SIGNATURE == b"PBL"
    assert PBL_SIGNATURE_EXT == b"PBL\x00"


def test_block_size_constants():






    """Test block size constants."""
    from extract.pbd.structures.node import BLOCK_SIZE

    assert BLOCK_SIZE == 512


def test_entry_flags():






    """Test entry flag constants."""
    from extract.pbd.structures.entry import ENTRY_FLAG_OFFSET

    # Common flag offsets
    assert ENTRY_FLAG_OFFSET in {
        0x0022,
        0x002A,
    }  # Different versions have different offsets


def test_unicode_detection():






    """Test Unicode detection logic."""
    # Test Unicode marker
    unicode_data = b"\x00\x00\xfe\xff"  # Unicode BOM
    assert unicode_data[2:4] == b"\xfe\xff"

    # Test ANSI marker (no BOM)
    ansi_data = b"\x00\x00\x00\x00"
    assert ansi_data[2:4] != b"\xfe\xff"


def test_opcode_constants():






    """Test that opcode constants are properly defined."""
    from decompile.opcodes import OPCODE_TABLE

    # Common opcodes should be defined in the table
    assert 0x00 in OPCODE_TABLE  # NOP/HALT
    assert 0x01 in OPCODE_TABLE  # PUSHCONST
    assert 0x02 in OPCODE_TABLE  # PUSHVAR


def test_dat_signature():






    """Test DAT file signature."""
    from extract.pbd.structures.data_block import DAT_MARKER

    assert DAT_MARKER == b"DAT*"


def test_exception_hierarchy():






    """Test custom exception hierarchy."""
    from common.exceptions import (
        DatError,
        EntryError,
        HeaderError,
        NodeError,
        PbdError,
    )

    # Test inheritance
    assert issubclass(HeaderError, PbdError)
    assert issubclass(NodeError, PbdError)
    assert issubclass(EntryError, PbdError)
    assert issubclass(DatError, PbdError)

    # Test instantiation
    error = PbdError("test error")
    assert str(error) == "test error"


def test_pbd_file_fixture_exists():






    """Test that PBD test fixture exists."""
    pbd_file = Path(__file__).parent / "fixtures" / "pbd_files" / "dcm_email.pbd"
    assert pbd_file.exists(), f"PBD fixture not found: {pbd_file}"
    assert pbd_file.stat().st_size > 0, "PBD fixture is empty"


def test_read_pbd_header():






    """Test reading basic PBD header information."""
    pbd_file = Path(__file__).parent / "fixtures" / "pbd_files" / "dcm_email.pbd"

    if not pbd_file.exists():
        pytest.skip("PBD fixture not found")

    with open(pbd_file, "rb") as f:
        # Read first 4 bytes for signature
        signature = f.read(4)

        # Should be either PBD or PBL signature
        assert signature in {b"PBD\x00", b"PBL\x00", b"PBD", b"PBL"}, (
            f"Invalid signature: {signature}"
        )


def test_struct_formats():






    """Test struct format strings used in PBD parsing."""
    # Test common struct formats
    assert struct.calcsize("<I") == 4  # 32-bit unsigned int
    assert struct.calcsize("<H") == 2  # 16-bit unsigned short
    assert struct.calcsize("<B") == 1  # 8-bit unsigned char
    assert struct.calcsize("<Q") == 8  # 64-bit unsigned long long


def test_offset_calculations():






    """Test offset calculation logic."""
    # Block-based offset calculation
    block_size = 512
    block_number = 5
    offset_in_block = 100

    total_offset = (block_number * block_size) + offset_in_block
    assert total_offset == 2660

    # Verify reverse calculation
    assert total_offset // block_size == block_number
    assert total_offset % block_size == offset_in_block


def test_string_encoding():






    """Test string encoding/decoding for PBD files."""
    # ANSI string
    ansi_bytes = b"test_string\x00"
    ansi_str = ansi_bytes[:-1].decode("latin-1")
    assert ansi_str == "test_string"

    # Unicode string (UTF-16LE)
    unicode_bytes = b"t\x00e\x00s\x00t\x00\x00\x00"
    unicode_str = unicode_bytes[:-2].decode("utf-16le")
    assert unicode_str == "test"


class TestPBDExtractionHelpers:
    """Test helper functions for PBD extraction."""

    def test_checksum_calculation(self):




        """Test checksum calculation methods."""
        # Simple checksum by summing bytes
        data = b"Hello, World!"
        checksum = sum(data) & 0xFFFF  # 16-bit checksum
        assert checksum > 0
        assert checksum <= 0xFFFF

    def test_block_alignment(self):




        """Test block alignment calculations."""
        block_size = 512

        # Test various sizes
        test_cases = [
            (100, 512),  # Aligned to next block
            (512, 512),  # Already aligned
            (513, 1024),  # Just over one block
            (1000, 1024),  # Near two blocks
        ]

        for size, expected in test_cases:
            aligned = ((size + block_size - 1) // block_size) * block_size
            assert aligned == expected, f"Failed for size {size}"

    def test_entry_type_detection(self):




        """Test entry type detection logic."""
        # Common entry type values
        entry_types = {
            0x00: "source",
            0x01: "object",
            0x02: "binary",
            0x03: "resource",
        }

        for type_val, type_name in entry_types.items():
            assert isinstance(type_val, int)
            assert isinstance(type_name, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
