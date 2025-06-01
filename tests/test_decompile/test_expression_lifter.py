"""Unit tests for expression lifter."""

import pytest
from decompile.expression_lifter import ExpressionLifter, Expression, ExpressionType
from decompile.pcode_decoder_v2 import PCodeInstruction


def create_instruction(address, opcode, opcode_name, operands=None, operand_values=None):
    """Helper to create PCodeInstruction with proper text format."""
    if operands is None:
        operands = []
    if operand_values is None:
        operand_values = []
    
    # Create text format
    text_format = f"{address:04X}: {opcode_name}"
    if operand_values:
        text_format += f" {', '.join(str(v) for v in operand_values)}"
    
    return PCodeInstruction(
        address=address,
        opcode=opcode,
        opcode_name=opcode_name,
        operands=operands,
        operand_values=operand_values,
        text_format=text_format
    )


class TestExpressionLifter:
    """Test expression lifting functionality."""
    
    @pytest.fixture
    def lifter(self):
        """Create a fresh expression lifter instance."""
        return ExpressionLifter()
    
    def test_push_const_int(self, lifter):
        """Test pushing integer constants."""
        inst = create_instruction(
            address=0x100,
            opcode=b'\x32',
            opcode_name='PUSH_CONST_INT',
            operands=[b'\x2A\x00'],
            operand_values=[42]
        )
        
        lifter.lift_instruction(inst)
        assert len(lifter.stack) == 1
        assert lifter.stack[0].type == ExpressionType.LITERAL
        assert lifter.stack[0].value == 42
        assert lifter.stack[0].data_type == "integer"
    
    def test_push_const_string(self, lifter):
        """Test pushing string constants."""
        lifter.strings[10] = '"Hello World"'
        inst = create_instruction(
            address=0x100,
            opcode=b'\x33',
            opcode_name='PUSH_CONST_STRING',
            operands=[b'\x0A\x00'],
            operand_values=[10]
        )
        
        lifter.lift_instruction(inst)
        assert len(lifter.stack) == 1
        assert lifter.stack[0].value == '"Hello World"'
        assert lifter.stack[0].data_type == "string"
    
    def test_binary_operation_add(self, lifter):
        """Test binary addition operation."""
        # Push two values
        lifter.stack.append(Expression(ExpressionType.LITERAL, 10, "integer"))
        lifter.stack.append(Expression(ExpressionType.LITERAL, 20, "integer"))
        
        # ADD operation
        inst = create_instruction(
            address=0x100,
            opcode=b'\x60',
            opcode_name='ADD_INT',
            operands=[],
            operand_values=[]
        )
        
        lifter.lift_instruction(inst)
        assert len(lifter.stack) == 1
        result = lifter.stack[0]
        assert result.type == ExpressionType.BINARY_OP
        assert result.value == "+"
        assert len(result.children) == 2
        assert result.to_string() == "10 + 20"
    
    def test_unary_operation_negate(self, lifter):
        """Test unary negation."""
        lifter.stack.append(Expression(ExpressionType.LITERAL, 42, "integer"))
        
        inst = create_instruction(
            address=0x100,
            opcode=b'\x70',
            opcode_name='NEG_INT',
            operands=[],
            operand_values=[]
        )
        
        lifter.lift_instruction(inst)
        assert len(lifter.stack) == 1
        result = lifter.stack[0]
        assert result.type == ExpressionType.UNARY_OP
        assert result.value == "-"
        assert result.to_string() == "-42"
    
    def test_increment_operation(self, lifter):
        """Test increment operation on variable."""
        lifter.stack.append(Expression(ExpressionType.VARIABLE, "counter", "integer"))
        
        inst = create_instruction(
            address=0x100,
            opcode=b'\x71',
            opcode_name='INCR_INT',
            operands=[],
            operand_values=[]
        )
        
        lifter.lift_instruction(inst)
        assert len(lifter.stack) == 1
        result = lifter.stack[0]
        assert result.type == ExpressionType.UNARY_OP
        assert result.value == "++"
        assert result.to_string() == "++(counter)"
    
    def test_function_call(self, lifter):
        """Test function call handling."""
        lifter.methods[0x0B] = "getUserName"
        
        # Push arguments
        lifter.stack.append(Expression(ExpressionType.LITERAL, 123, "integer"))
        
        inst = create_instruction(
            address=0x100,
            opcode=b'\x29',
            opcode_name='GLOBFUNCCALL',
            operands=[b'\x0B\x00', b'\x01\x00'],
            operand_values=[0x0B, 1]  # function index, arg count
        )
        
        result = lifter.lift_instruction(inst)
        assert result is None  # Function calls push to stack
        assert len(lifter.stack) == 1
        call_expr = lifter.stack[0]
        assert call_expr.type == ExpressionType.CALL
        assert call_expr.value == "getUserName"
        assert len(call_expr.children) == 1
        assert call_expr.to_string() == "getUserName(123)"
    
    def test_store_local_var(self, lifter):
        """Test storing to local variable."""
        lifter.locals[5] = "total"
        lifter.stack.append(Expression(ExpressionType.LITERAL, 100, "integer"))
        
        inst = create_instruction(
            address=0x100,
            opcode=b'\x40',
            opcode_name='STORE_LOCAL_VAR',
            operands=[b'\x05\x00'],
            operand_values=[5]
        )
        
        result = lifter.lift_instruction(inst)
        assert result == "total = 100"
        assert len(lifter.stack) == 0
    
    def test_return_with_value(self, lifter):
        """Test return statement with value."""
        lifter.stack.append(Expression(ExpressionType.LITERAL, "true", "boolean"))
        
        inst = create_instruction(
            address=0x100,
            opcode=b'\x00',
            opcode_name='RETURN',
            operands=[],
            operand_values=[]
        )
        
        result = lifter.lift_instruction(inst)
        assert result == "return true"
        assert len(lifter.stack) == 0
    
    def test_return_without_value(self, lifter):
        """Test return statement without value."""
        inst = create_instruction(
            address=0x100,
            opcode=b'\x00',
            opcode_name='RETURN',
            operands=[],
            operand_values=[]
        )
        
        result = lifter.lift_instruction(inst)
        assert result == "return"
    
    def test_database_operation(self, lifter):
        """Test database operation handling."""
        inst = create_instruction(
            address=0x100,
            opcode=b'\x05',
            opcode_name='DBFETCH',
            operands=[],
            operand_values=[]
        )
        
        result = lifter.lift_instruction(inst)
        assert result == "FETCH cursor INTO variables"
    
    def test_type_conversion(self, lifter):
        """Test type conversion handling."""
        lifter.stack.append(Expression(ExpressionType.LITERAL, 42, "integer"))
        
        inst = create_instruction(
            address=0x100,
            opcode=b'\x40',
            opcode_name='CNV_INT_TO_STRING',
            operands=[],
            operand_values=[]
        )
        
        lifter.lift_instruction(inst)
        assert len(lifter.stack) == 1
        result = lifter.stack[0]
        assert result.type == ExpressionType.CAST
        assert result.value == "string"
        assert result.to_string() == "string(42)"
    
    def test_field_access(self, lifter):
        """Test field access operation."""
        lifter.fields[10] = "name"
        lifter.stack.append(Expression(ExpressionType.VARIABLE, "customer", "object"))
        
        inst = create_instruction(
            address=0x100,
            opcode=b'\x2E',
            opcode_name='DOT',
            operands=[b'\x0A\x00'],
            operand_values=[10]
        )
        
        lifter.lift_instruction(inst)
        assert len(lifter.stack) == 1
        result = lifter.stack[0]
        assert result.type == ExpressionType.FIELD_ACCESS
        assert result.value == "name"
        assert result.to_string() == "customer.name"
    
    def test_array_access(self, lifter):
        """Test array indexing."""
        lifter.stack.append(Expression(ExpressionType.VARIABLE, "items", "array"))
        lifter.stack.append(Expression(ExpressionType.LITERAL, 5, "integer"))
        
        lifter._handle_index()
        
        assert len(lifter.stack) == 1
        result = lifter.stack[0]
        assert result.type == ExpressionType.ARRAY_ACCESS
        assert result.to_string() == "items[5]"
    
    def test_expression_precedence(self):
        """Test operator precedence in expressions."""
        # Create expression: 2 + 3 * 4
        two = Expression(ExpressionType.LITERAL, 2, "integer")
        three = Expression(ExpressionType.LITERAL, 3, "integer")
        four = Expression(ExpressionType.LITERAL, 4, "integer")
        
        # 3 * 4
        mul_expr = Expression(
            ExpressionType.BINARY_OP, "*", "integer",
            children=[three, four]
        )
        
        # 2 + (3 * 4)
        add_expr = Expression(
            ExpressionType.BINARY_OP, "+", "integer",
            children=[two, mul_expr]
        )
        
        assert add_expr.to_string() == "2 + 3 * 4"
        
        # Now test with reversed precedence: (2 + 3) * 4
        add_first = Expression(
            ExpressionType.BINARY_OP, "+", "integer",
            children=[two, three]
        )
        mul_after = Expression(
            ExpressionType.BINARY_OP, "*", "integer",
            children=[add_first, four]
        )
        
        assert mul_after.to_string() == "(2 + 3) * 4"
    
    def test_lift_instruction_sequence(self, lifter):
        """Test lifting a sequence of instructions."""
        instructions = [
            create_instruction(0x100, b'\x32', 'PUSH_CONST_INT', [b'\x0A\x00'], [10]),
            create_instruction(0x102, b'\x32', 'PUSH_CONST_INT', [b'\x14\x00'], [20]),
            create_instruction(0x104, b'\x60', 'ADD_INT', [], []),
        ]
        
        results = lifter.lift_instruction_sequence(instructions)
        
        # Should have one orphan expression (the result)
        assert len(results) == 1
        assert "10 + 20" in results[0]