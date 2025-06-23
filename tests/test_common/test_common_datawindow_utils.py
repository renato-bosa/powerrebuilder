"""Tests for common.datawindow_utils module."""

import logging

import pytest

from common.datawindow_utils import DataWindowDetector


class TestDataWindowDetector:
    """Test DataWindowDetector class."""

    def test_detect_format_binary(self):




        """Test detecting binary DataWindow format."""
        # Test with DWHD signature
        data = b"DWHD\x00\x01\x02\x03binary data"
        assert DataWindowDetector.detect_format(data) == "binary"

        # Test with alternative header format
        data = b"\x00\x00\x00\x00DWHD more data"
        assert DataWindowDetector.detect_format(data) == "binary"

        # Test with UTF-16 BOM
        data = b"\xff\xfe\x00\x00some unicode data"
        assert DataWindowDetector.detect_format(data) == "binary"

        # Test with UTF-16 BE BOM
        data = b"\xfe\xff\x00\x00some unicode data"
        assert DataWindowDetector.detect_format(data) == "binary"

    def test_detect_format_text(self):




        """Test detecting text DataWindow format."""
        # Test with release signature
        data = b"release 12;\ndatawindow(..."
        assert DataWindowDetector.detect_format(data) == "text"

        # Test with export header
        data = b"HA$PBExportHeader$datawindow.srd"
        assert DataWindowDetector.detect_format(data) == "text"

        # Test with export comments
        data = b"$PBExportComments$\nDataWindow object"
        assert DataWindowDetector.detect_format(data) == "text"

        # Test with datawindow keyword
        data = b"datawindow(units=0 timer_interval=0)"
        assert DataWindowDetector.detect_format(data) == "text"

        # Test with table keyword
        data = b"table(column=(type=char(10) name=id))"
        assert DataWindowDetector.detect_format(data) == "text"

        # Test with column keyword (note: signature is "column(" not "column=")
        data = b"column(type=char updatewhereclause=yes)"
        assert DataWindowDetector.detect_format(data) == "text"

    def test_detect_format_none(self):




        """Test when no DataWindow format is detected."""
        data = b"This is just regular text without any signatures"
        assert DataWindowDetector.detect_format(data) is None

        # Test with empty data
        data = b""
        assert DataWindowDetector.detect_format(data) is None

    def test_detect_format_max_check_bytes(self):




        """Test format detection with limited bytes."""
        # Signature at the beginning
        data = b"DWHD" + b"x" * 10000
        assert DataWindowDetector.detect_format(data, max_check_bytes=10) == "binary"

        # Signature beyond check limit
        data = b"x" * 5000 + b"DWHD"
        assert DataWindowDetector.detect_format(data, max_check_bytes=4096) is None

    def test_extract_metadata_no_format(self):




        """Test metadata extraction when format is not detected."""
        data = b"random data"
        metadata = DataWindowDetector.extract_metadata(data)

        assert metadata["format"] is None
        assert metadata["type"] is None
        assert metadata["has_syntax"] is False
        assert metadata["has_header"] is False
        assert metadata["encoding"] is None
        assert metadata["table_count"] == 0
        assert metadata["column_count"] == 0

    def test_extract_metadata_with_header(self):




        """Test metadata extraction with header marker."""
        data = b"$PBExportHeader$datawindow.srd\nrelease 12;"
        metadata = DataWindowDetector.extract_metadata(data)

        assert metadata["format"] == "text"
        assert metadata["has_header"] is True

    def test_extract_metadata_encoding_detection(self):




        """Test encoding detection from BOM."""
        # UTF-16 LE
        data = b"\xff\xfe" + "release 12;".encode("utf-16-le")
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["encoding"] == "utf-16-le"

        # UTF-16 BE
        data = b"\xfe\xff" + "release 12;".encode("utf-16-be")
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["encoding"] == "utf-16-be"

        # UTF-8 BOM
        data = b"\xef\xbb\xbf" + b"release 12;"
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["encoding"] == "utf-8"

    def test_extract_metadata_type_detection(self):




        """Test DataWindow type detection."""
        # Tabular type (processing="1" without grid-specific attributes)
        data = b'release 12;\ndatawindow(processing="1")'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["type"] == "tabular"

        # Grid type (processing="1" with grid-specific attributes)
        data = b'release 12;\ndatawindow(processing="1" grid.lines=1)'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["type"] == "grid"

        # Freeform type
        data = b'release 12;\ndatawindow(processing="0")'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["type"] == "freeform"

        # Label type
        data = b'release 12;\ndatawindow(processing="2")'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["type"] == "label"

        # Graph type
        data = b'release 12;\ngraph(name="gr_1")'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["type"] == "graph"

        # Crosstab type
        data = b'release 12;\ncrosstab(columns="month")'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["type"] == "crosstab"

        # OLE type
        data = b'release 12;\nole(name="ole_1")'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["type"] == "ole"

        # RichText type
        data = b'release 12;\nrichtext(name="rt_1")'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["type"] == "richtext"

    def test_extract_metadata_counts(self):




        """Test counting tables and columns."""
        data = b"""release 12;
        table(name=customer)
        column(type=char(10) name=id)
        column(type=char(50) name=name)
        table(name=orders)
        column(type=decimal(2) name=amount)
        """
        metadata = DataWindowDetector.extract_metadata(data)

        assert metadata["table_count"] == 2
        assert metadata["column_count"] == 3

    def test_extract_metadata_syntax_detection(self):




        """Test syntax section detection."""
        data = b'release 12;\nsyntax="SELECT * FROM customer"'
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["has_syntax"] is True

        data = b"release 12;\ndatawindow(units=0)"
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["has_syntax"] is False

    def test_extract_metadata_encoding_fallback(self):




        """Test encoding detection with fallbacks."""
        # Data that's valid in latin-1 but not UTF-8
        data = b"release 12;\xE9\xE8"  # é and è in latin-1
        metadata = DataWindowDetector.extract_metadata(data)
        assert metadata["encoding"] == "latin-1"

    def test_extract_metadata_unicode_error_handling(self, caplog):




        """Test handling of unicode decode errors."""
        # Invalid UTF-8 sequence
        data = b"\xff\xfe\xff\xff"  # Invalid data
        with caplog.at_level(logging.DEBUG):
            metadata = DataWindowDetector.extract_metadata(data)

        # Should still detect as binary due to BOM
        assert metadata["format"] == "binary"

    def test_validate_syntax_valid(self):




        """Test validating correct DataWindow syntax."""
        syntax = """release 12;
datawindow(units=0 timer_interval=0)
table(column=(type=char(10) name=id))
"""
        is_valid, issues = DataWindowDetector.validate_syntax(syntax)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_syntax_missing_keywords(self):




        """Test validation with missing required keywords."""
        # Missing 'release'
        syntax = "datawindow(units=0) table()"
        is_valid, issues = DataWindowDetector.validate_syntax(syntax)
        assert is_valid is False
        assert "Missing required keyword: release" in issues

        # Missing 'datawindow'
        syntax = "release 12; table()"
        is_valid, issues = DataWindowDetector.validate_syntax(syntax)
        assert is_valid is False
        assert "Missing required keyword: datawindow" in issues

    def test_validate_syntax_mismatched_parentheses(self):




        """Test validation with mismatched parentheses."""
        syntax = "release 12; datawindow(units=0 table("
        is_valid, issues = DataWindowDetector.validate_syntax(syntax)
        assert is_valid is False
        assert "Mismatched parentheses" in issues

    def test_validate_syntax_no_data_source(self):




        """Test validation with no data source."""
        syntax = "release 12; datawindow(units=0)"
        is_valid, issues = DataWindowDetector.validate_syntax(syntax)
        assert is_valid is False
        assert "No data source defined (table or external)" in issues

    def test_validate_syntax_external_source(self):




        """Test validation with external data source."""
        syntax = "release 12; datawindow(units=0) external()"
        is_valid, issues = DataWindowDetector.validate_syntax(syntax)
        assert is_valid is True
        assert len(issues) == 0

    def test_validate_syntax_table_no_columns(self):




        """Test validation with table but no columns."""
        syntax = "release 12; datawindow(units=0) table()"
        is_valid, issues = DataWindowDetector.validate_syntax(syntax)
        assert is_valid is False
        assert "Table defined but no columns" in issues

    def test_extract_sql_simple(self):




        """Test extracting simple SQL statement."""
        syntax = '''datawindow(retrieve="SELECT * FROM customer")'''
        sql = DataWindowDetector.extract_sql(syntax)
        assert sql == "SELECT * FROM customer"

    def test_extract_sql_with_escaped_quotes(self):




        """Test extracting SQL with escaped quotes."""
        syntax = '''datawindow(retrieve="SELECT name FROM customer WHERE type=~"VIP~"")'''
        sql = DataWindowDetector.extract_sql(syntax)
        assert sql == 'SELECT name FROM customer WHERE type="VIP"'

    def test_extract_sql_multiline(self):




        """Test extracting multiline SQL statement."""
        syntax = '''
        datawindow(
            retrieve="SELECT id, name
                     FROM customer
                     WHERE active = 1"
        )
        '''
        sql = DataWindowDetector.extract_sql(syntax)
        assert sql == """SELECT id, name
                     FROM customer
                     WHERE active = 1"""

    def test_extract_sql_none(self):




        """Test when no SQL is found."""
        syntax = "datawindow(units=0) table()"
        sql = DataWindowDetector.extract_sql(syntax)
        assert sql is None

    def test_extract_sql_case_insensitive(self):




        """Test SQL extraction is case insensitive."""
        syntax = '''DATAWINDOW(RETRIEVE="SELECT * FROM customer")'''
        sql = DataWindowDetector.extract_sql(syntax)
        assert sql == "SELECT * FROM customer"

    def test_is_datawindow_file_by_extension(self):




        """Test DataWindow file detection by extension."""
        assert DataWindowDetector.is_datawindow_file("customer.srd") is True
        assert DataWindowDetector.is_datawindow_file("CUSTOMER.SRD") is True
        assert DataWindowDetector.is_datawindow_file("test.srd.bak") is False
        assert DataWindowDetector.is_datawindow_file("window.srw") is False

    def test_is_datawindow_file_by_prefix(self):




        """Test DataWindow file detection by prefix patterns."""
        # d_ prefix
        assert DataWindowDetector.is_datawindow_file("d_customer.psr") is True
        assert DataWindowDetector.is_datawindow_file("D_CUSTOMER") is True

        # dw_ prefix
        assert DataWindowDetector.is_datawindow_file("dw_order_list.psr") is True
        assert DataWindowDetector.is_datawindow_file("DW_ORDER") is True

        # dwo_ prefix
        assert DataWindowDetector.is_datawindow_file("dwo_report.psr") is True
        assert DataWindowDetector.is_datawindow_file("DWO_REPORT") is True

        # Not DataWindow prefixes
        assert DataWindowDetector.is_datawindow_file("w_customer.psr") is False
        assert DataWindowDetector.is_datawindow_file("customer_d.psr") is False

    def test_is_datawindow_file_by_suffix(self):




        """Test DataWindow file detection by suffix patterns."""
        # _dw suffix
        assert DataWindowDetector.is_datawindow_file("customer_dw") is True
        assert DataWindowDetector.is_datawindow_file("ORDER_DW.psr") is True

        # _dwo suffix
        assert DataWindowDetector.is_datawindow_file("report_dwo") is True
        assert DataWindowDetector.is_datawindow_file("SALES_DWO.psr") is True

        # Not DataWindow suffixes
        assert DataWindowDetector.is_datawindow_file("customer_window") is False
        assert DataWindowDetector.is_datawindow_file("dw") is False

    def test_class_variables(self):




        """Test that class variables are properly defined."""
        # Check BINARY_SIGNATURES
        assert len(DataWindowDetector.BINARY_SIGNATURES) == 4
        assert b"DWHD" in DataWindowDetector.BINARY_SIGNATURES

        # Check TEXT_SIGNATURES
        assert len(DataWindowDetector.TEXT_SIGNATURES) == 6
        assert b"release " in DataWindowDetector.TEXT_SIGNATURES

        # Check FORMAT_PATTERNS
        assert len(DataWindowDetector.FORMAT_PATTERNS) == 8
        assert "grid" in DataWindowDetector.FORMAT_PATTERNS
        assert "graph" in DataWindowDetector.FORMAT_PATTERNS

        # Check SECTION_MARKERS
        assert len(DataWindowDetector.SECTION_MARKERS) == 4
        assert DataWindowDetector.SECTION_MARKERS["header"] == b"$PBExportHeader$"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
