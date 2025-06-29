"""Tests for advanced expression reconstruction."""

import pytest

from model.expressions.reconstructor import (
    AdvancedExpressionReconstructor,
    StackValue,
)
from model.expressions.reconstructor import ExpressionType
from decompile.core.pcode_decoder import PCodeInstruction
from decompile.core.special_opcode_formatter import SpecialOpcodeFormatter
from decompile.types import BlockType, ControlBlock


class TestAdvancedExpressionReconstructor:
    """Test cases for AdvancedExpressionReconstructor."""

    def create_instruction(
        self, opcode: str, operands: list = None, address: int = 0,
    ) -> PCodeInstruction:




        """Helper to create test instructions."""
        operand_values = operands or []
        text_format = f"{opcode} {' '.join(map(str, operand_values))}"

        return PCodeInstruction(
            address=address,
            opcode=b"",
            opcode_name=opcode,
            operands=b"",
            operand_values=operand_values,
            text_format=text_format,
        )

    def test_initialization(self):




        """Test reconstructor initialization."""
        reconstructor = AdvancedExpressionReconstructor()

        assert reconstructor.optimize_expressions is True
        assert reconstructor.fold_constants is True
        assert reconstructor.simplify_boolean is True
        assert len(reconstructor.patterns) > 0
        assert reconstructor.lambda_depth == 0
        assert len(reconstructor.method_chain_buffer) == 0

    def test_pattern_registration(self):




        """Test that patterns are properly registered."""
        reconstructor = AdvancedExpressionReconstructor()

        pattern_names = [p.name for p in reconstructor.patterns]
        assert "ternary" in pattern_names
        assert "compound_assign" in pattern_names
        assert "increment" in pattern_names
        assert "method_chain" in pattern_names
        assert "null_coalesce" in pattern_names

    def test_ternary_expression_reconstruction(self):




        """Test ternary operator pattern recognition."""
        reconstructor = AdvancedExpressionReconstructor()

        # Set up stack with condition and values
        reconstructor.stack = [
            StackValue("x > 0", "boolean"),
            StackValue("positive", "string"),
            StackValue("negative", "string"),
        ]

        # Create ternary pattern instructions
        instructions = [
            self.create_instruction("JUMPTRUE", [10]),
            self.create_instruction("JUMP", [20]),
        ]

        # Match pattern
        match = reconstructor._match_pattern(instructions)
        assert match is not None
        pattern, count = match
        assert pattern.name == "ternary"
        assert count == 2

        # Apply pattern
        result = reconstructor._apply_pattern(pattern, instructions[:count])
        assert result is not None
        # The result should be a ternary expression

    def test_method_chaining_reconstruction(self):




        """Test method chaining pattern recognition."""
        reconstructor = AdvancedExpressionReconstructor()
        reconstructor.fields = {10: "trim", 20: "upper", 30: "substring"}

        # Set up stack with base object
        reconstructor.stack = [StackValue("name", "string")]

        # Create method chain instructions
        instructions = [
            self.create_instruction("DOT", [10]),
            self.create_instruction("CALL_FUNC"),
            self.create_instruction("DOT", [20]),
            self.create_instruction("CALL_FUNC"),
        ]

        # Match pattern
        match = reconstructor._match_pattern(instructions)
        assert match is not None
        pattern, count = match
        assert pattern.name == "method_chain"

        # Apply pattern
        result = reconstructor._apply_pattern(pattern, instructions[:count])
        assert result is not None
        assert "trim" in result
        assert "upper" in result

    def test_increment_decrement_pattern(self):




        """Test increment/decrement pattern recognition."""
        reconstructor = AdvancedExpressionReconstructor()
        reconstructor.locals = {1: "counter"}

        # Set up stack to meet min_stack_depth requirement
        reconstructor.stack.append(StackValue(ExpressionType.VARIABLE, "counter"))

        # Test increment
        instructions = [
            self.create_instruction("PUSH_LOCAL_VAR", [1]),
            self.create_instruction("PUSH_CONST_INT", [1]),
            self.create_instruction("ADD"),
            self.create_instruction("ASSIGN", [1]),
        ]

        match = reconstructor._match_pattern(instructions)
        assert match is not None
        pattern, count = match
        assert pattern.name == "increment"

    def test_constant_folding(self):




        """Test constant folding optimization."""
        reconstructor = AdvancedExpressionReconstructor()

        test_cases = [
            ("1 + 1", "2"),
            ("2 * 2", "4"),
            ("10 / 2", "5"),
            ("true AND true", "true"),
            ("false OR false", "false"),
            ("NOT false", "true"),
            ("NOT true", "false"),
        ]

        for input_stmt, expected in test_cases:
            result = reconstructor._fold_constants_in_statement(input_stmt)
            assert expected in result

    def test_boolean_simplification(self):




        """Test boolean expression simplification."""
        reconstructor = AdvancedExpressionReconstructor()

        test_cases = [
            ("NOT NOT x", "x"),
            ("flag = true", "flag"),
            ("flag = false", "NOT flag"),
            ("x OR true", "true"),
            ("x AND false", "false"),
        ]

        for input_stmt, expected in test_cases:
            result = reconstructor._simplify_boolean_in_statement(input_stmt)
            assert result == expected

    def test_redundant_statement_detection(self):




        """Test detection of redundant statements."""
        reconstructor = AdvancedExpressionReconstructor()

        assert reconstructor._is_redundant_statement("") is True
        assert reconstructor._is_redundant_statement("// comment") is True
        assert reconstructor._is_redundant_statement("x = x") is True
        assert reconstructor._is_redundant_statement("x = y") is False
        assert reconstructor._is_redundant_statement("x = x + 1") is False

    def test_type_inference(self):




        """Test type inference from statements."""
        reconstructor = AdvancedExpressionReconstructor()

        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0,
            end_addr=100,
            statements=[
                "x = Integer(value)",
                "name = String(data)",
                "price = Double(amount)",
                "pi = 3.14",
            ],
        )

        inferred = reconstructor.infer_types(block)

        assert inferred.get("x") == "integer"
        assert inferred.get("name") == "string"
        assert inferred.get("price") == "double"
        assert inferred.get("pi") == "double"

    def test_full_block_emulation_with_patterns(self):




        """Test full block emulation with pattern recognition."""
        reconstructor = AdvancedExpressionReconstructor()
        reconstructor.locals = {1: "x", 2: "y", 3: "result"}

        block = ControlBlock(type=BlockType.BASIC, start_addr=0, end_addr=100)

        block.instructions = [
            # Basic assignment
            self.create_instruction("PUSH_CONST_INT", [10]),
            self.create_instruction("STORE", [1]),

            # Expression with operators
            self.create_instruction("PUSH_LOCAL_VAR", [1]),
            self.create_instruction("PUSH_CONST_INT", [5]),
            self.create_instruction("ADD"),
            self.create_instruction("STORE", [2]),

            # Comparison
            self.create_instruction("PUSH_LOCAL_VAR", [1]),
            self.create_instruction("PUSH_LOCAL_VAR", [2]),
            self.create_instruction("GT"),
            self.create_instruction("STORE", [3]),
        ]

        reconstructor.emulate_block(block)

        assert len(block.statements) > 0
        assert any("x" in stmt for stmt in block.statements)
        assert any("y" in stmt for stmt in block.statements)

    def test_null_coalescing_pattern(self):




        """Test null coalescing pattern recognition."""
        reconstructor = AdvancedExpressionReconstructor()

        # Set up stack for null coalescing
        reconstructor.stack = [
            StackValue("value", "any"),
            StackValue("default_value", "string"),
        ]

        instructions = [
            self.create_instruction("PUSH_NULL"),
            self.create_instruction("EQ"),
            self.create_instruction("JUMPFALSE", [10]),
        ]

        match = reconstructor._match_pattern(instructions)
        assert match is not None
        pattern, count = match
        assert pattern.name == "null_coalesce"


