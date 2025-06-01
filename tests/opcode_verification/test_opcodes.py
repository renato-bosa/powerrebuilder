"""
Test framework for verifying opcode implementations.
"""

import pytest
from pathlib import Path
from decompile.opcodes_unified import OPCODES, get_opcode_name, get_opcode_length

class TestOpcodes:
    """Test opcode definitions."""

    def test_all_opcodes_have_names(self):
        """Verify all opcodes have meaningful names."""
        for opcode, info in OPCODES.items():
            assert info.name != f"UNKNOWN_{opcode:02X}"
            assert len(info.name) > 0

    def test_opcode_lengths_positive(self):
        """Verify all opcodes have positive lengths."""
        for opcode, info in OPCODES.items():
            assert info.length > 0
            assert info.length <= 10  # Reasonable max

    def test_type_variants_exist(self):
        """Verify type-specific variants exist for common operations."""
        # Operations that should have type variants
        expected_variants = ["ADD", "SUB", "MUL", "DIV", "ASSIGN", "PUSH"]
        
        for base_op in expected_variants:
            variants = [name for name in [info.name for info in OPCODES.values()] 
                       if name.startswith(base_op + "_")]
            assert len(variants) > 1, f"{base_op} should have type variants"

    @pytest.mark.parametrize("opcode,expected_name", [
        (0x00, "RETURN"),
        (0x01, "STORE_RETURN_VAL"),
        (0x04, "JUMP"),
    ])
    def test_known_opcodes(self, opcode, expected_name):
        """Test specific known opcodes."""
        assert get_opcode_name(opcode) == expected_name
