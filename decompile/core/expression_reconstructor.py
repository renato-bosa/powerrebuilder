"""Expression reconstruction for PowerBuilder P-code.

This module combines stack emulation and expression lifting to reconstruct
high-level expressions from low-level P-code stack operations.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from ..analysis.control_flow_analyzer import ControlBlock
from .pcode_decoder import PCodeInstruction

logger = logging.getLogger(__name__)


class ExpressionType(Enum):
    """Types of expressions."""
    LITERAL = auto()
    VARIABLE = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    CALL = auto()
    FIELD_ACCESS = auto()
    ARRAY_ACCESS = auto()
    CAST = auto()
    CONDITIONAL = auto()


@dataclass
class Expression:
    """Represents a lifted expression."""
    type: ExpressionType
    value: Any
    data_type: str | None = None
    children: list['Expression'] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        """Convert expression to PowerBuilder syntax."""
        if self.type == ExpressionType.LITERAL or self.type == ExpressionType.VARIABLE:
            return str(self.value)

        if self.type == ExpressionType.BINARY_OP:
            if len(self.children) == 2:
                left = self.children[0].to_string()
                right = self.children[1].to_string()
                op = self.value

                # Handle precedence
                if self._needs_parentheses(self.children[0], op):
                    left = f"({left})"
                if self._needs_parentheses(self.children[1], op):
                    right = f"({right})"

                return f"{left} {op} {right}"

        if self.type == ExpressionType.UNARY_OP:
            if self.children:
                operand = self.children[0].to_string()
                if self.value == 'NOT':
                    return f"NOT {operand}"
                return f"{self.value}{operand}"

        if self.type == ExpressionType.CALL:
            args = ', '.join(c.to_string() for c in self.children)
            return f"{self.value}({args})"

        if self.type == ExpressionType.FIELD_ACCESS:
            if self.children:
                obj = self.children[0].to_string()
                return f"{obj}.{self.value}"
            return self.value

        if self.type == ExpressionType.ARRAY_ACCESS:
            if len(self.children) == 2:
                array = self.children[0].to_string()
                index = self.children[1].to_string()
                return f"{array}[{index}]"

        return str(self.value)

    def _needs_parentheses(self, child: 'Expression', parent_op: str) -> bool:
        """Check if child expression needs parentheses."""
        if child.type != ExpressionType.BINARY_OP:
            return False

        # Operator precedence map (higher = tighter binding)
        precedence = {
            '^': 5,  # Power
            '*': 4, '/': 4, 'MOD': 4,
            '+': 3, '-': 3,
            '<': 2, '>': 2, '<=': 2, '>=': 2, '=': 2, '<>': 2,
            'AND': 1,
            'OR': 0,
        }

        parent_prec = precedence.get(parent_op, 0)
        child_prec = precedence.get(child.value, 0)

        return child_prec < parent_prec


@dataclass
class StackValue:
    """Represents a value on the emulation stack."""
    expression: str
    type: str | None = None
    is_lvalue: bool = False


class ExpressionReconstructor:
    """Reconstructs high-level expressions from P-code using stack emulation."""

    def __init__(self):
        """Initialize the reconstructor."""
        self.stack: list[StackValue] = []
        self.locals: dict[int, str] = {}
        self.strings: dict[int, str] = {}
        self.methods: dict[int, str] = {}
        self.fields: dict[int, str] = {}

        # Initialize some common locals
        self.locals[0] = "this"
        self.locals[1] = "return_value"

    def emulate_block(self, block: ControlBlock) -> None:
        """Emulate a control flow block and update its statements.
        
        Args:
            block: Control flow block to emulate
        """
        self.stack = []  # Reset stack for each block
        block.statements = []

        for inst in block.instructions:
            try:
                statement = self._emulate_instruction(inst)
                if statement:
                    block.statements.append(statement)
            except Exception as e:
                logger.error(f"Error emulating instruction {inst.opcode_name} at {inst.address:04X}: {e}")
                block.statements.append(f"// ERROR: {inst.text_format}")

    def _emulate_instruction(self, inst: PCodeInstruction) -> str | None:
        """Emulate a single instruction.
        
        Args:
            inst: The instruction to emulate
            
        Returns:
            Statement string if the instruction produces one, None otherwise
        """
        opcode = inst.opcode_name
        operands = inst.operand_values

        # Stack operations
        if opcode.startswith("PUSH_"):
            return self._handle_push(opcode, operands)
        elif opcode == "POP":
            if self.stack:
                self.stack.pop()
            return None
        elif opcode == "DUP":
            if self.stack:
                self.stack.append(self.stack[-1])
            return None

        # Arithmetic operations
        elif opcode in ["ADD", "SUB", "MULT", "DIV", "MOD", "POWER"]:
            return self._handle_binary_op(opcode)
        elif opcode.startswith("ADD_") or opcode.startswith("SUB_") or \
             opcode.startswith("MULT_") or opcode.startswith("DIV_") or \
             opcode.startswith("MOD_") or opcode.startswith("POWER_"):
            return self._handle_typed_binary_op(opcode)

        # Comparison operations
        elif opcode in ["EQ", "NE", "LT", "GT", "LE", "GE"]:
            return self._handle_comparison(opcode)
        elif opcode.startswith("EQ_") or opcode.startswith("NE_") or \
             opcode.startswith("LT_") or opcode.startswith("GT_") or \
             opcode.startswith("LE_") or opcode.startswith("GE_"):
            return self._handle_typed_comparison(opcode)

        # Logical operations
        elif opcode in ["AND", "OR", "NOT"]:
            return self._handle_logical(opcode)

        # Assignment operations
        elif opcode.startswith("ASSIGN"):
            return self._handle_assignment(opcode, operands)
        elif opcode.startswith("STORE"):
            return self._handle_store(opcode, operands)

        # Function calls
        elif "CALL" in opcode:
            return self._handle_call(opcode, operands)

        # Field/array access
        elif opcode == "DOT":
            return self._handle_dot(operands)
        elif opcode == "INDEX":
            return self._handle_index()

        # Control flow
        elif opcode == "RETURN":
            return self._handle_return()

        # Type conversions
        elif opcode.startswith("CNV_"):
            return self._handle_conversion(opcode)

        # Database operations
        elif opcode.startswith("DB"):
            return self._handle_database(opcode, operands)

        # Default: just comment the instruction
        return f"// {inst.text_format}"

    def _handle_push(self, opcode: str, operands: list) -> str | None:
        """Handle PUSH operations."""
        if opcode == "PUSH_LOCAL_VAR" and operands:
            var_idx = operands[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")
            self.stack.append(StackValue(var_name, "local"))
        elif opcode == "PUSH_CONST_INT" and operands:
            self.stack.append(StackValue(str(operands[0]), "int"))
        elif opcode == "PUSH_CONST_STRING" and operands:
            str_idx = operands[0]
            string_val = self.strings.get(str_idx, f'"string_{str_idx}"')
            self.stack.append(StackValue(string_val, "string"))
        elif opcode == "PUSH_CONST_BOOL" and operands:
            bool_val = "true" if operands[0] else "false"
            self.stack.append(StackValue(bool_val, "boolean"))
        elif opcode == "PUSH_THIS":
            self.stack.append(StackValue("this", "object"))
        elif opcode == "PUSH_NULL":
            self.stack.append(StackValue("null", "null"))
        else:
            # Generic push
            val = operands[0] if operands else "?"
            self.stack.append(StackValue(str(val), None))
        return None

    def _handle_binary_op(self, opcode: str) -> str | None:
        """Handle binary operations."""
        if len(self.stack) < 2:
            return f"// ERROR: Stack underflow for {opcode}"

        right = self.stack.pop()
        left = self.stack.pop()

        op_map = {
            "ADD": "+", "SUB": "-", "MULT": "*", "DIV": "/",
            "MOD": "MOD", "POWER": "^"
        }
        op = op_map.get(opcode, opcode)

        result = f"{left.expression} {op} {right.expression}"
        self.stack.append(StackValue(result, None))
        return None

    def _handle_typed_binary_op(self, opcode: str) -> str | None:
        """Handle typed binary operations (e.g., ADD_INT)."""
        # Extract base operation
        base_op = opcode.split('_')[0]
        return self._handle_binary_op(base_op)

    def _handle_comparison(self, opcode: str) -> str | None:
        """Handle comparison operations."""
        if len(self.stack) < 2:
            return f"// ERROR: Stack underflow for {opcode}"

        right = self.stack.pop()
        left = self.stack.pop()

        op_map = {
            "EQ": "=", "NE": "<>", "LT": "<", "GT": ">",
            "LE": "<=", "GE": ">="
        }
        op = op_map.get(opcode, opcode)

        result = f"{left.expression} {op} {right.expression}"
        self.stack.append(StackValue(result, "boolean"))
        return None

    def _handle_typed_comparison(self, opcode: str) -> str | None:
        """Handle typed comparison operations."""
        # Extract base operation
        base_op = opcode.split('_')[0]
        return self._handle_comparison(base_op)

    def _handle_logical(self, opcode: str) -> str | None:
        """Handle logical operations."""
        if opcode == "NOT":
            if not self.stack:
                return f"// ERROR: Stack underflow for NOT"
            operand = self.stack.pop()
            result = f"NOT {operand.expression}"
            self.stack.append(StackValue(result, "boolean"))
        else:
            if len(self.stack) < 2:
                return f"// ERROR: Stack underflow for {opcode}"
            right = self.stack.pop()
            left = self.stack.pop()
            result = f"{left.expression} {opcode} {right.expression}"
            self.stack.append(StackValue(result, "boolean"))
        return None

    def _handle_assignment(self, opcode: str, operands: list) -> str:
        """Handle assignment operations."""
        if not self.stack:
            return f"// ERROR: Stack underflow for {opcode}"

        value = self.stack.pop()

        if operands and opcode == "ASSIGN":
            # Direct assignment to a variable
            var_idx = operands[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")
            return f"{var_name} = {value.expression}"
        elif self.stack:
            # Assignment to whatever is on the stack (lvalue)
            lvalue = self.stack.pop()
            return f"{lvalue.expression} = {value.expression}"
        else:
            return f"// ERROR: No lvalue for assignment"

    def _handle_store(self, opcode: str, operands: list) -> str:
        """Handle STORE operations."""
        if not self.stack:
            return f"// ERROR: Stack underflow for {opcode}"

        value = self.stack.pop()
        if operands:
            var_idx = operands[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")
            return f"{var_name} = {value.expression}"
        return f"// {opcode} {value.expression}"

    def _handle_call(self, opcode: str, operands: list) -> str | None:
        """Handle function calls."""
        method_name = "unknown_method"
        if operands:
            method_idx = operands[0]
            method_name = self.methods.get(method_idx, f"method_{method_idx}")

        # Pop arguments from stack (simplified - real implementation needs arg count)
        args = []
        # For now, assume no arguments
        # TODO: Implement proper argument handling

        result = f"{method_name}()"

        if "VOID" not in opcode:
            # Non-void call, push result
            self.stack.append(StackValue(result, None))
            return None
        else:
            # Void call, return as statement
            return result

    def _handle_dot(self, operands: list) -> str | None:
        """Handle field access."""
        if not self.stack:
            return f"// ERROR: Stack underflow for DOT"

        obj = self.stack.pop()
        field_name = "unknown_field"
        if operands:
            field_idx = operands[0]
            field_name = self.fields.get(field_idx, f"field_{field_idx}")

        result = f"{obj.expression}.{field_name}"
        self.stack.append(StackValue(result, None))
        return None

    def _handle_index(self) -> str | None:
        """Handle array indexing."""
        if len(self.stack) < 2:
            return f"// ERROR: Stack underflow for INDEX"

        index = self.stack.pop()
        array = self.stack.pop()

        result = f"{array.expression}[{index.expression}]"
        self.stack.append(StackValue(result, None))
        return None

    def _handle_return(self) -> str:
        """Handle RETURN statement."""
        if self.stack:
            value = self.stack.pop()
            return f"return {value.expression}"
        return "return"

    def _handle_conversion(self, opcode: str) -> str | None:
        """Handle type conversions."""
        if not self.stack:
            return f"// ERROR: Stack underflow for {opcode}"

        value = self.stack.pop()
        # For now, just preserve the value
        # TODO: Implement proper type conversion
        self.stack.append(value)
        return None

    def _handle_database(self, opcode: str, operands: list) -> str:
        """Handle database operations."""
        if opcode == "DBOPEN":
            return "OPEN cursor"
        elif opcode == "DBCLOSE":
            return "CLOSE cursor"
        elif opcode == "DBFETCH":
            return "FETCH cursor INTO variables"
        elif opcode == "DBSELECT":
            return "SELECT ... FROM ..."
        elif opcode == "DBINSERT":
            return "INSERT INTO ..."
        elif opcode == "DBUPDATE":
            return "UPDATE ... SET ..."
        elif opcode == "DBDELETE":
            return "DELETE FROM ..."
        elif opcode == "DBCOMMIT":
            return "COMMIT"
        elif opcode == "DBROLLBACK":
            return "ROLLBACK"
        else:
            return f"// {opcode}"


# Backwards compatibility aliases
StackEmulator = ExpressionReconstructor
ExpressionLifter = ExpressionReconstructor