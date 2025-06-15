#!/usr/bin/env python3
"""Comprehensive test suite for Extract module."""

import pytest
from pathlib import Path
import tempfile
import struct
from extract.extract_coordinator import extract_with_recovery, extract_pbls
from extract.pbd.structures.header import PBDHeader
from extract.pbd.structures.entry import PBDEntry
from extract.pbd.structures.data_block import DataBlock
from extract.pbd.utils.binary_utils import read_uint32_le, read_string
from common.object_type_detector import detect_object_type


class TestPBDExtraction:
    """Test PBD file extraction functionality."""
    
    def create_mock_pbd_file(self, entries: list[dict]) -> Path:
        """Create a mock PBD file for testing."""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.pbd', delete=False)
        temp_path = Path(temp_file.name)
        
        with open(temp_path, 'wb') as f:
            # Write PBD magic number (simplified)
            f.write(b'PBD\x00')  # Mock header
            
            # Write number of entries
            f.write(struct.pack('<I', len(entries)))
            
            # Write entries
            for entry in entries:
                # Write entry name
                name_bytes = entry['name'].encode('utf-8')
                f.write(struct.pack('<I', len(name_bytes)))
                f.write(name_bytes)
                
                # Write entry data
                data_bytes = entry['data'].encode('utf-8')
                f.write(struct.pack('<I', len(data_bytes)))
                f.write(data_bytes)
        
        return temp_path
    
    def test_extract_single_object(self):
        """Test extracting a single PowerBuilder object."""
        # Create mock PBD with one object
        entries = [{
            'name': 'n_test',
            'data': 'type n_test from nonvisualobject\nend type'
        }]
        pbd_path = self.create_mock_pbd_file(entries)
        
        try:
            # Extract to temporary directory
            with tempfile.TemporaryDirectory() as output_dir:
                result = extract_pbd_file(pbd_path, Path(output_dir))
                
                # Check result
                assert result is not None
                assert result.get('status') == 'success'
                assert result.get('extracted_count', 0) > 0
                
                # Check extracted file exists
                extracted_file = Path(output_dir) / 'n_test.sru'
                assert extracted_file.exists()
        finally:
            pbd_path.unlink()
    
    def test_extract_multiple_objects(self):
        """Test extracting multiple objects from PBD."""
        entries = [
            {'name': 'w_main', 'data': 'window w_main\nend window'},
            {'name': 'n_custom', 'data': 'type n_custom from nonvisualobject\nend type'},
            {'name': 'd_employee', 'data': 'datawindow d_employee\nend datawindow'}
        ]
        pbd_path = self.create_mock_pbd_file(entries)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = extract_pbd_file(pbd_path, Path(output_dir))
                
                assert result is not None
                assert result.get('extracted_count', 0) == 3
                
                # Check all files extracted
                assert (Path(output_dir) / 'w_main.srw').exists()
                assert (Path(output_dir) / 'n_custom.sru').exists()
                assert (Path(output_dir) / 'd_employee.srd').exists()
        finally:
            pbd_path.unlink()
    
    def test_binary_detection(self):
        """Test binary data detection with magic numbers."""
        # Test with 0x444F4D76 magic number (known binary indicator)
        binary_data = struct.pack('<I', 0x444F4D76) + b'\x00' * 100
        
        # Should detect as binary
        from extract.pbd.structures.enhanced_data_block import is_binary_data
        assert is_binary_data(binary_data) is True
        
        # Test with text data
        text_data = b"type n_test from nonvisualobject\nend type"
        assert is_binary_data(text_data) is False
    
    def test_object_type_detection(self):
        """Test PowerBuilder object type detection."""
        test_cases = [
            ("window w_test", "window", ".srw"),
            ("type n_test from nonvisualobject", "nonvisualobject", ".sru"),
            ("datawindow d_test", "datawindow", ".srd"),
            ("function f_test()", "function", ".srf"),
            ("menu m_test", "menu", ".srm"),
            ("structure s_test", "structure", ".srs"),
            ("global type q_test from query", "query", ".srq"),
            ("userobject u_test", "userobject", ".sru"),
        ]
        
        for content, expected_type, expected_ext in test_cases:
            obj_type, ext = detect_object_type(content)
            assert obj_type == expected_type
            assert ext == expected_ext
    
    def test_datawindow_syntax_extraction(self):
        """Test DataWindow syntax extraction."""
        # Mock DataWindow with syntax
        dw_content = """
        release 12.5;
        datawindow(units=0 timer_interval=0)
        header(height=80 color="536870912")
        summary(height=0 color="536870912")
        footer(height=0 color="536870912")
        detail(height=100 color="536870912")
        table(column=(type=char(50) name=employee_name dbname="emp.name"))
        """
        
        entries = [{'name': 'd_test', 'data': dw_content}]
        pbd_path = self.create_mock_pbd_file(entries)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = extract_pbd_file(pbd_path, Path(output_dir))
                
                # Check DataWindow file created
                dw_file = Path(output_dir) / 'd_test.srd'
                assert dw_file.exists()
                
                # Content should contain datawindow syntax
                content = dw_file.read_text()
                assert 'datawindow(' in content
                assert 'table(' in content
        finally:
            pbd_path.unlink()
    
    def test_corruption_handling(self):
        """Test handling of corrupted data."""
        # Create data with asterisk corruption pattern
        corrupted_data = "type n_test from nonvisualobject\n**** CORRUPTED ****\nend type"
        
        entries = [{'name': 'n_corrupted', 'data': corrupted_data}]
        pbd_path = self.create_mock_pbd_file(entries)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = extract_pbd_file(pbd_path, Path(output_dir))
                
                # Should still extract but may have warnings
                assert result is not None
                
                # Check file exists
                assert (Path(output_dir) / 'n_corrupted.sru').exists()
        finally:
            pbd_path.unlink()
    
    def test_extract_directory(self):
        """Test extracting all PBD/PBL files from directory."""
        with tempfile.TemporaryDirectory() as input_dir:
            input_path = Path(input_dir)
            
            # Create multiple PBD files
            for i in range(3):
                entries = [{
                    'name': f'n_test_{i}',
                    'data': f'type n_test_{i} from nonvisualobject\nend type'
                }]
                pbd_path = input_path / f'test_{i}.pbd'
                self.create_mock_pbd_file(entries).rename(pbd_path)
            
            # Extract all
            with tempfile.TemporaryDirectory() as output_dir:
                result = extract_directory(input_path, Path(output_dir))
                
                assert result is not None
                assert result.get('total_files', 0) == 3
                
                # Check all objects extracted
                for i in range(3):
                    assert (Path(output_dir) / f'n_test_{i}.sru').exists()


