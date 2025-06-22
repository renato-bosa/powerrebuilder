"""Test framework for verifying opcode implementations."""

import pytest

from decompile.opcodes.opcodes import OPCODE_NAMES, OPCODE_TABLE


class TestOpcodes:
    """Test opcode definitions."""

    def test_all_opcodes_have_names(self):




        """Verify all opcodes have meaningful names."""
        for opcode, (name, _length, _hint) in OPCODE_TABLE.items():
            assert name != f"UNKNOWN_{opcode:02X}"
            assert len(name) > 0

    def test_opcode_lengths_positive(self):




        """Verify all opcodes have positive lengths."""
        for _name, length, _hint in OPCODE_TABLE.values():
            assert length > 0
            assert length <= 10  # Reasonable max

    def test_type_variants_exist(self):




        """Verify type-specific variants exist for common operations."""
        # Operations that should have type variants
        expected_variants = ["ADD", "SUB", "MULT", "DIV", "ASSIGN", "PUSH"]

        for base_op in expected_variants:
            variants = [
                name for name in OPCODE_NAMES.values() if name.startswith(base_op + "_")
            ]
            assert len(variants) > 1, f"{base_op} should have type variants"

    @pytest.mark.parametrize(
        ("opcode", "expected_name"),
        [
            (0x00, "RETURN"),
            (0x01, "STORE_RETURN_VAL"),
            (0x04, "JUMP"),
        ],
    )
    def test_known_opcodes(self, opcode, expected_name):


        """Test specific known opcodes."""
        assert OPCODE_NAMES.get(opcode) == expected_name
