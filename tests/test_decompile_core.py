"""Tests for decompile core modules."""

import pytest
from pathlib import Path
from decompile.core.pcode_decoder import PCodeDecoder
from decompile.core.expression_reconstructor import ExpressionReconstructor
from decompile.core.output_formatter import OutputFormatter
from decompile.core.simple_formatter import SimpleFormatter
from decompile.types import DecodedObject, OpcodeInstance
from common.exceptions import DecompileError


class TestPCodeDecoder:
    """Test cases for P-code decoder."""

    def setup_method(self):
        """Set up test instances."""
        self.decoder = PCodeDecoder()

    def test_decode_simple_object(self):
        """Test decoding a simple P-code object."""
        # Mock P-code data with basic opcodes
        pcode_data = b'\x00\x01\x02\x03'  # Simple test data
        
        result = self.decoder.decode_object(pcode_data, "test_object")
        
        assert isinstance(result, DecodedObject)
        assert result.name == "test_object"
        assert hasattr(result, 'opcodes')

    def test_decode_empty_object(self):
        """Test decoding empty P-code data."""
        result = self.decoder.decode_object(b'', "empty_object")
        
        assert result.name == "empty_object"
        assert len(result.opcodes) == 0

    def test_decode_with_error_handling(self):
        """Test decoder error handling."""
        # Invalid P-code data
        invalid_data = b'\xFF\xFF\xFF\xFF' * 100
        
        # Should handle gracefully
        result = self.decoder.decode_object(invalid_data, "error_object")
        assert result is not None


class TestExpressionReconstructor:
    """Test cases for expression reconstruction."""

    def setup_method(self):
        """Set up test instances."""
        self.reconstructor = ExpressionReconstructor()

    def test_reconstruct_simple_expression(self):
        """Test reconstructing a simple expression."""
        # Mock opcode for simple assignment
        opcode = OpcodeInstance(
            opcode=0x01,  # Mock assignment opcode
            operands=[1, 2],
            offset=0
        )
        
        expr = self.reconstructor.reconstruct_expression([opcode])
        assert isinstance(expr, str)

    def test_reconstruct_arithmetic_expression(self):
        """Test reconstructing arithmetic expressions."""
        # Mock opcodes for arithmetic
        opcodes = [
            OpcodeInstance(opcode=0x10, operands=[1], offset=0),  # Load
            OpcodeInstance(opcode=0x11, operands=[2], offset=1),  # Load
            OpcodeInstance(opcode=0x20, operands=[], offset=2),   # Add
        ]
        
        expr = self.reconstructor.reconstruct_expression(opcodes)
        assert isinstance(expr, str)

    def test_reconstruct_comparison(self):
        """Test reconstructing comparison expressions."""
        # Mock comparison opcodes
        opcodes = [
            OpcodeInstance(opcode=0x10, operands=[1], offset=0),
            OpcodeInstance(opcode=0x10, operands=[2], offset=1),
            OpcodeInstance(opcode=0x30, operands=[], offset=2),  # Compare
        ]
        
        expr = self.reconstructor.reconstruct_expression(opcodes)
        assert isinstance(expr, str)


class TestOutputFormatter:
    """Test cases for output formatting."""

    def setup_method(self):
        """Set up test instances."""
        self.formatter = OutputFormatter()

    def test_format_simple_object(self):
        """Test formatting a simple decoded object."""
        decoded_obj = DecodedObject(
            name="test_function",
            object_type="function",
            opcodes=[],
            metadata={"returns": "integer"}
        )
        
        output = self.formatter.format_object(decoded_obj)
        assert isinstance(output, list)
        assert any("test_function" in line for line in output)

    def test_format_with_control_blocks(self):
        """Test formatting with control flow blocks."""
        decoded_obj = DecodedObject(
            name="test_method",
            object_type="function",
            opcodes=[]
        )
        
        control_blocks = [
            {"type": "if", "start": 0, "end": 10},
            {"type": "loop", "start": 20, "end": 30}
        ]
        
        output = self.formatter.format_object(decoded_obj, control_blocks)
        assert isinstance(output, list)

    def test_format_header_generation(self):
        """Test header comment generation."""
        header = self.formatter._generate_header(
            "w_main",
            "window",
            "main.pbl"
        )
        
        assert isinstance(header, list)
        assert any("w_main" in line for line in header)
        assert any("window" in line for line in header)

    def test_format_metadata_handling(self):
        """Test metadata formatting."""
        decoded_obj = DecodedObject(
            name="dw_list",
            object_type="datawindow",
            opcodes=[],
            metadata={
                "sql": "SELECT * FROM customers",
                "columns": ["id", "name", "balance"]
            }
        )
        
        output = self.formatter.format_object(decoded_obj)
        assert isinstance(output, list)
        # Should include SQL information
        assert any("SELECT" in line for line in output)


class TestSimpleFormatter:
    """Test cases for simple formatter."""

    def setup_method(self):
        """Set up test instances."""
        self.formatter = SimpleFormatter()

    def test_format_opcode(self):
        """Test formatting individual opcodes."""
        opcode = OpcodeInstance(
            opcode=0x01,
            operands=[10, 20],
            offset=100
        )
        
        result = self.formatter.format_opcode(opcode)
        assert isinstance(result, str)
        assert "0x01" in result or "01" in result

    def test_format_opcode_with_mnemonic(self):
        """Test formatting with mnemonic names."""
        opcode = OpcodeInstance(
            opcode=0x10,  # Assume this is LOAD
            operands=[5],
            offset=0,
            mnemonic="LOAD"
        )
        
        result = self.formatter.format_opcode(opcode)
        assert "LOAD" in result

    def test_format_special_opcodes(self):
        """Test formatting special opcodes."""
        # Test jump opcode
        jump_opcode = OpcodeInstance(
            opcode=0x50,  # Assume jump
            operands=[200],  # Jump target
            offset=100,
            mnemonic="JMP"
        )
        
        result = self.formatter.format_opcode(jump_opcode)
        assert isinstance(result, str)

    def test_format_with_indentation(self):
        """Test formatting with indentation."""
        opcodes = [
            OpcodeInstance(opcode=0x01, operands=[], offset=0),
            OpcodeInstance(opcode=0x02, operands=[], offset=1),
        ]
        
        result = self.formatter.format_opcodes(opcodes, indent_level=2)
        assert all(line.startswith("    ") or line == "" for line in result)


class TestDecompileIntegration:
    """Integration tests for decompile components."""

    def test_full_decompile_flow(self):
        """Test the full decompile flow."""
        # Create test P-code data
        test_data = b'\x10\x01\x11\x02\x20\x00'  # Load 1, Load 2, Add
        
        # Decode
        decoder = PCodeDecoder()
        decoded = decoder.decode_object(test_data, "test_add")
        
        # Format
        formatter = OutputFormatter()
        output = formatter.format_object(decoded)
        
        assert isinstance(output, list)
        assert len(output) > 0

    def test_error_recovery(self):
        """Test error recovery in decompile flow."""
        # Invalid data that should trigger error recovery
        bad_data = b'\xFF' * 1000
        
        decoder = PCodeDecoder()
        decoded = decoder.decode_object(bad_data, "bad_object")
        
        # Should still produce some output
        formatter = OutputFormatter()
        output = formatter.format_object(decoded)
        
        assert isinstance(output, list)
        # Should include error information
        assert any("error" in line.lower() or "failed" in line.lower() 
                  for line in output)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])