class TestSpecialOpcodeFormatter:
    """Test cases for SpecialOpcodeFormatter."""

    def test_database_operations(self):




        """Test database operation formatting."""
        formatter = SpecialOpcodeFormatter()
        formatter.strings = {10: "users", 20: "SELECT * FROM users WHERE id = ?"}

        # Test SELECT
        result = formatter.format_opcode("DBSELECT", [4, 1, 20], [])
        assert "SELECT" in result
        assert "4 columns" in result

        # Test COMMIT
        result = formatter.format_opcode("DBCOMMIT", [], [])
        assert result == "COMMIT"

        # Test ROLLBACK
        result = formatter.format_opcode("DBROLLBACK", [], [])
        assert result == "ROLLBACK"

    def test_system_function_calls(self):




        """Test system function call formatting."""
        formatter = SpecialOpcodeFormatter()

        # Test MessageBox
        result = formatter.format_opcode(
            "SYSFUNCCALL", [0], ["Title", "Message"],
        )
        assert "MessageBox" in result
        assert "Title" in result
        assert "Message" in result

        # Test IsNull
        result = formatter.format_opcode("SYSFUNCCALL", [1], ["value"])
        assert "IsNull" in result
        assert "value" in result

    def test_control_flow_formatting(self):




        """Test control flow operation formatting."""
        formatter = SpecialOpcodeFormatter()

        # Test JUMP
        result = formatter.format_opcode("JUMP", [0x1234], [])
        assert "goto" in result
        assert "1234" in result

        # Test conditional jumps
        result = formatter.format_opcode("JUMPTRUE", [0x5678], [])
        assert "if" in result
        assert "goto" in result

    def test_array_operations(self):




        """Test array operation formatting."""
        formatter = SpecialOpcodeFormatter()

        # Test array creation
        result = formatter.format_opcode("ARRAYLIST", [10], [])
        assert "array" in result
        assert "10" in result

        # Test bounds checking
        result = formatter.format_opcode("LOWERBOUND", [], [])
        assert "LowerBound" in result

        result = formatter.format_opcode("UPPERBOUND", [], [])
        assert "UpperBound" in result

    def test_event_calls(self):




        """Test event call formatting."""
        formatter = SpecialOpcodeFormatter()
        formatter.functions = {100: "clicked", 101: "doubleclicked"}

        result = formatter.format_opcode("EVENTCALL", [100, 1], [])
        assert "TriggerEvent" in result
        assert "clicked" in result

    def test_exception_handling(self):




        """Test exception handling formatting."""
        formatter = SpecialOpcodeFormatter()

        # Test TRY
        result = formatter.format_opcode("PUSH_TRY", [], [])
        assert result == "TRY"

        # Test CATCH
        result = formatter.format_opcode("CATCH_EXCEPTION", [1], [])
        assert "CATCH" in result
        assert "Exception" in result

        # Test THROW
        result = formatter.format_opcode("THROW_EXCEPTION", [], [])
        assert result == "THROW"

    def test_type_operations(self):




        """Test type operation formatting."""
        formatter = SpecialOpcodeFormatter()

        # Test TypeOf
        result = formatter.format_opcode("TYPEOF", [], ["myObject"])
        assert "TypeOf" in result
        assert "myObject" in result

        # Test InstanceOf
        result = formatter.format_opcode(
            "INSTANCEOF", [], ["obj", "MyClass"],
        )
        assert "INSTANCEOF" in result

    def test_string_operations(self):




        """Test advanced string operation formatting."""
        formatter = SpecialOpcodeFormatter()

        # Test Match
        result = formatter.format_opcode(
            "MATCH", [], ["text", "pattern"],
        )
        assert "Match" in result
        assert "text" in result
        assert "pattern" in result

        # Test Split
        result = formatter.format_opcode(
            "SPLIT", [], ["string", ","],
        )
        assert "Split" in result
        assert "string" in result

    def test_halt_formatting(self):




        """Test HALT statement formatting."""
        formatter = SpecialOpcodeFormatter()

        # Test HALT
        result = formatter.format_opcode("HALT", [], [])
        assert result == "HALT"

        # Test HALT CLOSE
        result = formatter.format_opcode("HALT", [1], [])
        assert result == "HALT CLOSE"

    def test_object_lifecycle(self):




        """Test object creation/destruction formatting."""
        formatter = SpecialOpcodeFormatter()
        formatter.strings = {10: "MyClass"}

        # Test CREATE
        result = formatter.format_opcode("CREATE_EXT_OBJ", [10], [])
        assert "CREATE" in result
        assert "MyClass" in result

        # Test DESTROY
        result = formatter.format_opcode("DESTROY", [], ["myObject"])
        assert "DESTROY" in result
        assert "myObject" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
