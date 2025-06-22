"""Tests for common.object_type_detector module."""

import struct

import pytest

from common.object_type_detector import (
    DataWindowSubtype,
    MagicNumbers,
    ObjectType,
    ObjectTypeDetector,
)


class TestObjectType:
    """Test ObjectType class constants."""

    def test_type_constants(self):




        """Test that object type constants are defined correctly."""
        assert ObjectType.FUNCTION == 0
        assert ObjectType.STRUCTURE == 1
        assert ObjectType.WINDOW == 13
        assert ObjectType.USER_OBJECT == 8
        assert ObjectType.DATAWINDOW == 18
        assert ObjectType.MENU == 55
        assert ObjectType.APPLICATION == 9
        assert ObjectType.QUERY == 77
        assert ObjectType.PIPELINE == 33
        assert ObjectType.PROJECT == 36
        assert ObjectType.PROXY == 44

    def test_pcode_types(self):




        """Test that P-code types are correctly defined."""
        expected_pcode_types = {
            ObjectType.FUNCTION,
            ObjectType.WINDOW,
            ObjectType.USER_OBJECT,
            ObjectType.MENU,
            ObjectType.APPLICATION,
        }
        assert ObjectType.PCODE_TYPES == expected_pcode_types

    def test_data_only_types(self):




        """Test that data-only types are correctly defined."""
        expected_data_types = {
            ObjectType.STRUCTURE,
            ObjectType.DATAWINDOW,
            ObjectType.QUERY,
            ObjectType.PIPELINE,
            ObjectType.PROJECT,
            ObjectType.PROXY,
        }
        assert ObjectType.DATA_ONLY_TYPES == expected_data_types


class TestDataWindowSubtype:
    """Test DataWindowSubtype enum."""

    def test_subtype_values(self):




        """Test DataWindow subtype values."""
        assert DataWindowSubtype.SQL.value == "_sql"
        assert DataWindowSubtype.DATASTORE.value == "_ds"
        assert DataWindowSubtype.EXTERNAL.value == "_ex"
        assert DataWindowSubtype.DROPDOWN.value == "_dddw"
        assert DataWindowSubtype.REPORT.value == "_rpt"
        assert DataWindowSubtype.DATAWINDOW.value == "_dw"
        assert DataWindowSubtype.UNKNOWN.value == "_unknown"


class TestMagicNumbers:
    """Test MagicNumbers class constants."""

    def test_magic_number_values(self):




        """Test magic number values."""
        assert MagicNumbers.DATAWINDOW_HEADER == 0x444F4D76
        assert MagicNumbers.OBJECT_DESCRIPTOR == 0x4F424A44
        assert MagicNumbers.PBD_HEADER == 0x00524448
        assert MagicNumbers.BINARY_MARKER == 0x00000000
        assert MagicNumbers.SQL_MARKER == 0x53514C20
        assert MagicNumbers.RELEASE_MARKER == 0x72656C65

    def test_corrupt_sizes(self):




        """Test corrupt size values."""
        expected_corrupt = {0x444F4D76, 0x4F424A44, 0xFFFFFFFF}
        assert MagicNumbers.CORRUPT_SIZES == expected_corrupt


