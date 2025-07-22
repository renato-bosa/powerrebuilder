#!/usr/bin/env python3
"""Enhanced tests for the simple formatter with special opcode handling."""

from typing import List

from src.decompile.pcode.decoder import DecodedObject, PCodeInstruction
from src.decompile.core.formatter import SimpleFormatter
from src.extract.utils.version import PowerBuilderVersion


def create_instruction(address: int, opcode_value: int, opcode_name: str, operand_values: List = None, text_format: str = None) -> PCodeInstruction:








    """Helper to create PCodeInstruction with proper dataclass format."""
    return PCodeInstruction(
        address=address, opcode=bytes([opcode_value]), opcode_name=opcode_name, operands=b"", operand_values=operand_values or [], text_format=text_format or opcode_name, opcode_value=opcode_value,
    )


class TestSimpleFormatterEnhanced:
    """Test the enhanced simple formatter with special opcode handling."""

    def test_format_special_opcodes_jumps(self):




        """Test formatting jump instructions with proper labels."""
        formatter = SimpleFormatter()

        # Create a decoded object with jump instructions
        decoded_obj = DecodedObject(
            name="process_condition", type="function", version=PowerBuilderVersion(10, 5, True), instructions=[
                create_instruction(0, 0x20, "JUMPFALSE", [10]), # Jump to offset 10
                create_instruction(2, 0x01, "PUSH_CONST_INT", [1]), create_instruction(4, 0x99, "RETURN", [0]), create_instruction(10, 0x01, "PUSH_CONST_INT", [0]), # Jump target
                create_instruction(12, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        result_text = "\n".join(result)

        # Verify jump formatting
        assert "if not lb_condition then goto" in result_text
        assert "L_" in result_text  # Should have label

    def test_format_special_opcodes_function_calls(self):




        """Test formatting various function call opcodes."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="call_functions", type="function", version=PowerBuilderVersion(10, 5, True), instructions=[
                create_instruction(0, 0x30, "GLOBFUNCCALL", [100]), create_instruction(2, 0x31, "CALL_FUNCTION", [200]), create_instruction(4, 0x32, "DLLFUNCCALL", [0]), # MessageBoxA
                create_instruction(6, 0x33, "SYSFUNCCALL", [2]), # Upper
                create_instruction(8, 0x34, "DOTFUNCCALL", [1]), # gettext
                create_instruction(10, 0x35, "CLASS_CALL", [0]), # datawindow
                create_instruction(12, 0x36, "EVENTCALL", [0]), # clicked
                create_instruction(14, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        lines = result  # Already a list of lines

        # Check for proper function call formatting
        assert any("gf_function_100()" in line for line in lines)
        assert any("lf_function_200()" in line for line in lines)
        assert any("MessageBoxA()" in line for line in lines)
        assert any("Upper()" in line for line in lines)
        assert any("gettext()" in line for line in lines)
        assert any("datawindow.constructor()" in line for line in lines)
        assert any("this.event clicked()" in line for line in lines)

    def test_format_special_opcodes_constants(self):




        """Test formatting push constant instructions."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="push_constants", type="function", version=PowerBuilderVersion(10, 5, True), instructions=[
                create_instruction(0, 0x40, "PUSH_CONST_INT", [42]), create_instruction(2, 0x41, "PUSH_CONST_STRING", [0]), create_instruction(4, 0x42, "PUSH_CONST_BOOL", [1]), create_instruction(6, 0x43, "PUSH_CONST_DOUBLE", [3.14159]), create_instruction(8, 0x44, "PUSH_CONST_DATE", ["2025-06-17"]), create_instruction(10, 0x45, "PUSH_CONST_ENUM", [3]), # AlignLeft!
                create_instruction(12, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        lines = result  # Already a list of lines

        # Check for proper constant formatting
        assert any("li_value = 42" in line for line in lines)
        assert any("ls_value = " in line for line in lines)
        assert any("lb_value = TRUE" in line for line in lines)
        assert any("ld_value = 3.14159" in line for line in lines)
        assert any('Date("2025-06-17")' in line for line in lines)
        assert any("AlignLeft!" in line for line in lines)

    def test_format_special_opcodes_database(self):




        """Test formatting database operation opcodes."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="database_operations", type="function", version=PowerBuilderVersion(10, 5, True), instructions=[
                create_instruction(0, 0x50, "DBSELECT"), create_instruction(2, 0x51, "DBFETCH"), create_instruction(4, 0x52, "DBINSERT"), create_instruction(6, 0x53, "DBUPDATE"), create_instruction(8, 0x54, "DBDELETE"), create_instruction(10, 0x55, "DBOPEN"), create_instruction(12, 0x56, "DBCLOSE"), create_instruction(14, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        lines = result  # Already a list of lines

        # Check for proper SQL formatting
        assert any("SELECT * FROM table USING SQLCA" in line for line in lines)
        assert any("FETCH cursor INTO :variable;" in line for line in lines)
        assert any("INSERT INTO table VALUES (...) USING SQLCA;" in line for line in lines)
        assert any("UPDATE table SET column = value WHERE condition USING SQLCA;" in line for line in lines)
        assert any("DELETE FROM table WHERE condition USING SQLCA;" in line for line in lines)
        assert any("OPEN cursor;" in line for line in lines)
        assert any("CLOSE cursor;" in line for line in lines)

    def test_format_special_opcodes_variables(self):




        """Test formatting variable reference opcodes."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="variable_references",
            type="function",
            version=PowerBuilderVersion(10, 5, True),
            instructions=[
                create_instruction(0, 0x60, "PUSH_LOCAL_VAR", [0]),  # al_arg1
                create_instruction(2, 0x61, "PUSH_GLOBAL_VAR", [0]),  # SQLCA
                create_instruction(4, 0x62, "PUSH_SHARED_VAR", [100]),
                create_instruction(6, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        lines = result  # Already a list of lines

        # Check for variable references in comments
        assert any("al_arg1" in line for line in lines)
        assert any("SQLCA" in line for line in lines)
        assert any("shared_var_100" in line for line in lines)

    def test_format_with_control_flow(self):




        """Test formatting with control flow detection."""
        formatter = SimpleFormatter()

        # Simulate a function with conditional logic
        decoded_obj = DecodedObject(
            name="check_value",
            type="function",
            version=PowerBuilderVersion(10, 5, True),
            instructions=[
                create_instruction(0, 0x60, "PUSH_LOCAL_VAR", [0]),  # Push argument
                create_instruction(2, 0x01, "PUSH_CONST_INT", [0]),  # Push 0
                create_instruction(4, 0x70, "COMPARE_EQ"),  # Compare
                create_instruction(6, 0x20, "JUMPFALSE", [6]),  # Jump if false
                create_instruction(8, 0x01, "PUSH_CONST_INT", [1]),  # Return 1
                create_instruction(10, 0x99, "RETURN", [0]),
                create_instruction(12, 0x01, "PUSH_CONST_INT", [0]),  # Return 0
                create_instruction(14, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        result_text = "\n".join(result)

        # Should have detected special operations
        assert "Special operations detected" in result_text
        assert "L_" in result_text  # Should have labels

    def test_format_empty_function(self):




        """Test formatting an empty function."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="empty_function",
            type="function",
            version=PowerBuilderVersion(10, 5, True),
            instructions=[],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        result_text = "\n".join(result)

        # Should still generate valid function structure
        assert "global function integer empty_function()" in result_text
        assert "return 0" in result_text
        assert "end function" in result_text

    def test_format_with_all_numeric_types(self):




        """Test formatting all numeric constant types."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="numeric_constants",
            type="function", 
            version=PowerBuilderVersion(10, 5, True),
            instructions=[
                create_instruction(0, 0x40, "PUSH_CONST_INT", [42]),
                create_instruction(2, 0x41, "PUSH_CONST_UINT", [42]),
                create_instruction(4, 0x42, "PUSH_CONST_LONG", [999999]),
                create_instruction(6, 0x43, "PUSH_CONST_ULONG", [999999]),
                create_instruction(8, 0x44, "PUSH_CONST_DEC", [123.45]),
                create_instruction(10, 0x45, "PUSH_CONST_FLOAT", [3.14]),
                create_instruction(12, 0x46, "PUSH_CONST_DOUBLE", [2.71828]),
                create_instruction(14, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        lines = result  # Already a list of lines

        # Check for proper numeric formatting
        assert any("li_value = 42" in line for line in lines)
        assert any("lui_value = 42" in line for line in lines)
        assert any("ll_value = 999999" in line for line in lines)
        assert any("lul_value = 999999" in line for line in lines)
        assert any("ld_value = 123.45" in line for line in lines)
        assert any("lf_value = 3.14" in line for line in lines)
        assert any("ld_value = 2.71828" in line for line in lines)


class TestFormatterDebug:
    """Debug tests for formatter output inspection."""

    def test_debug_function_calls(self):
        """Debug test to inspect function call formatting."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="call_functions",
            type="function",
            version=PowerBuilderVersion(10, 5, True),
            instructions=[
                create_instruction(0, 0x30, "GLOBFUNCCALL", [100]),
                create_instruction(2, 0x31, "CALL_FUNCTION", [200]),
                create_instruction(4, 0x32, "DLLFUNCCALL", [0]),  # MessageBoxA
                create_instruction(14, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        result_text = "\n".join(result)
        
        # Verify function calls are properly formatted
        assert "gf_function_100()" in result_text
        assert "lf_function_200()" in result_text
        assert "MessageBoxA()" in result_text

    def test_debug_database(self):
        """Debug test to inspect database operation formatting."""
        formatter = SimpleFormatter()

        decoded_obj = DecodedObject(
            name="database_operations",
            type="function",
            version=PowerBuilderVersion(10, 5, True),
            instructions=[
                create_instruction(0, 0x50, "DBSELECT"),
                create_instruction(2, 0x51, "DBFETCH"),
                create_instruction(14, 0x99, "RETURN", [0]),
            ],
        )

        result = formatter.format_object(decoded_obj, "test.fun")
        result_text = "\n".join(result)
        
        # Verify database operations are properly formatted
        assert "SELECT * FROM table USING SQLCA" in result_text
        assert "FETCH cursor INTO :variable;" in result_text
        assert "// Database operations detected" in result_text