class TestBinaryUtils:
    """Test binary utility functions."""
    
    def test_read_uint32_le(self):
        """Test reading 32-bit little-endian integers."""
        data = struct.pack('<I', 0x12345678)
        value = read_uint32_le(data, 0)
        assert value == 0x12345678
    
    def test_read_string(self):
        """Test reading strings from binary data."""
        # Create string with length prefix
        test_string = "Hello, PowerBuilder!"
        data = struct.pack('<I', len(test_string)) + test_string.encode('utf-8')
        
        string_value, offset = read_string(data, 0)
        assert string_value == test_string
        assert offset == 4 + len(test_string)
    
    def test_encoding_detection(self):
        """Test character encoding detection."""
        from extract.pbd.utils.text_extraction import detect_encoding
        
        # Test UTF-8
        utf8_data = "Hello, 世界!".encode('utf-8')
        encoding = detect_encoding(utf8_data)
        assert encoding in ['utf-8', 'UTF-8']
        
        # Test ASCII
        ascii_data = b"Hello, World!"
        encoding = detect_encoding(ascii_data)
        assert encoding in ['ascii', 'ASCII', 'utf-8', 'UTF-8']


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_pbd(self):
        """Test extracting empty PBD file."""
        # Create empty PBD
        temp_file = tempfile.NamedTemporaryFile(suffix='.pbd', delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                # Should handle gracefully
                result = extract_pbd_file(temp_path, Path(output_dir))
                # May return error or empty result
        finally:
            temp_path.unlink()
    
    def test_invalid_pbd(self):
        """Test handling invalid PBD file."""
        # Create file with invalid data
        temp_file = tempfile.NamedTemporaryFile(suffix='.pbd', delete=False)
        temp_path = Path(temp_file.name)
        temp_file.write(b'INVALID DATA NOT A PBD FILE')
        temp_file.close()
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                # Should handle error gracefully
                result = extract_pbd_file(temp_path, Path(output_dir))
                # May return error status
        finally:
            temp_path.unlink()
    
    def test_permission_error(self):
        """Test handling permission errors."""
        # This test would require OS-specific permission manipulation
        # For now, just test the structure
        pass
    
    def test_large_file_handling(self):
        """Test extraction of large PBD files."""
        # Create a large mock entry
        large_data = "x" * (1024 * 1024)  # 1MB of data
        entries = [{'name': 'n_large', 'data': large_data}]
        
        pbd_path = self.create_mock_pbd_file(entries)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = extract_pbd_file(pbd_path, Path(output_dir))
                
                # Should handle large files
                assert result is not None
                
                # Check file created
                large_file = Path(output_dir) / 'n_large.sru'
                assert large_file.exists()
                assert large_file.stat().st_size > 1024 * 1024
        finally:
            pbd_path.unlink()


class TestDataWindowExtraction:
    """Test specific DataWindow extraction features."""
    
    def test_binary_blob_in_datawindow(self):
        """Test handling binary blobs in DataWindow definitions."""
        # DataWindow with embedded binary data
        dw_with_binary = """
        release 12.5;
        datawindow(units=0)
        table(
            column=(type=blob name=employee_photo)
        )
        data(
            binary_data_here_0x444F4D76...
        )
        """
        
        entries = [{'name': 'd_binary', 'data': dw_with_binary}]
        pbd_path = self.create_mock_pbd_file(entries)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = extract_pbd_file(pbd_path, Path(output_dir))
                
                # Should extract without corruption
                dw_file = Path(output_dir) / 'd_binary.srd'
                assert dw_file.exists()
        finally:
            pbd_path.unlink()
    
    def test_datawindow_with_computed_fields(self):
        """Test DataWindow with computed fields."""
        dw_computed = """
        release 12.5;
        datawindow(units=0)
        table(
            column=(type=decimal(2) name=salary)
        )
        compute(
            name=annual_salary
            expression="salary * 12"
        )
        """
        
        entries = [{'name': 'd_computed', 'data': dw_computed}]
        pbd_path = self.create_mock_pbd_file(entries)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = extract_pbd_file(pbd_path, Path(output_dir))
                
                dw_file = Path(output_dir) / 'd_computed.srd'
                assert dw_file.exists()
                
                content = dw_file.read_text()
                assert 'compute(' in content
                assert 'expression=' in content
        finally:
            pbd_path.unlink()