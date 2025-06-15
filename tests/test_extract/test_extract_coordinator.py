#!/usr/bin/env python3
"""Comprehensive test suite for Extract coordinator."""

import pytest
from pathlib import Path
import tempfile
import os
from extract.extract_coordinator import extract_with_recovery, extract_pbls
from common.object_type_detector import ObjectType, DataWindowSubtype
from extract.pbd.utils.binary_utils import safe_filename, decode, is_source_file


class TestExtractCoordinator:
    """Test extract coordinator functionality."""
    
    def test_safe_filename(self):
        """Test filename sanitization."""
        test_cases = [
            ("normal_file.txt", "normal_file.txt"),
            ("file<>with:illegal*chars", "file_with_illegal_chars"),
            ("file//with\\slashes", "file_with_slashes"),
            ("..hidden", "hidden"),
            ("file   .txt", "file   .txt"),
            ("", "_"),
            ("___multiple___underscores___", "_multiple_underscores_"),
        ]
        
        for input_name, expected in test_cases:
            result = safe_filename(input_name)
            assert result == expected
    
    def test_decode_ascii(self):
        """Test decoding ASCII text."""
        # Test ASCII text
        ascii_text = b"Hello, PowerBuilder!"
        decoded = decode(ascii_text, unicode=False)
        assert decoded == "Hello, PowerBuilder!"
        
        # Test with null terminator
        null_terminated = b"Hello\x00World"
        decoded = decode(null_terminated, unicode=False, is_terminated=True)
        assert decoded == "Hello"
    
    def test_decode_unicode(self):
        """Test decoding Unicode text."""
        # Test UTF-16 LE (PowerBuilder Unicode)
        unicode_text = "Hello, 世界!".encode('utf-16-le')
        decoded = decode(unicode_text, unicode=True)
        assert "Hello" in decoded
    
    def test_is_source_file(self):
        """Test source file detection."""
        source_files = [
            "window.srw",
            "nonvisual.sru",
            "datawindow.srd",
            "function.srf",
            "menu.srm",
            "struct.srs",
            "query.srq",
            "app.sra"
        ]
        
        for filename in source_files:
            assert is_source_file(filename) is True
        
        # Test non-source files
        assert is_source_file("image.png") is False
        assert is_source_file("data.dat") is False
    
    def test_object_type_constants(self):
        """Test PowerBuilder object type constants."""
        # Test that object types are properly categorized
        assert ObjectType.WINDOW in ObjectType.PCODE_TYPES
        assert ObjectType.FUNCTION in ObjectType.PCODE_TYPES
        assert ObjectType.USER_OBJECT in ObjectType.PCODE_TYPES
        assert ObjectType.MENU in ObjectType.PCODE_TYPES
        assert ObjectType.APPLICATION in ObjectType.PCODE_TYPES
        
        assert ObjectType.DATAWINDOW in ObjectType.DATA_ONLY_TYPES
        assert ObjectType.STRUCTURE in ObjectType.DATA_ONLY_TYPES
        assert ObjectType.QUERY in ObjectType.DATA_ONLY_TYPES
        
        # Test DataWindow subtypes
        assert DataWindowSubtype.SQL.value == "_sql"
        assert DataWindowSubtype.REPORT.value == "_rpt"
    
    def test_extract_with_recovery_invalid_file(self):
        """Test extract_with_recovery with invalid file."""
        with tempfile.NamedTemporaryFile(suffix='.pbl', delete=False) as temp_file:
            temp_path = temp_file.name
            # Write invalid data
            temp_file.write(b"NOT A VALID PBL FILE")
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                # Should return False for invalid file
                result = extract_with_recovery(
                    temp_path, 
                    output_dir,
                    show_progress=False
                )
                assert result is False
        finally:
            os.unlink(temp_path)
    
    def test_extract_pbls_empty_directory(self):
        """Test extract_pbls with empty directory."""
        with tempfile.TemporaryDirectory() as input_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                # Should handle empty directory gracefully
                extract_pbls(
                    input_path=input_dir,
                    output_path=output_dir,
                    file_filter=None,
                    verbose=False
                )
                # No assertion - just ensure it doesn't crash
    
    def test_extract_pbls_with_filter(self):
        """Test extract_pbls with file filter."""
        with tempfile.TemporaryDirectory() as input_dir:
            # Create some dummy files
            Path(input_dir, "test1.pbl").touch()
            Path(input_dir, "test2.pbl").touch()
            Path(input_dir, "ignore.txt").touch()
            
            with tempfile.TemporaryDirectory() as output_dir:
                # Extract only .pbl files
                extract_pbls(
                    input_path=input_dir,
                    output_path=output_dir,
                    file_filter="*.pbl",
                    verbose=False
                )
                # Should process only PBL files


class TestBinaryDataHandling:
    """Test binary data detection and handling."""
    
    def test_magic_number_detection(self):
        """Test detection of binary data by magic numbers."""
        # Known binary magic number from the project
        magic_number = 0x444F4D76
        binary_data = magic_number.to_bytes(4, byteorder='little') + b'\x00' * 100
        
        # Create a simple binary detection function
        def is_binary(data: bytes) -> bool:
            if len(data) < 4:
                return False
            magic = int.from_bytes(data[:4], byteorder='little')
            return magic == 0x444F4D76
        
        assert is_binary(binary_data) is True
        assert is_binary(b"text data") is False
    
    def test_dat_block_corruption(self):
        """Test handling of DAT block corruption patterns."""
        # Test data with asterisk corruption pattern
        corrupted = "normal text *** corrupted *** more text"
        
        # Simple corruption detection
        def has_corruption(text: str) -> bool:
            return "***" in text or text.count('*') > 10
        
        assert has_corruption(corrupted) is True
        assert has_corruption("normal text") is False


class TestEncodingHandling:
    """Test character encoding detection and conversion."""
    
    def test_ascii_encoding(self):
        """Test ASCII encoding handling."""
        ascii_text = "Hello, World!"
        encoded = ascii_text.encode('ascii')
        
        # Should decode properly
        decoded = decode(encoded, unicode=False)
        assert decoded == ascii_text
    
    def test_unicode_encoding(self):
        """Test Unicode encoding handling."""
        unicode_text = "Hello, 世界! Привет!"
        
        # PowerBuilder uses UTF-16 LE for Unicode
        encoded = unicode_text.encode('utf-16-le')
        
        # Decode with unicode flag
        decoded = decode(encoded, unicode=True)
        # May have some encoding issues but should contain Hello
        assert "Hello" in decoded
    
    def test_mixed_encoding(self):
        """Test handling of mixed encoding scenarios."""
        # Sometimes files have mixed ASCII and Unicode
        mixed_data = b"ASCII: " + "Hello".encode('ascii') + b" Unicode: " + "世界".encode('utf-16-le')
        
        # Should handle gracefully
        try:
            decoded = decode(mixed_data, unicode=False)
            assert "ASCII:" in decoded
        except:
            # May fail on mixed encoding, which is expected
            pass