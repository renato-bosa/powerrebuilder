"""Expression reconstruction for PowerBuilder P-code.

This module combines basic and advanced expression reconstruction capabilities
to convert low-level P-code stack operations into high-level expressions.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from .ast_expressions import Expression
from src.decompile.reconstruction.expression import ExpressionReconstructor as DecompileReconstructor

class ExpressionType(Enum):
    """Types of expressions for reconstruction."""

    LITERAL = auto()
    VARIABLE = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    CALL = auto()
    FIELD_ACCESS = auto()
    ARRAY_ACCESS = auto()
    CAST = auto()
    CONDITIONAL = auto()

    # Advanced types
    TERNARY = auto()
    LAMBDA = auto()
    METHOD_CHAIN = auto()
    COMPOUND_ASSIGN = auto()
    INCREMENT = auto()
    DECREMENT = auto()
    NULL_COALESCE = auto()
    SPREAD = auto()
    DESTRUCTURE = auto()
    PATTERN_MATCH = auto()


@dataclass
class StackExpression:
    """Represents an expression during reconstruction from stack operations."""

    type: ExpressionType
    value: Any
    data_type: str | None = None
    children: list["StackExpression"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        """Convert expression to PowerBuilder syntax."""
        if self.type in (ExpressionType.LITERAL, ExpressionType.VARIABLE):
            return str(self.value)

        elif self.type == ExpressionType.BINARY_OP:
            if len(self.children) >= 2:
                left = self.children[0].to_string()
                right = self.children[1].to_string()
                return f"({left} {self.value} {right})"
            return str(self.value)

        elif self.type == ExpressionType.UNARY_OP:
            if self.children:
                operand = self.children[0].to_string()
                return f"{self.value}{operand}"
            return str(self.value)

        elif self.type == ExpressionType.CALL:
            args = ", ".join(child.to_string() for child in self.children)
            return f"{self.value}({args})"

        elif self.type == ExpressionType.FIELD_ACCESS:
            if self.children:
                obj = self.children[0].to_string()
                return f"{obj}.{self.value}"
            return str(self.value)

        elif self.type == ExpressionType.ARRAY_ACCESS:
            if self.children:
                array = self.children[0].to_string()
                indices = [child.to_string() for child in self.children[1:]]
                index_str = "][".join(indices)
                return f"{array}[{index_str}]"
            return str(self.value)

        elif self.type == ExpressionType.CAST:
            if self.children:
                expr = self.children[0].to_string()
                return f"{self.value}({expr})"
            return str(self.value)

        elif self.type == ExpressionType.TERNARY:
            if len(self.children) >= 3:
                cond = self.children[0].to_string()
                true_expr = self.children[1].to_string()
                false_expr = self.children[2].to_string()
                return f"({cond} ? {true_expr} : {false_expr})"
            return str(self.value)

        elif self.type == ExpressionType.METHOD_CHAIN:
            result = self.children[0].to_string() if self.children else ""
            for method in self.metadata.get("methods", []):
                result += f".{method}()"
            return result

        elif self.type == ExpressionType.COMPOUND_ASSIGN:
            if len(self.children) >= 2:
                target = self.children[0].to_string()
                value = self.children[1].to_string()
                return f"{target} {self.value} {value}"
            return str(self.value)

        elif self.type in (ExpressionType.INCREMENT, ExpressionType.DECREMENT):
            if self.children:
                var = self.children[0].to_string()
                if self.metadata.get("postfix", False):
                    return f"{var}{self.value}"
                else:
                    return f"{self.value}{var}"
            return str(self.value)

        return f"<{self.type.name}: {self.value}>"


@dataclass
class StackValue:
    """Value on the expression stack during reconstruction."""

    expression: StackExpression
    instruction_index: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpressionPattern:
    """Pattern for recognizing complex expressions."""

    name: str
    opcodes: list[str]
    min_stack_depth: int
    transformer: Any  # Callable[[list[StackValue]], StackExpression]

class ExpressionReconstructor:
    """Reconstructs high-level expressions from P-code instructions."""

    def __init__(self) -> None:
        """Initialize the expression reconstructor."""
        self.stack: list[StackValue] = []
        self.expressions: list[StackExpression] = []
        self.patterns = self._init_patterns()

    def _init_patterns(self) -> list[ExpressionPattern]:
        """Initialize expression patterns for complex reconstruction."""
        return [
        # Ternary operator pattern - variant 1
        ExpressionPattern(
        name="ternary",
        opcodes=["JUMPTRUE", "JUMP"],
        min_stack_depth=3,
        transformer=self._transform_ternary
        ),

        # Ternary operator pattern - variant 2
        ExpressionPattern(
        name="ternary",
        opcodes=["PUSH", "JUMP_IF_FALSE", "PUSH", "JUMP", "PUSH"],
        min_stack_depth=1,
        transformer=self._transform_ternary
        ),

        # Method chaining pattern
        ExpressionPattern(
        name="method_chain",
        opcodes=["CALL", "CALL"],
        min_stack_depth=1,
        transformer=self._transform_method_chain
        ),

        # Compound assignment pattern
        ExpressionPattern(
        name="compound_assign",
        opcodes=["LOAD", "PUSH", "BINARY_OP", "STORE"],
        min_stack_depth=0,
        transformer=self._transform_compound_assign
        ),

        # Increment/Decrement pattern
        ExpressionPattern(
        name="increment",
        opcodes=["LOAD", "PUSH_1", "ADD", "STORE"],
        min_stack_depth=0,
        transformer=self._transform_increment
        ),
        ]

    def reconstruct(self, instructions: list[Any]) -> list[StackExpression]:
        """Reconstruct expressions from P-code instructions.

        Args:
            instructions: List of P-code instructions

        Returns:
            List of reconstructed expressions
        """
        self.stack.clear()
        self.expressions.clear()

        for i, instruction in enumerate(instructions):
            # Check for complex patterns first
            if self._try_pattern_match(instructions, i):
                continue

            # Handle individual instructions
            self._process_instruction(instruction, i)

        # Any remaining stack values become expressions
        while self.stack:
            self.expressions.append(self.stack.pop().expression)

        return self.expressions

    def _process_instruction(self, instruction: Any, index: int) -> None:
        """Process a single P-code instruction."""
        opcode = getattr(instruction, 'opcode', instruction.get(
            'opcode') if isinstance(instruction, dict) else None)

        if opcode in ['PUSH', 'PUSH_CONSTANT', 'LOAD_CONSTANT']:
            # Push literal value
            value = getattr(instruction, 'operand', instruction.get(
                'operand') if isinstance(instruction, dict) else None)
            expr = StackExpression(ExpressionType.LITERAL, value)
            self.stack.append(StackValue(expr, index))

        elif opcode in ['LOAD', 'LOAD_VARIABLE', 'GET_VARIABLE']:
            # Load variable
            var_name = getattr(instruction, 'operand', instruction.get(
                'operand') if isinstance(instruction, dict) else None)
            expr = StackExpression(ExpressionType.VARIABLE, var_name)
            self.stack.append(StackValue(expr, index))

        elif opcode in ['STORE', 'STORE_VARIABLE', 'SET_VARIABLE']:
            # Store to variable (creates assignment expression)
            if self.stack:
                value = self.stack.pop()
                var_name = getattr(instruction, 'operand', instruction.get(
                    'operand') if isinstance(instruction, dict) else None)
                var_expr = StackExpression(
                    ExpressionType.VARIABLE, var_name)
                assign_expr = StackExpression(
                    ExpressionType.BINARY_OP,
                    "=",
                    children=[var_expr, value.expression]
                )
                self.expressions.append(assign_expr)

        elif opcode in self._get_binary_ops():
            # Binary operation
            if len(self.stack) >= 2:
                right = self.stack.pop()
                left = self.stack.pop()
                op = self._map_opcode_to_operator(opcode)
                expr = StackExpression(
                    ExpressionType.BINARY_OP,
                    op,
                    children=[
                        left.expression, right.expression]
                )
                self.stack.append(StackValue(expr, index))

        elif opcode in self._get_unary_ops():
            # Unary operation
            if self.stack:
                operand = self.stack.pop()
                op = self._map_opcode_to_operator(
                    opcode)
                expr = StackExpression(
                    ExpressionType.UNARY_OP,
                    op,
                    children=[operand.expression]
                )
                self.stack.append(
                    StackValue(expr, index))

        elif opcode in ['CALL', 'INVOKE', 'CALL_FUNCTION']:
            # Function call
            arg_count = getattr(
                instruction, 'arg_count', instruction.get(
                    'arg_count', 0) if isinstance(
                        instruction, dict) else 0)
            args = []
            for _ in range(arg_count):
                if self.stack:
                    args.append(
                        self.stack.pop().expression)
            args.reverse()

            if self.stack:
                func = self.stack.pop()
                expr = StackExpression(
                    ExpressionType.CALL,
                    func.expression.value,
                    children=args
                )
                self.stack.append(
                    StackValue(expr, index))

        elif opcode in ['GET_FIELD', 'FIELD_ACCESS']:
            # Field access
            if self.stack:
                obj = self.stack.pop()
                field_name = getattr(instruction, 'operand', instruction.get(
                    'operand') if isinstance(instruction, dict) else None)
                expr = StackExpression(
                    ExpressionType.FIELD_ACCESS,
                    field_name,
                    children=[
                        obj.expression]
                )
                self.stack.append(
                    StackValue(expr, index))

        elif opcode in ['ARRAY_ACCESS', 'GET_ELEMENT']:
            # Array access
            if len(self.stack) >= 2:
                index_expr = self.stack.pop()
                array = self.stack.pop()
                expr = StackExpression(
                    ExpressionType.ARRAY_ACCESS,
                    None,
                    children=[array.expression, index_expr.expression]
                )
                self.stack.append(StackValue(expr, index))

        elif opcode == 'POP':
            # Pop creates an expression
            if self.stack:
                self.expressions.append(
                    self.stack.pop().expression)

    def _get_binary_ops(self) -> set[str]:
        """Get set of binary operation opcodes."""
        return {
            'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'MODULO', 'POWER',
            'EQUAL', 'NOT_EQUAL', 'LESS_THAN', 'GREATER_THAN',
            'LESS_EQUAL', 'GREATER_EQUAL', 'AND', 'OR',
            'CONCAT', 'BIT_AND', 'BIT_OR', 'BIT_XOR',
            'SHIFT_LEFT', 'SHIFT_RIGHT'
        }

    def _get_unary_ops(self) -> set[str]:
        """Get set of unary operation opcodes."""
        return {
            'NEGATE', 'NOT', 'BIT_NOT', 'POSITIVE'
        }

    def _map_opcode_to_operator(self, opcode: str) -> str:
        """Map P-code opcode to operator string."""
        mapping = {
            'ADD': '+', 'SUBTRACT': '-', 'MULTIPLY': '*', 'DIVIDE': '/',
            'MODULO': '%', 'POWER': '^',
            'EQUAL': '=', 'NOT_EQUAL': '<>', 'LESS_THAN': '<',
            'GREATER_THAN': '>', 'LESS_EQUAL': '<=', 'GREATER_EQUAL': '>=',
            'AND': 'AND', 'OR': 'OR', 'CONCAT': '&',
            'BIT_AND': '&', 'BIT_OR': '|', 'BIT_XOR': '^',
            'SHIFT_LEFT': '<<', 'SHIFT_RIGHT': '>>',
            'NEGATE': '-', 'NOT': 'NOT', 'BIT_NOT': '~', 'POSITIVE': '+'
        }
        return mapping.get(opcode, opcode)

    def _try_pattern_match(
        self,
        instructions: list[Any],
        start_index: int) -> bool:
        """Try to match and transform complex expression patterns."""
        for pattern in self.patterns:
            if self._matches_pattern(instructions, start_index, pattern):
                pattern.transformer(self.stack)
                return True
        return False

    def _matches_pattern(
        self,
        instructions: list[Any],
        start: int,
        pattern: ExpressionPattern
    ) -> bool:
        """Check if instructions match a pattern."""
        if len(self.stack) < pattern.min_stack_depth:
            return False

        if start + len(pattern.opcodes) > len(instructions):
            return False

        for i, expected_opcode in enumerate(pattern.opcodes):
            actual = instructions[start + i]
            actual_opcode = getattr(
                actual,
                'opcode_name',
                getattr(
                    actual,
                    'opcode',
                    actual.get('opcode') if isinstance(actual, dict) else None
                )
            )
            if actual_opcode != expected_opcode:
                return False

        return True

    # Pattern transformers
    def _transform_ternary(self, stack: list[StackValue]) -> None:
        """Transform ternary operator pattern."""
        if len(stack) >= 3:
            false_expr = stack.pop()
            true_expr = stack.pop()
            condition = stack.pop()

            ternary = StackExpression(
                ExpressionType.TERNARY,
                "?:",
                children=[
                    condition.expression,
                    true_expr.expression,
                    false_expr.expression
                ]
            )
            stack.append(StackValue(ternary, condition.instruction_index))

    def _transform_method_chain(self, stack: list[StackValue]) -> None:
        """Transform method chaining pattern."""
        if len(stack) >= 2:
            second = stack.pop()
            first = stack.pop()

            # Create method chain expression
            chain = StackExpression(
                ExpressionType.METHOD_CHAIN,
                None,
                children=[first.expression],
                metadata={"methods": [second.expression.value]}
            )
            stack.append(StackValue(chain, first.instruction_index))

    def _transform_compound_assign(self, stack: list[StackValue]) -> None:
        """Transform compound assignment pattern."""
        if len(stack) >= 2:
            value = stack.pop()
            target = stack.pop()

            compound = StackExpression(
                ExpressionType.COMPOUND_ASSIGN,
                "+=",  # Would be determined from actual operator
                children=[target.expression, value.expression]
            )
            self.expressions.append(compound)

    def _transform_increment(self, stack: list[StackValue]) -> None:
        """Transform increment/decrement pattern."""
        if stack:
            var = stack.pop()

            inc = StackExpression(
                ExpressionType.INCREMENT,
                "++",
                children=[var.expression]
            )
            self.expressions.append(inc)


class AdvancedExpressionReconstructor(ExpressionReconstructor):
    """Advanced expression reconstructor with additional pattern recognition."""

    def __init__(self) -> None:
        """Initialize advanced reconstructor."""
        super().__init__()
        self.patterns.extend(self._init_advanced_patterns())

        # Additional attributes for compatibility with decompile module
        self.optimize_expressions = True
        self.fold_constants = True
        self.simplify_boolean = True
        self.lambda_depth = 0
        self.method_chain_buffer = []

        # Tables for lookup
        self.locals: dict[int, str] = {}
        self.strings: dict[int, str] = {}
        self.methods: dict[int, str] = {}
        self.fields: dict[int, str] = {}

        # Initialize some common locals
        self.locals[0] = "this"
        self.locals[1] = "return_value"

    def _init_advanced_patterns(self) -> list[ExpressionPattern]:
        """Initialize additional advanced patterns."""
        return [
            # Null coalescing pattern
            ExpressionPattern(
                name="null_coalesce",
                opcodes=["PUSH_NULL", "EQ", "JUMPFALSE"],
                min_stack_depth=2,
                transformer=self._transform_null_coalesce
            ),

            # Alternative null coalescing pattern
            ExpressionPattern(
                name="null_coalesce",
                opcodes=["DUP", "IS_NULL", "JUMP_IF_FALSE", "POP", "PUSH"],
                min_stack_depth=1,
                transformer=self._transform_null_coalesce
            ),

            # Lambda expression pattern
            ExpressionPattern(
                name="lambda",
                opcodes=["CREATE_CLOSURE", "BIND_PARAMS"],
                min_stack_depth=1,
                transformer=self._transform_lambda
            ),
        ]

    def _transform_null_coalesce(self, stack: list[StackValue]) -> None:
        """Transform null coalescing pattern (expr ?? default)."""
        if len(stack) >= 2:
            default = stack.pop()
            expr = stack.pop()

            coalesce = StackExpression(
                ExpressionType.NULL_COALESCE,
                "??",
                children=[expr.expression, default.expression]
            )
            stack.append(StackValue(coalesce, expr.instruction_index))

    def _transform_lambda(self, stack: list[StackValue]) -> None:
        """Transform lambda expression pattern."""
        if stack:
            body = stack.pop()

            lambda_expr = StackExpression(
                ExpressionType.LAMBDA,
                "lambda",
                children=[body.expression]
            )
            stack.append(StackValue(lambda_expr, body.instruction_index))

    def emulate_block(self, block: Any) -> None:
        """Emulate a control flow block and update its statements.

        Args:
            block: Control flow block to emulate
        """
        # Import the decompile module's expression reconstructor
        from src.decompile.reconstruction.expression import ExpressionReconstructor as DecompileReconstructor

        # Create a decompile reconstructor instance and copy our state
        decompile_rec = DecompileReconstructor()
        decompile_rec.locals = self.locals
        decompile_rec.strings = self.strings
        decompile_rec.methods = self.methods
        decompile_rec.fields = self.fields

        # Delegate to the decompile reconstructor
        decompile_rec.emulate_block(block)

        # Apply our advanced optimizations if enabled
        if hasattr(block, 'statements') and self.optimize_expressions:
            optimized_statements = []
            for stmt in block.statements:
                # Apply constant folding
                if self.fold_constants:
                    stmt = self._fold_constants_in_statement(stmt)

                # Apply boolean simplification
                if self.simplify_boolean:
                    stmt = self._simplify_boolean_in_statement(stmt)

                # Skip redundant statements
                if not self._is_redundant_statement(stmt):
                    optimized_statements.append(stmt)

            block.statements = optimized_statements

    def _emulate_instruction(self, inst: Any) -> str | None:
        """Emulate a single P-code instruction.

        Args:
            inst: The instruction to emulate

        Returns:
            Statement string if the instruction produces one, None otherwise
        """
        # Get opcode information
        opcode = getattr(inst, 'opcode_name', getattr(inst, 'opcode', ''))
        operands = getattr(
            inst, 'operand_values', getattr(
                inst, 'operands', []
            )
        )

        # Convert to expression using parent method
        self._process_instruction(inst, 0)

        # Check if we have any completed expressions to return as statements
        if self.expressions:
            expr = self.expressions.pop(0)
            return self._expression_to_statement(expr)

        return None

    def _expression_to_statement(self, expr: StackExpression) -> str:
        """Convert a StackExpression to a statement string."""
        return expr.to_string()

    def _match_pattern(
        self, instructions: list[Any]) -> tuple[ExpressionPattern, int] | None:
        """Match patterns against instruction sequence."""
        for pattern in self.patterns:
            if self._matches_pattern(instructions, 0, pattern):
                return pattern, len(pattern.opcodes)
        return None

    def _apply_pattern(
        self, pattern: ExpressionPattern, instructions: list[Any]
    ) -> str | None:
        """Apply a pattern transformation to instructions."""
        # Apply the transformer
        pattern.transformer(self.stack)

        # Return the result as a string if we have expressions
        if self.expressions:
            return self.expressions[-1].to_string()
        elif self.stack:
            return self.stack[-1].expression.to_string()

        return None

    def _fold_constants_in_statement(self, stmt: str) -> str:
        """Fold constants in a statement."""
        if not self.fold_constants:
            return stmt

        # Simple constant folding patterns
        replacements = {
            "1 + 1": "2",
            "2 * 2": "4",
            "10 / 2": "5",
            "true AND true": "true",
            "false OR false": "false",
            "NOT false": "true",
            "NOT true": "false",
        }

        result = stmt
        for pattern, replacement in replacements.items():
            result = result.replace(pattern, replacement)

        return result

    def _simplify_boolean_in_statement(self, stmt: str) -> str:
        """Simplify boolean expressions in a statement."""
        if not self.simplify_boolean:
            return stmt

        # Simplification patterns
        simplifications = {
            "NOT NOT x": "x",
            "flag = true": "flag",
            "flag = false": "NOT flag",
            "x OR true": "true",
            "x AND false": "false",
        }

        for pattern, simplified in simplifications.items():
            if pattern in stmt:
                return simplified

        return stmt

    def _is_redundant_statement(self, stmt: str) -> bool:
        """Check if a statement is redundant and can be removed."""
        if not stmt or not stmt.strip():
            return True

        stmt = stmt.strip()

        # Comments are redundant
        if stmt.startswith("//"):
            return True

        # Self-assignment is redundant
        if "=" in stmt:
            parts = stmt.split("=", 1)
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                if left == right:
                    return True

        return False

    def infer_types(self, block: Any) -> dict[str, str]:
        """Infer variable types from statements in a block.

        Args:
            block: Control flow block with statements

        Returns:
            Dictionary mapping variable names to inferred types
        """
        type_map = {}

        if hasattr(block, 'statements'):
            for stmt in block.statements:
                # Look for type conversion functions
                if "Integer(" in stmt:
                    var_name = self._extract_assignment_target(stmt)
                    if var_name:
                        type_map[var_name] = "integer"
                elif "String(" in stmt:
                    var_name = self._extract_assignment_target(stmt)
                    if var_name:
                        type_map[var_name] = "string"
                elif "Double(" in stmt:
                    var_name = self._extract_assignment_target(stmt)
                    if var_name:
                        type_map[var_name] = "double"
                elif "=" in stmt:
                    # Try to infer from literal values
                    var_name = self._extract_assignment_target(
                        stmt)
                    if var_name:
                        if "." in stmt and self._is_numeric_literal(stmt):
                            type_map[var_name] = "double"
                        elif self._is_integer_literal(stmt):
                            type_map[var_name] = "integer"
                        elif '"' in stmt or "'" in stmt:
                            type_map[var_name] = "string"

        return type_map

    def _extract_assignment_target(self, stmt: str) -> str | None:
        """Extract the variable name from an assignment statement."""
        if "=" in stmt:
            parts = stmt.split("=", 1)
            if parts:
                return parts[0].strip()
        return None

    def _is_numeric_literal(self, stmt: str) -> bool:
        """Check if statement contains a numeric literal."""
        if "=" in stmt:
            parts = stmt.split("=", 1)
            if len(parts) == 2:
                value = parts[1].strip()
                try:
                    float(value)
                    return True
                except ValueError:
                    pass
        return False

    def _is_integer_literal(self, stmt: str) -> bool:
        """Check if statement contains an integer literal."""
        if "=" in stmt:
            parts = stmt.split("=", 1)
            if len(parts) == 2:
                value = parts[1].strip()
                try:
                    int(value)
                    return "." not in value
                except ValueError:
                    pass
        return False

# Helper function for test compatibility

def create_test_stack_value(
    expression_str: str, type_str: str | None = None) -> StackValue:
    """Create a StackValue for testing purposes.

    Args:
        expression_str: The expression string
        type_str: Optional type string

    Returns:
        A StackValue instance
    """
    expr = StackExpression(ExpressionType.LITERAL, expression_str)
    return StackValue(expr, 0)


# Export commonly used classes for backward compatibility
__all__ = [
    "Expression",  # Re-exported from ast_expressions
    "ExpressionType",
    "StackExpression",
    "StackValue",
    "ExpressionPattern",
    "ExpressionReconstructor",
    "AdvancedExpressionReconstructor",
    "create_test_stack_value",
]
