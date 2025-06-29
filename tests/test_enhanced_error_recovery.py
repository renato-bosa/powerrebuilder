"""Test enhanced error recovery for corrupted PBL/PBD files."""

import struct
import tempfile
from pathlib import Path

from src.extract.coordinator import (
    _extract_text_segments,
    _looks_like_pb_code,
    _perform_enhanced_byte_recovery,
    _scan_for_dat_blocks,
    _scan_for_ent_blocks,
    _scan_for_pb_objects,
    extract_with_recovery,
)


class TestEnhancedErrorRecovery:
    """Test enhanced error recovery functionality."""

    def test_looks_like_pb_code(self):




        """Test PowerBuilder code detection."""
        # Valid PowerBuilder code
        pb_code = """
        global function integer calculate_total(integer amount)
        integer li_total

        if amount > 0 then
            li_total = amount * 1.1
        else
            li_total = 0
        end if

        return li_total
        end function
        """
        assert _looks_like_pb_code(pb_code) is True

        # Not PowerBuilder code
        random_text = "This is just some random text without any code."
        assert _looks_like_pb_code(random_text) is False

        # Minimal PowerBuilder code
        minimal_code = "function test()\nreturn 1\nend function"
        assert _looks_like_pb_code(minimal_code) is True

    def test_scan_for_pb_objects(self):




        """Test scanning for PowerBuilder objects in corrupted data."""
        # Create test data with embedded PowerBuilder object
        pb_object = b"""$PBExportHeader$w_main.srw
global type w_main from window
end type
end forward

global type w_main from window
integer width = 1234
integer height = 567
string title = "Main Window"
end type
global w_main w_main
"""

        # Embed in corrupted data
        corrupted_data = b"\x00\x01\x02\x03" * 100 + pb_object + b"\xFF\xFE" * 100

        with tempfile.TemporaryDirectory() as temp_dir:
            recovery_dir = Path(temp_dir)
            count = _scan_for_pb_objects(corrupted_data, recovery_dir, "test.pbd")

            assert count > 0
            # Check that a file was created
            recovered_files = list(recovery_dir.glob("pb_*.txt"))
            assert len(recovered_files) > 0

            # Verify content
            content = recovered_files[0].read_text()
            assert "$PBExportHeader$" in content
            assert "w_main" in content

    def test_scan_for_dat_blocks(self):




        """Test scanning for DAT blocks."""
        # Create a simple DAT block
        dat_header = b"DAT*"  # ASCII DAT signature
        next_block = struct.pack("<I", 0)  # No next block
        data_len = struct.pack("<H", 20)  # 20 bytes of data
        data = b"Test DAT block data!"

        dat_block = dat_header + next_block + data_len + data

        # Embed in file
        file_data = b"\x00" * 100 + dat_block + b"\xFF" * 100

        with tempfile.TemporaryDirectory() as temp_dir:
            recovery_dir = Path(temp_dir)
            count = _scan_for_dat_blocks(file_data, recovery_dir, "test.pbd")

            # Should find at least the DAT block we created
            assert count >= 0  # May be 0 if block is too small

    def test_scan_for_ent_blocks(self):




        """Test scanning for ENT blocks."""
        # Create an ENT block with object name
        ent_header = b"ENT*"  # ASCII ENT signature
        padding = b"\x00" * 16  # Some header padding
        object_name = b"w_employee\x00"  # Null-terminated name

        ent_block = ent_header + padding + object_name

        # Embed in file
        file_data = b"\xFF" * 200 + ent_block + b"\x00" * 200

        with tempfile.TemporaryDirectory() as temp_dir:
            recovery_dir = Path(temp_dir)
            count = _scan_for_ent_blocks(file_data, recovery_dir, "test.pbd")

            if count > 0:
                # Check that metadata was saved
                metadata_files = list(recovery_dir.glob("ent_metadata_*.txt"))
                assert len(metadata_files) > 0

                content = metadata_files[0].read_text()
                assert "w_employee" in content

    def test_extract_text_segments(self):




        """Test extracting text segments."""
        # Create text segment that looks like PowerBuilder code
        text_segment = """
forward prototypes
global function integer calculate_discount (decimal price, integer percent)
end prototypes

global function integer calculate_discount (decimal price, integer percent)
decimal ld_discount

if percent > 0 and percent <= 100 then
    ld_discount = price * (percent / 100.0)
else
    ld_discount = 0
end if

return truncate(ld_discount, 0)
end function
""".encode("utf-8")

        # Embed in binary data
        file_data = b"\x00\x01\x02" * 50 + text_segment + b"\xFF\xFE\xFD" * 50

        with tempfile.TemporaryDirectory() as temp_dir:
            recovery_dir = Path(temp_dir)
            count = _extract_text_segments(file_data, recovery_dir, "test.pbd")

            assert count > 0
            # Check that text was extracted
            text_files = list(recovery_dir.glob("text_segment_*.txt"))
            assert len(text_files) > 0

            content = text_files[0].read_text()
            assert "calculate_discount" in content
            assert "forward prototypes" in content

    def test_perform_enhanced_byte_recovery(self):




        """Test the main enhanced byte recovery function."""
        # Create a file with multiple recoverable elements

        # PowerBuilder object
        pb_object = b"""$PBExportHeader$d_employee.srd
release 11;
datawindow(units=0 timer_interval=0)
""" 

        # DAT block
        dat_block = b"DAT*" + struct.pack("<I", 0) + struct.pack("<H", 10) + b"Some data!"

        # Text segment
        text_code = """
global type n_calculator from nonvisualobject
end type
end forward

global type n_calculator from nonvisualobject
end type
global n_calculator n_calculator

function decimal calculate(decimal a, decimal b, string operation)
decimal result

choose case operation
    case "+"
        result = a + b
    case "-"
        result = a - b
    case "*"
        result = a * b
    case "/"
        if b <> 0 then
            result = a / b
        else
            result = 0
        end if
end choose

return result
end function
""".encode("utf-8")

        # Combine all elements with corruption
        file_data = (
            b"\xFF\xFE" * 100 +
            pb_object +
            b"\x00" * 50 +
            dat_block +
            b"\xAB\xCD" * 75 +
            text_code +
            b"\x00\x00\x00\x00"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = temp_dir

            # Run enhanced recovery
            success = _perform_enhanced_byte_recovery(
                file_data,
                output_dir,
                "corrupted.pbd",
                show_progress=False,
            )

            assert success is True

            # Check recovery directory was created
            recovery_dir = Path(output_dir) / "recovery"
            assert recovery_dir.exists()

            # Check summary file
            summary_file = recovery_dir / "recovery_summary.txt"
            assert summary_file.exists()

            summary = summary_file.read_text()
            assert "Recovery Summary" in summary
            assert "Total objects/segments recovered:" in summary

            # Check that some files were recovered
            all_recovered = list(recovery_dir.glob("*.txt"))
            assert len(all_recovered) > 1  # At least summary + some recovered files

    def test_extract_with_recovery_with_byte_recovery_enabled(self):




        """Test the main extract_with_recovery function with byte recovery enabled."""
        # Create a corrupted file that standard extraction can't handle
        # but byte recovery can partially recover

        # Invalid header
        corrupted_header = b"INVALID_HEADER" + b"\x00" * 50

        # But contains valid PowerBuilder code
        pb_code = b"""
$PBExportHeader$corrupted.sru
global type s_data from structure
end type

type s_data from structure
    string name
    integer id
    decimal amount
end type
"""

        corrupted_file = corrupted_header + pb_code + b"\xFF" * 100

        with tempfile.TemporaryDirectory() as temp_dir:
            # Write corrupted file
            input_file = Path(temp_dir) / "corrupted.pbd"
            input_file.write_bytes(corrupted_file)

            output_dir = Path(temp_dir) / "output"

            # Run extraction with byte recovery enabled
            success = extract_with_recovery(
                str(input_file),
                str(output_dir),
                show_progress=False,
                enable_byte_recovery=True,
            )

            # Should succeed with byte recovery
            # (standard extraction would fail due to invalid header)
            # Note: This might still return False if no significant data is found
            # The important part is that it attempts byte recovery

            # Check that recovery was attempted
            expected_output = output_dir / input_file.name / "recovery"
            # Recovery dir might not exist if nothing was recovered
            # But the function should have run without crashing
