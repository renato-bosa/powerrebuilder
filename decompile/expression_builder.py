"""Expression reconstruction from P-code stack operations.

This module builds expression trees from stack-based P-code instructions,
converting RPN (Reverse Polish Notation) operations into infix expressions.
"""

from dataclasses import dataclass
from enum import Enum, auto

from decompile.pcode_decoder import PCodeInstruction
from model.ast.nodes import (
    BinaryExpression,
    Expression,
    Literal,
    UnaryExpression,
    Variable,
)


class ExpressionType(Enum):
    """Types of expressions we can build."""
    LITERAL = auto()
    VARIABLE = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    FUNCTION_CALL = auto()
    ARRAY_ACCESS = auto()
    FIELD_ACCESS = auto()


@dataclass
class StackValue:
    """Value on the expression stack."""
    expression: Expression
    source_instruction: PCodeInstruction | None = None

    def __repr__(self) -> str:
        return f"StackValue({self.expression})"


class ExpressionBuilder:
    """Builds expression trees from P-code instructions."""

    # Map P-code opcodes to binary operators
    BINARY_OPS = {
        'ADD': '+',
        'SUB': '-',
        'MUL': '*',
        'DIV': '/',
        'MOD': '%',
        'CONCAT': '+',  # String concatenation
        'EQ': '=',
        'NE': '<>',
        'LT': '<',
        'LE': '<=',
        'GT': '>',
        'GE': '>=',
        'AND': 'and',
        'OR': 'or',
    }

    # Map P-code opcodes to unary operators
    UNARY_OPS = {
        'NEG': '-',
        'NOT': 'not',
    }

    def __init__(self) -> None:
        """Initialize the expression builder."""
        self.stack: list[StackValue] = []
        self.variables: dict[int, str] = {}  # Map var indices to names
        self.strings: dict[int, str] = {}  # String constants

    def reset(self) -> None:
        """Reset the expression stack."""
        self.stack.clear()

    def process_instruction(self, inst: PCodeInstruction) -> Expression | None:
        """Process a single instruction and return expression if complete.

        Args:
            inst: P-code instruction to process

        Returns:
            Complete expression if a store operation, None otherwise
        """
        opcode = inst.opcode_name

        # Handle constants
        if opcode.startswith('CONST_'):
            return self._handle_constant(inst)

        # Handle variable loads
        if opcode.startswith('LOAD_'):
            return self._handle_load(inst)

        # Handle store operations - these complete expressions
        if opcode.startswith('STORE_'):
            return self._handle_store(inst)

        # Handle arithmetic operations
        if opcode == 'ARITHMETIC_OP':
            return self._handle_arithmetic(inst)

        # Handle logical operations
        if opcode == 'LOGICAL_OP':
            return self._handle_logical(inst)

        # Handle comparisons
        if opcode == 'COMPARE':
            return self._handle_compare(inst)

        # Handle function/method calls
        if opcode in ['CALL_FUNCTION', 'CALL_METHOD']:
            return self._handle_call(inst)

        # Handle string literals
        if opcode == 'STRING':
            return self._handle_string(inst)

        return None

    def _handle_constant(self, inst: PCodeInstruction) -> None:
        """Handle constant push operations."""
        opcode = inst.opcode_name
        value = inst.operand_values[0] if inst.operand_values else 0

        # Determine literal type
        if opcode == 'CONST_BOOL_TRUE':
            literal = Literal(value='true', type='boolean')
        elif opcode == 'CONST_BOOL_FALSE':
            literal = Literal(value='false', type='boolean')
        elif opcode == 'CONST_NULL':
            literal = Literal(value='null', type='null')
        elif opcode in {'CONST_BYTE', 'CONST_INT16', 'CONST_INT32'}:
            literal = Literal(value=str(value), type='integer')
        elif opcode == 'CONST_FLOAT':
            literal = Literal(value=str(value), type='real')
        elif opcode == 'CONST_STRING_REF':
            # Look up string from string table
            string_val = self.strings.get(value, f'string_{value}')
            literal = Literal(value=f'"{string_val}"', type='string')
        else:
            # Generic constant
            literal = Literal(value=str(value), type='unknown')

        self.stack.append(StackValue(literal, inst))

    def _handle_load(self, inst: PCodeInstruction) -> None:
        """Handle variable load operations."""
        if not inst.operand_values:
            return

        var_index = inst.operand_values[0]

        # Create variable reference
        var_name = self.variables.get(var_index, f'lv_{var_index}')
        var_expr = Variable(name=var_name)

        self.stack.append(StackValue(var_expr, inst))

    def _handle_store(self, inst: PCodeInstruction) -> Expression | None:
        """Handle store operations - these complete expressions."""
        if not self.stack:
            return None

        # Pop the value to store
        value = self.stack.pop()

        # For now, return the expression that was on top of stack
        # In a full implementation, we'd create an assignment
        return value.expression

    def _handle_arithmetic(self, inst: PCodeInstruction) -> None:
        """Handle arithmetic operations."""
        if len(self.stack) < 2:
            return

        # Pop operands (right then left for correct order)
        right = self.stack.pop()
        left = self.stack.pop()

        # Determine operator from operand or context
        # For now, assume addition as default
        operator = '+'
        if inst.operand_values:
            # Map operand value to operator
            op_map = {0x80: '+', 0x81: '-', 0x82: '*', 0x83: '/'}
            operator = op_map.get(inst.operand_values[0], '+')

        # Create binary expression
        expr = BinaryExpression(
            left=left.expression,
            operator=operator,
            right=right.expression,
        )

        self.stack.append(StackValue(expr, inst))

    def _handle_logical(self, inst: PCodeInstruction) -> None:
        """Handle logical operations."""
        if len(self.stack) < 2:
            return

        # Pop operands
        right = self.stack.pop()
        left = self.stack.pop()

        # Determine operator
        operator = 'and'  # Default
        if inst.operand_values:
            op_map = {0x80: 'and', 0x88: 'or'}
            operator = op_map.get(inst.operand_values[0], 'and')

        # Create binary expression
        expr = BinaryExpression(
            left=left.expression,
            operator=operator,
            right=right.expression,
        )

        self.stack.append(StackValue(expr, inst))

    def _handle_compare(self, inst: PCodeInstruction) -> None:
        """Handle comparison operations."""
        if len(self.stack) < 2:
            return

        # Pop operands
        right = self.stack.pop()
        left = self.stack.pop()

        # Determine comparison operator
        operator = '='  # Default
        if inst.operand_values:
            op_map = {
                0x80: '=',
                0x81: '<>',
                0x82: '<',
                0x83: '<=',
                0x84: '>',
                0x85: '>=',
            }
            operator = op_map.get(inst.operand_values[0], '=')

        # Create comparison expression
        expr = BinaryExpression(
            left=left.expression,
            operator=operator,
            right=right.expression,
        )

        self.stack.append(StackValue(expr, inst))

    def _handle_call(self, inst: PCodeInstruction) -> None:
        """Handle function/method calls."""
        # For now, just create a placeholder
        # In full implementation, would pop arguments from stack
        func_name = f"function_{inst.operand_values[0] if inst.operand_values else 0}"
        var_expr = Variable(name=func_name + "()")
        self.stack.append(StackValue(var_expr, inst))

    def _handle_string(self, inst: PCodeInstruction) -> None:
        """Handle string literals."""
        if inst.operand_values:
            string_val = inst.operand_values[0]
            literal = Literal(value=f'"{string_val}"', type='string')
            self.stack.append(StackValue(literal, inst))

    def build_assignment(self, var_name: str, expression: Expression) -> str:
        """Build an assignment statement.

        Args:
            var_name: Variable name
            expression: Expression to assign

        Returns:
            PowerBuilder assignment statement
        """
        return f"{var_name} = {self.expression_to_string(expression)}"

    def expression_to_string(self, expr: Expression) -> str:
        """Convert expression tree to PowerBuilder string.

        Args:
            expr: Expression to convert

        Returns:
            PowerBuilder expression string
        """
        if isinstance(expr, Literal):
            return expr.value
        if isinstance(expr, Variable):
            return expr.name
        if isinstance(expr, BinaryExpression):
            left = self.expression_to_string(expr.left)
            right = self.expression_to_string(expr.right)
            return f"({left} {expr.operator} {right})"
        if isinstance(expr, UnaryExpression):
            operand = self.expression_to_string(expr.operand)
            return f"{expr.operator}{operand}"
        return str(expr)

    def analyze_expression_sequence(self, instructions: list[PCodeInstruction]) -> list[str]:
        """Analyze a sequence of instructions to build expressions.

        Args:
            instructions: List of P-code instructions

        Returns:
            List of PowerBuilder statements
        """
        statements = []
        self.reset()

        for inst in instructions:
            expr = self.process_instruction(inst)

            # If we completed an expression (usually on STORE)
            if expr and isinstance(inst.opcode_name, str) and inst.opcode_name.startswith('STORE_'):
                # Determine target variable
                if inst.operand_values:
                    var_idx = inst.operand_values[0]
                    var_name = self.variables.get(var_idx, f'lv_{var_idx}')
                    stmt = self.build_assignment(var_name, expr)
                    statements.append(stmt)
                    self.reset()  # Clear stack after assignment

        return statements
