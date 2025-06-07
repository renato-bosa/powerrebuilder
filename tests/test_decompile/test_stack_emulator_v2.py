"""Unit tests for stack emulator - updated to match actual interface."""

import pytest
from decompile.core.expression_reconstructor import ExpressionReconstructor as StackEmulator, StackValue
from decompile.analysis.control_flow_analyzer import ControlBlock, BlockType
from decompile.core.pcode_decoder import PCodeInstruction


def create_instruction(address, opcode_name, operand_values=None):
    """Helper to create test instructions."""
    if operand_values is None:
        operand_values = []
    
    text_format = f"{address:04X}: {opcode_name}"
    if operand_values:
        text_format += f" {', '.join(str(v) for v in operand_values)}"
    
    return PCodeInstruction(
        address=address,
        opcode=b'',
        opcode_name=opcode_name,
        operands=[],
        operand_values=operand_values,
        text_format=text_format
    )


class TestStackEmulator:
    """Test stack emulation functionality."""
    
    @pytest.fixture
    def emulator(self):
        """Create a fresh stack emulator instance."""
        return StackEmulator()
    
    def test_init(self, emulator):
        """Test emulator initialization."""
        assert len(emulator.stack) == 0
        assert len(emulator.locals) >= 2  # this and return_value
        assert emulator.locals[0] == "this"
        assert emulator.locals[1] == "return_value"
    
    def test_emulate_push_const_int(self, emulator):
        """Test emulating PUSH_CONST_INT instruction."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x103,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_INT', [42])
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert emulator.stack[0].expression == "42"
    
    def test_emulate_arithmetic_add(self, emulator):
        """Test emulating arithmetic addition."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x107,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_INT', [10]),
                create_instruction(0x103, 'PUSH_CONST_INT', [20]),
                create_instruction(0x106, 'ADD')
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert emulator.stack[0].expression == "(10 + 20)"
    
    def test_emulate_store_local(self, emulator):
        """Test emulating store to local variable."""
        emulator.locals[5] = "count"
        
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x107,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_INT', [100]),
                create_instruction(0x103, 'STORE_LOCAL_VAR', [5])
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(block.statements) == 1
        assert block.statements[0] == "count = 100"
        assert len(emulator.stack) == 0
    
    def test_emulate_function_call(self, emulator):
        """Test emulating function call."""
        emulator.methods[0x10] = "calculate"
        
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x10A,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_INT', [5]),
                create_instruction(0x103, 'PUSH_CONST_INT', [10]),
                create_instruction(0x106, 'GLOBFUNCCALL', [0x10, 2])  # function_id, arg_count
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert "calculate(5, 10)" in emulator.stack[0].expression
    
    def test_emulate_comparison(self, emulator):
        """Test emulating comparison operations."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x107,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_INT', [10]),
                create_instruction(0x103, 'PUSH_CONST_INT', [20]),
                create_instruction(0x106, 'LT')  # Less than
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert emulator.stack[0].expression == "(10 < 20)"
    
    def test_emulate_string_operations(self, emulator):
        """Test emulating string operations."""
        emulator.strings[1] = '"Hello"'
        emulator.strings[2] = '" World"'
        
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x109,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_STRING', [1]),
                create_instruction(0x103, 'PUSH_CONST_STRING', [2]),
                create_instruction(0x106, 'ADD')  # String concatenation uses ADD
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert emulator.stack[0].expression == '("Hello" + " World")'
    
    def test_emulate_field_access(self, emulator):
        """Test emulating field access with DOT operation."""
        emulator.fields[10] = "name"
        
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x106,
            instructions=[
                create_instruction(0x100, 'PUSH_LOCAL_VAR', [0]),  # this
                create_instruction(0x103, 'DOT', [10])  # field index
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert emulator.stack[0].expression == "this.name"
    
    def test_emulate_array_access(self, emulator):
        """Test emulating array indexing."""
        emulator.locals[3] = "items"
        
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x109,
            instructions=[
                create_instruction(0x100, 'PUSH_LOCAL_VAR', [3]),
                create_instruction(0x103, 'PUSH_CONST_INT', [5]),
                create_instruction(0x106, 'INDEX')
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert emulator.stack[0].expression == "items[5]"
    
    def test_emulate_return_with_value(self, emulator):
        """Test emulating return statement with value."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x106,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_INT', [42]),
                create_instruction(0x103, 'RETURN')
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(block.statements) == 1
        assert block.statements[0] == "return 42"
    
    def test_emulate_return_without_value(self, emulator):
        """Test emulating return statement without value."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x103,
            instructions=[
                create_instruction(0x100, 'RETURN')
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(block.statements) == 1
        assert block.statements[0] == "return"
    
    def test_emulate_complex_expression(self, emulator):
        """Test emulating complex nested expression."""
        # (a + b) * (c - d)
        emulator.locals[2] = "a"
        emulator.locals[3] = "b"
        emulator.locals[4] = "c"
        emulator.locals[5] = "d"
        
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x115,
            instructions=[
                create_instruction(0x100, 'PUSH_LOCAL_VAR', [2]),  # a
                create_instruction(0x103, 'PUSH_LOCAL_VAR', [3]),  # b
                create_instruction(0x106, 'ADD'),                  # a + b
                create_instruction(0x107, 'PUSH_LOCAL_VAR', [4]),  # c
                create_instruction(0x10A, 'PUSH_LOCAL_VAR', [5]),  # d
                create_instruction(0x10D, 'SUB'),                  # c - d
                create_instruction(0x10E, 'MUL')                   # (a + b) * (c - d)
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert "(a + b)" in emulator.stack[0].expression
        assert "(c - d)" in emulator.stack[0].expression
        assert " * " in emulator.stack[0].expression
    
    def test_emulate_boolean_operations(self, emulator):
        """Test emulating boolean operations."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x109,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_BOOL', [1]),  # true
                create_instruction(0x103, 'PUSH_CONST_BOOL', [0]),  # false
                create_instruction(0x106, 'AND')
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert "true" in emulator.stack[0].expression
        assert "false" in emulator.stack[0].expression
        assert " and " in emulator.stack[0].expression
    
    def test_emulate_type_conversion(self, emulator):
        """Test emulating type conversion."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x106,
            instructions=[
                create_instruction(0x100, 'PUSH_CONST_INT', [42]),
                create_instruction(0x103, 'CNV_INT_TO_STRING')
            ]
        )
        
        emulator.emulate_block(block)
        
        assert len(emulator.stack) == 1
        assert "string(42)" in emulator.stack[0].expression
    
    def test_emulate_database_operations(self, emulator):
        """Test emulating database operations."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x10C,
            instructions=[
                create_instruction(0x100, 'DBSTART'),
                create_instruction(0x103, 'DBSELECT', [1]),  # SQL statement ID
                create_instruction(0x106, 'DBCOMMIT')
            ]
        )
        
        emulator.emulate_block(block)
        
        # Should generate database operation statements
        assert any("BEGIN TRANSACTION" in stmt for stmt in block.statements)
        assert any("SELECT" in stmt for stmt in block.statements)
        assert any("COMMIT" in stmt for stmt in block.statements)