class TestObjectTypeDetector:
    """Test ObjectTypeDetector class."""

    def test_detect_type_from_extension(self):




        """Test type detection from file extensions."""
        # Function types
        assert ObjectTypeDetector.detect_type("test.fun") == ObjectType.FUNCTION

        # Structure types
        assert ObjectTypeDetector.detect_type("test.str") == ObjectType.STRUCTURE

        # Window types
        assert ObjectTypeDetector.detect_type("test.win") == ObjectType.WINDOW

        # User object types
        assert ObjectTypeDetector.detect_type("test.udo") == ObjectType.USER_OBJECT
        assert ObjectTypeDetector.detect_type("test.sru") == ObjectType.USER_OBJECT

        # DataWindow types
        assert ObjectTypeDetector.detect_type("test.dwo") == ObjectType.DATAWINDOW
        assert ObjectTypeDetector.detect_type("test.srd") == ObjectType.DATAWINDOW

        # Menu types
        assert ObjectTypeDetector.detect_type("test.men") == ObjectType.MENU
        assert ObjectTypeDetector.detect_type("test.srm") == ObjectType.MENU
        assert ObjectTypeDetector.detect_type("test.mef") == ObjectType.MENU

        # Application types
        assert ObjectTypeDetector.detect_type("test.apl") == ObjectType.APPLICATION
        assert ObjectTypeDetector.detect_type("test.sra") == ObjectType.APPLICATION
        assert ObjectTypeDetector.detect_type("test.apf") == ObjectType.APPLICATION

        # Other types
        assert ObjectTypeDetector.detect_type("test.srq") == ObjectType.QUERY
        assert ObjectTypeDetector.detect_type("test.pip") == ObjectType.PIPELINE
        assert ObjectTypeDetector.detect_type("test.srp") == ObjectType.PIPELINE
        assert ObjectTypeDetector.detect_type("test.srj") == ObjectType.PROJECT
        assert ObjectTypeDetector.detect_type("test.prx") == ObjectType.PROXY

    def test_detect_type_case_insensitive(self):




        """Test that extension detection is case-insensitive."""
        assert ObjectTypeDetector.detect_type("TEST.FUN") == ObjectType.FUNCTION
        assert ObjectTypeDetector.detect_type("Test.Win") == ObjectType.WINDOW
        assert ObjectTypeDetector.detect_type("test.DWO") == ObjectType.DATAWINDOW

    def test_detect_type_from_name_patterns(self):




        """Test type detection from naming conventions."""
        # Window prefix
        assert ObjectTypeDetector.detect_type("w_customer") == ObjectType.WINDOW

        # User object prefix
        assert ObjectTypeDetector.detect_type("u_button") == ObjectType.USER_OBJECT
        assert ObjectTypeDetector.detect_type("n_service") == ObjectType.USER_OBJECT

        # DataWindow prefix
        assert ObjectTypeDetector.detect_type("d_report") == ObjectType.DATAWINDOW

        # Menu prefix
        assert ObjectTypeDetector.detect_type("m_main") == ObjectType.MENU

        # Function prefix
        assert ObjectTypeDetector.detect_type("f_calculate") == ObjectType.FUNCTION
        assert ObjectTypeDetector.detect_type("of_validate") == ObjectType.FUNCTION

    def test_detect_type_from_embedded_patterns(self):




        """Test type detection from embedded patterns in names."""
        assert ObjectTypeDetector.detect_type("customer_w_detail") == ObjectType.WINDOW
        assert ObjectTypeDetector.detect_type("base_u_control") == ObjectType.USER_OBJECT
        assert ObjectTypeDetector.detect_type("report_d_sales") == ObjectType.DATAWINDOW
        assert ObjectTypeDetector.detect_type("popup_m_context") == ObjectType.MENU
        assert ObjectTypeDetector.detect_type("util_f_helper") == ObjectType.FUNCTION

    def test_detect_type_from_type_code(self):




        """Test type detection from PowerBuilder internal type codes."""
        # Type codes are offset by 0x4077
        base = 0x4077

        assert ObjectTypeDetector.detect_type("any", base + 0) == ObjectType.FUNCTION
        assert ObjectTypeDetector.detect_type("any", base + 1) == ObjectType.STRUCTURE
        assert ObjectTypeDetector.detect_type("any", base + 8) == ObjectType.USER_OBJECT
        assert ObjectTypeDetector.detect_type("any", base + 9) == ObjectType.APPLICATION
        assert ObjectTypeDetector.detect_type("any", base + 13) == ObjectType.WINDOW
        assert ObjectTypeDetector.detect_type("any", base + 18) == ObjectType.DATAWINDOW
        assert ObjectTypeDetector.detect_type("any", base + 55) == ObjectType.MENU

    def test_detect_type_unknown(self):




        """Test that unknown types return None."""
        assert ObjectTypeDetector.detect_type("unknown.xyz") is None
        assert ObjectTypeDetector.detect_type("test") is None
        assert ObjectTypeDetector.detect_type("any", 0x5000) is None

    def test_contains_pcode(self):




        """Test P-code detection."""
        # P-code types
        assert ObjectTypeDetector.contains_pcode("test.fun") is True
        assert ObjectTypeDetector.contains_pcode("test.win") is True
        assert ObjectTypeDetector.contains_pcode("test.udo") is True
        assert ObjectTypeDetector.contains_pcode("test.men") is True
        assert ObjectTypeDetector.contains_pcode("test.apl") is True

        # Data-only types
        assert ObjectTypeDetector.contains_pcode("test.str") is False
        assert ObjectTypeDetector.contains_pcode("test.dwo") is False
        assert ObjectTypeDetector.contains_pcode("test.srq") is False
        assert ObjectTypeDetector.contains_pcode("test.pip") is False
        assert ObjectTypeDetector.contains_pcode("test.srj") is False
        assert ObjectTypeDetector.contains_pcode("test.prx") is False

        # Unknown types assume P-code for safety
        assert ObjectTypeDetector.contains_pcode("unknown.xyz") is True

    def test_is_datawindow(self):




        """Test DataWindow detection."""
        assert ObjectTypeDetector.is_datawindow("test.dwo") is True
        assert ObjectTypeDetector.is_datawindow("test.srd") is True
        assert ObjectTypeDetector.is_datawindow("d_report") is True
        assert ObjectTypeDetector.is_datawindow("test.win") is False
        assert ObjectTypeDetector.is_datawindow("test.str") is False

    def test_is_structure(self):




        """Test Structure detection."""
        assert ObjectTypeDetector.is_structure("test.str") is True
        assert ObjectTypeDetector.is_structure("test.dwo") is False
        assert ObjectTypeDetector.is_structure("test.win") is False

    def test_get_object_info(self):




        """Test getting object info."""
        # Function
        name, has_pcode = ObjectTypeDetector.get_object_info("test.fun")
        assert name == "Function"
        assert has_pcode is True

        # Structure
        name, has_pcode = ObjectTypeDetector.get_object_info("test.str")
        assert name == "Structure"
        assert has_pcode is False

        # DataWindow
        name, has_pcode = ObjectTypeDetector.get_object_info("test.dwo")
        assert name == "DataWindow"
        assert has_pcode is False

        # Unknown
        name, has_pcode = ObjectTypeDetector.get_object_info("unknown.xyz")
        assert name == "Unknown"
        assert has_pcode is True  # Assumes P-code for safety

    def test_should_decompile(self):




        """Test decompilation decision."""
        # Should decompile
        assert ObjectTypeDetector.should_decompile("test.fun") is True
        assert ObjectTypeDetector.should_decompile("test.win") is True
        assert ObjectTypeDetector.should_decompile("test.udo") is True
        assert ObjectTypeDetector.should_decompile("test.men") is True
        assert ObjectTypeDetector.should_decompile("test.mef") is True
        assert ObjectTypeDetector.should_decompile("test.apl") is True
        assert ObjectTypeDetector.should_decompile("test.apf") is True

        # Should not decompile
        assert ObjectTypeDetector.should_decompile("test.dwo") is False
        assert ObjectTypeDetector.should_decompile("test.str") is False
        assert ObjectTypeDetector.should_decompile("test.srd") is False
        assert ObjectTypeDetector.should_decompile("test.srm") is False
        assert ObjectTypeDetector.should_decompile("test.sra") is False

    def test_detect_datawindow_subtype(self):




        """Test DataWindow subtype detection."""
        assert ObjectTypeDetector.detect_datawindow_subtype("d_customer_sql.dwo") == DataWindowSubtype.SQL
        assert ObjectTypeDetector.detect_datawindow_subtype("d_data_ds.dwo") == DataWindowSubtype.DATASTORE
        assert ObjectTypeDetector.detect_datawindow_subtype("d_import_ex.dwo") == DataWindowSubtype.EXTERNAL
        assert ObjectTypeDetector.detect_datawindow_subtype("d_state_dddw.dwo") == DataWindowSubtype.DROPDOWN
        assert ObjectTypeDetector.detect_datawindow_subtype("d_sales_rpt.dwo") == DataWindowSubtype.REPORT
        assert ObjectTypeDetector.detect_datawindow_subtype("d_customer_dw.dwo") == DataWindowSubtype.DATAWINDOW

        # Default to DATAWINDOW for .dwo files without specific suffix
        assert ObjectTypeDetector.detect_datawindow_subtype("d_customer.dwo") == DataWindowSubtype.DATAWINDOW

        # Unknown for non-DataWindow files
        assert ObjectTypeDetector.detect_datawindow_subtype("w_window.win") == DataWindowSubtype.UNKNOWN

    def test_is_binary_content(self):




        """Test binary content detection."""
        # Binary data with nulls
        binary_data = b"\x00\x01\x02\x00\x00\x00\x03\x04\x00" * 100
        assert ObjectTypeDetector.is_binary_content(binary_data) is True

        # Text data
        text_data = b"This is plain text with normal characters\n"
        assert ObjectTypeDetector.is_binary_content(text_data) is False

        # Mixed data with some nulls (below threshold)
        mixed_data = b"Text with \x00 some \x00 nulls but not too many"
        assert ObjectTypeDetector.is_binary_content(mixed_data) is False

        # High non-printable characters
        non_printable = bytes(range(0, 32)) * 50
        assert ObjectTypeDetector.is_binary_content(non_printable) is True

        # Empty data
        assert ObjectTypeDetector.is_binary_content(b"") is False

    def test_detect_magic_number(self):




        """Test magic number detection."""
        # DataWindow header
        data = struct.pack("<I", MagicNumbers.DATAWINDOW_HEADER) + b"extra"
        assert ObjectTypeDetector.detect_magic_number(data) == MagicNumbers.DATAWINDOW_HEADER

        # Object descriptor
        data = struct.pack("<I", MagicNumbers.OBJECT_DESCRIPTOR) + b"extra"
        assert ObjectTypeDetector.detect_magic_number(data) == MagicNumbers.OBJECT_DESCRIPTOR

        # PBD header
        data = struct.pack("<I", MagicNumbers.PBD_HEADER) + b"extra"
        assert ObjectTypeDetector.detect_magic_number(data) == MagicNumbers.PBD_HEADER

        # Unknown magic
        data = struct.pack("<I", 0x12345678) + b"extra"
        assert ObjectTypeDetector.detect_magic_number(data) is None

        # Too short
        assert ObjectTypeDetector.detect_magic_number(b"abc") is None

    def test_is_corrupted_size(self):




        """Test corrupted size detection."""
        assert ObjectTypeDetector.is_corrupted_size(0x444F4D76) is True
        assert ObjectTypeDetector.is_corrupted_size(0x4F424A44) is True
        assert ObjectTypeDetector.is_corrupted_size(0xFFFFFFFF) is True
        assert ObjectTypeDetector.is_corrupted_size(1024) is False
        assert ObjectTypeDetector.is_corrupted_size(0) is False

    def test_analyze_file_content_empty(self):




        """Test analyzing empty file content."""
        analysis = ObjectTypeDetector.analyze_file_content(b"", "test.dwo")

        assert analysis["filename"] == "test.dwo"
        assert analysis["size"] == 0
        assert analysis["is_binary"] is False
        assert analysis["magic_number"] is None
        assert analysis["object_type"] == ObjectType.DATAWINDOW
        assert analysis["datawindow_subtype"] == DataWindowSubtype.DATAWINDOW
        assert analysis["null_percentage"] == 0.0
        assert analysis["has_pcode_markers"] is False
        assert analysis["has_datawindow_markers"] is False

    def test_analyze_file_content_binary(self):




        """Test analyzing binary file content."""
        # Create binary data with magic number
        data = struct.pack("<I", MagicNumbers.DATAWINDOW_HEADER)
        data += b"\x00" * 100 + b"Some text"

        analysis = ObjectTypeDetector.analyze_file_content(data, "d_report.dwo")

        assert analysis["size"] == len(data)
        assert analysis["is_binary"] is True
        assert analysis["magic_number"] == MagicNumbers.DATAWINDOW_HEADER
        assert analysis["object_type"] == ObjectType.DATAWINDOW
        assert analysis["null_percentage"] > 80
        assert analysis["has_pcode_markers"] is False
        assert analysis["has_datawindow_markers"] is False

    def test_analyze_file_content_pcode(self):




        """Test analyzing P-code file content."""
        data = b"binary data with argcount and localcount and return"

        analysis = ObjectTypeDetector.analyze_file_content(data, "w_window.win")

        assert analysis["object_type"] == ObjectType.WINDOW
        assert analysis["has_pcode_markers"] is True
        assert analysis["has_datawindow_markers"] is False

    def test_analyze_file_content_datawindow(self):




        """Test analyzing DataWindow file content."""
        data = b"release 12;\ndatawindow(units=0)\ntable(column=(type=char))"

        analysis = ObjectTypeDetector.analyze_file_content(data, "d_customer.dwo")

        assert analysis["object_type"] == ObjectType.DATAWINDOW
        assert analysis["has_pcode_markers"] is False
        assert analysis["has_datawindow_markers"] is True

    def test_validate_extraction_target_datawindow_binary(self):




        """Test validation for binary DataWindow."""
        # High null percentage DataWindow
        data = b"\x00" * 800 + b"some data" + b"\x00" * 200

        should_extract, method = ObjectTypeDetector.validate_extraction_target(data, "d_report.dwo")
        assert should_extract is True
        assert method == "datawindow_binary"

    def test_validate_extraction_target_corrupted_magic(self):




        """Test validation for corrupted magic number."""
        data = struct.pack("<I", 0x444F4D76) + b"data"

        should_extract, method = ObjectTypeDetector.validate_extraction_target(data, "test.dwo")
        assert should_extract is True
        assert method == "magic_number_recovery"

    def test_validate_extraction_target_binary_datawindow(self):




        """Test validation for binary with DataWindow markers."""
        data = b"\x00\x01\x02" * 100 + b"datawindow(" + b"\x00" * 100

        should_extract, method = ObjectTypeDetector.validate_extraction_target(data, "test")
        assert should_extract is True
        assert method == "binary_datawindow"

    def test_validate_extraction_target_text(self):




        """Test validation for text files."""
        data = b"Plain text content without binary data"

        should_extract, method = ObjectTypeDetector.validate_extraction_target(data, "test.txt")
        assert should_extract is True
        assert method == "standard"

    def test_validate_extraction_target_pcode(self):




        """Test validation for P-code files."""
        data = b"\x00\x01" * 100 + b"argcount" + b"\x00" * 50

        should_extract, method = ObjectTypeDetector.validate_extraction_target(data, "test.fun")
        assert should_extract is True
        assert method == "pcode"

    def test_validate_extraction_target_binary_recovery(self):




        """Test validation for unknown binary."""
        data = b"\x00\x01\x02\x03" * 100

        should_extract, method = ObjectTypeDetector.validate_extraction_target(data, "unknown.bin")
        assert should_extract is True
        assert method == "binary_recovery"

    def test_extension_map_completeness(self):




        """Test that EXTENSION_MAP is complete."""
        # Check that all extensions are lowercase
        for ext in ObjectTypeDetector.EXTENSION_MAP:
            assert ext == ext.lower()
            assert ext.startswith(".")

    def test_name_patterns_completeness(self):




        """Test that NAME_PATTERNS is complete."""
        # Check that all patterns end with underscore
        for pattern in ObjectTypeDetector.NAME_PATTERNS:
            assert pattern.endswith("_")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
