"""Expression reconstruction for PowerBuilder P-code.

This module provides enhanced expression reconstruction with advanced stack management,
pattern recognition, and context recovery. It serves as a drop-in replacement for
the legacy ExpressionReconstructor while providing significantly improved results.

The enhanced system includes:
- Advanced stack management with recovery
- Pattern recognition for PowerBuilder idioms
- Context-aware type inference
- Enhanced output formatting
- Confidence scoring
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

# Keep legacy imports for compatibility
from src.decompile.core.opcode_formatter import SpecialOpcodeFormatter
from src.decompile.pcode.decoder import PCodeInstruction
from src.decompile.types import ControlBlock

# Import the enhanced reconstruction system
from .integration import (
    create_enhanced_reconstructor,
)

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
    children: list["Expression"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        """Convert expression to PowerBuilder syntax."""
        if self.type in (ExpressionType.LITERAL, ExpressionType.VARIABLE):
            return str(self.value)

        if self.type == ExpressionType.BINARY_OP:
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
            operand = self.children[0].to_string()
            if self.value == "NOT":
                return f"NOT {operand}"
            return f"{self.value}{operand}"

        if self.type == ExpressionType.CALL:
            args = ", ".join(c.to_string() for c in self.children)
            return f"{self.value}({args})"

        if self.type == ExpressionType.FIELD_ACCESS:
            if self.children:
                obj = self.children[0].to_string()
                return f"{obj}.{self.value}"
            return self.value

        if self.type == ExpressionType.ARRAY_ACCESS:
            array = self.children[0].to_string()
            index = self.children[1].to_string()
            return f"{array}[{index}]"

        return str(self.value)

    def _needs_parentheses(self, child: "Expression", parent_op: str) -> bool:
        """Check if child expression needs parentheses."""
        if child.type != ExpressionType.BINARY_OP:
            return False

        # Operator precedence map (higher = tighter binding)
        precedence = {
            "^": 5,  # Power
            "*": 4,
            "/": 4,
            "MOD": 4,
            "+": 3,
            "-": 3,
            "<": 2,
            ">": 2,
            "<=": 2,
            ">=": 2,
            "=": 2,
            "<>": 2,
            "AND": 1,
            "OR": 0,
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
    """Enhanced expression reconstructor with advanced capabilities.

    This class now serves as a wrapper around the enhanced reconstruction system,
    providing the same interface as the legacy version but with dramatically
    improved results including:

    - Stack underflow recovery
    - Pattern recognition
    - Type inference
    - Enhanced output formatting
    - Confidence scoring
    """

    def __init__(self, use_enhanced: bool = True) -> None:
        """Initialize the reconstructor.

        Args:
            use_enhanced: Use enhanced reconstruction system (recommended)
        """
        self._use_enhanced = use_enhanced
        if use_enhanced:
            # Use the enhanced system with balanced mode for good performance/quality tradeoff
            self._reconstructor = create_enhanced_reconstructor(
                quality_mode="balanced", output_style="standard", enable_debug=False
            )
            logger.info("Initialized enhanced ExpressionReconstructor")
        else:
            # Legacy initialization for compatibility testing
            self._reconstructor = None
            self._init_legacy()
            logger.warning("Using legacy ExpressionReconstructor - consider upgrading")

        # Expose the same interface as legacy
        self.stack = (
            self._reconstructor.stack if self._reconstructor else self._legacy_stack
        )
        self.locals = (
            self._reconstructor.locals if self._reconstructor else self._legacy_locals
        )
        self.strings = (
            self._reconstructor.strings if self._reconstructor else self._legacy_strings
        )
        self.methods = (
            self._reconstructor.methods if self._reconstructor else self._legacy_methods
        )
        self.fields = (
            self._reconstructor.fields if self._reconstructor else self._legacy_fields
        )

    def _create_stack_value(self, expression: str, value_type: str | None = None, is_lvalue: bool = False) -> Any:
        """Create a stack value compatible with the current stack type."""
        if self._use_enhanced and self._reconstructor:
            # Import here to avoid circular imports
            from .enhanced_stack import StackValue as EnhancedStackValue, StackValueType, StackValueOrigin
            
            # Map string types to enhanced types
            type_map = {
                "integer": StackValueType.INTEGER,
                "int": StackValueType.INTEGER,
                "long": StackValueType.LONG,
                "double": StackValueType.DOUBLE,
                "real": StackValueType.REAL,
                "decimal": StackValueType.DECIMAL,
                "string": StackValueType.STRING,
                "boolean": StackValueType.BOOLEAN,
                "date": StackValueType.DATE,
                "time": StackValueType.TIME,
                "datetime": StackValueType.DATETIME,
                "object": StackValueType.OBJECT,
                "null": StackValueType.NULL,
                "local": StackValueType.UNKNOWN,  # Local variables type unknown initially
            }
            stack_type = type_map.get(value_type, StackValueType.UNKNOWN)
            return EnhancedStackValue(
                expression=expression,
                value_type=stack_type,
                origin=StackValueOrigin.UNKNOWN,
                is_lvalue=is_lvalue
            )
        else:
            # Use legacy StackValue
            return StackValue(expression=expression, type=value_type, is_lvalue=is_lvalue)

    def _init_legacy(self) -> None:
        """Initialize legacy components."""
        self._legacy_stack: list[StackValue] = []
        self._legacy_locals: dict[int, str] = {}
        self._legacy_strings: dict[int, str] = {}
        self._legacy_methods: dict[int, str] = {}
        self._legacy_fields: dict[int, str] = {}

        # Initialize special opcode formatter
        self.special_formatter = SpecialOpcodeFormatter()

        # Initialize some common locals
        self._legacy_locals[0] = "this"
        self._legacy_locals[1] = "return_value"

    def emulate_block(self, block: ControlBlock) -> None:
        """Emulate a control flow block and update its statements.

        Args:
            block: Control flow block to emulate
        """
        if self._reconstructor:
            # Use enhanced reconstruction system
            try:
                self._reconstructor.emulate_block(block)
                logger.debug(
                    "Enhanced reconstruction completed for block with %d instructions",
                    len(block.instructions),
                )
            except Exception as e:
                logger.error(
                    "Enhanced reconstruction failed, using error fallback: %s", e
                )
                block.statements = [f"// Enhanced reconstruction failed: {e}"]
        else:
            # Legacy reconstruction (maintained for compatibility testing)
            self._legacy_emulate_block(block)

    def _legacy_emulate_block(self, block: ControlBlock) -> None:
        """Legacy emulation method (kept for compatibility testing)."""
        self._legacy_stack = []  # Reset stack for each block
        block.statements = []

        for inst in block.instructions:
            try:
                statement = self._emulate_instruction(inst)
                if statement:
                    block.statements.append(statement)
            except (IndexError, KeyError) as e:
                # Handle common errors gracefully
                logger.warning(
                    "Stack or lookup error emulating %s at %04X: %s",
                    inst.opcode_name,
                    inst.offset,
                    e,
                )
                # Try to generate a meaningful comment instead of failing
                if inst.opcode_name == "RETURN" and isinstance(e, IndexError):
                    block.statements.append("return  // Stack was empty")
                else:
                    block.statements.append(
                        f"// {inst.opcode_name} - {type(e).__name__}: {e}"
                    )
            except Exception as e:
                logger.exception(
                    "Unexpected error emulating instruction %s at %04X: %s",
                    inst.opcode_name,
                    inst.offset,
                    e,
                )
                # Generate a comment with the instruction details
                operands = (
                    ", ".join(str(v) for v in inst.operands) if inst.operands else ""
                )
                block.statements.append(
                    f"// ERROR: {inst.opcode_name} {operands} - {e}"
                )

    def get_reconstruction_statistics(self) -> dict[str, Any]:
        """Get reconstruction statistics (enhanced feature).

        Returns:
            Statistics about the reconstruction process
        """
        if self._reconstructor:
            return self._reconstructor.get_reconstruction_statistics()
        return {
            "mode": "legacy",
            "enhanced_features": False,
            "message": "Upgrade to enhanced system for detailed statistics",
        }

    def _emulate_instruction(self, inst: PCodeInstruction) -> str | None:
        """Emulate a single instruction.

        Args:
            inst: The instruction to emulate

        Returns:
            Statement string if the instruction produces one, None otherwise
        """
        opcode = inst.opcode_name
        operands = inst.operands

        # Stack operations
        if opcode.startswith("PUSH_"):
            return self._handle_push(opcode, operands)
        if opcode == "POP":
            if self.stack:
                self.stack.pop()
            return None
        if opcode == "DUP":
            if self.stack:
                # Create a proper copy of the top stack value
                top_value = self.stack[-1]
                if hasattr(top_value, 'expression'):
                    # For both enhanced and legacy StackValue types
                    value_type = getattr(top_value, 'type', None) or getattr(top_value, 'value_type', None)
                    is_lvalue = getattr(top_value, 'is_lvalue', False)
                    new_value = self._create_stack_value(
                        top_value.expression, 
                        str(value_type) if value_type else None, 
                        is_lvalue
                    )
                    self.stack.append(new_value)
                else:
                    # Fallback for unexpected types
                    self.stack.append(top_value)
            return None

        # Arithmetic operations
        if opcode in ["ADD", "SUB", "MULT", "DIV", "MOD", "POWER"]:
            return self._handle_binary_op(opcode)
        if opcode.startswith(("ADD_", "SUB_", "MULT_", "DIV_", "MOD_", "POWER_")):
            return self._handle_typed_binary_op(opcode)

        # Comparison operations
        if opcode in ["EQ", "NE", "LT", "GT", "LE", "GE"]:
            return self._handle_comparison(opcode)
        if opcode.startswith(("EQ_", "NE_", "LT_", "GT_", "LE_", "GE_")):
            return self._handle_typed_comparison(opcode)

        # Logical operations
        if opcode in ["AND", "OR", "NOT"]:
            return self._handle_logical(opcode)

        # Assignment operations
        if opcode.startswith("ASSIGN"):
            return self._handle_assignment(opcode, operands)
        if opcode.startswith("STORE"):
            return self._handle_store(opcode, operands)

        # Function calls
        if "CALL" in opcode:
            return self._handle_call(opcode, operands)

        # Field/array access
        if opcode == "DOT":
            return self._handle_dot(operands)
        if opcode == "INDEX":
            return self._handle_index()

        # Control flow
        if opcode == "RETURN":
            return self._handle_return()

        # Type conversions
        if opcode.startswith("CNV_"):
            return self._handle_conversion(opcode)

        # Database operations
        if opcode.startswith("DB"):
            return self._handle_database(opcode, operands)

        # Try special opcode formatter for other special cases
        special_format = self.special_formatter.format_opcode(opcode, operands)
        if (
            special_format and special_format != opcode
        ):  # Only use if it's actually formatted
            return special_format

        # Format instruction as comment using available attributes
        operands_str = f" {inst.operands}" if inst.operands else ""
        return f"// {inst.opcode_name}{operands_str}"

    def _handle_push(self, opcode: str, operands: list[Any]) -> None:
        """Handle PUSH operations."""
        if opcode == "PUSH_LOCAL_VAR" and operands:
            var_idx = operands[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")
            self.stack.append(self._create_stack_value(var_name, "local"))

        elif opcode == "PUSH_CONST_INT" and operands:
            self.stack.append(self._create_stack_value(str(operands[0]), "int"))

        elif opcode == "PUSH_CONST_STRING" and operands:
            str_idx = operands[0]
            string_val = self.strings.get(str_idx, f'"string_{str_idx}"')
            self.stack.append(self._create_stack_value(string_val, "string"))

        elif opcode == "PUSH_CONST_BOOL" and operands:
            bool_val = "true" if operands[0] else "false"
            self.stack.append(self._create_stack_value(bool_val, "boolean"))

        elif opcode == "PUSH_THIS":
            self.stack.append(self._create_stack_value("this", "object"))

        elif opcode == "PUSH_NULL":
            self.stack.append(self._create_stack_value("null", "null"))
        else:
            # Generic push
            val = operands[0] if operands else "?"
            self.stack.append(self._create_stack_value(str(val), None))

    def _handle_binary_op(self, opcode: str) -> str | None:
        """Handle binary operations."""
        if len(self.stack) < 2:
            # Try to recover with placeholder values
            if len(self.stack) == 1:
                left = self.stack.pop()
                right = self._create_stack_value("0", "integer")
                logger.warning(
                    "Stack underflow for %s, using 0 for right operand", opcode
                )
            else:
                left = self._create_stack_value("0", "integer")
                right = self._create_stack_value("0", "integer")
                logger.warning("Stack underflow for %s, using placeholders", opcode)
                return f"// ERROR: Stack underflow for {opcode}"
        else:
            right = self.stack.pop()
            left = self.stack.pop()

        op_map = {
            "ADD": "+",
            "SUB": "-",
            "MULT": "*",
            "DIV": "/",
            "MOD": "MOD",
            "POWER": "^",
        }
        op = op_map.get(opcode, opcode)

        result = f"{left.expression} {op} {right.expression}"
        self.stack.append(self._create_stack_value(result, None))
        return None

    def _handle_typed_binary_op(self, opcode: str) -> str | None:
        """Handle typed binary operations (e.g., ADD_INT)."""
        # Extract base operation
        base_op = opcode.split("_")[0]
        return self._handle_binary_op(base_op)

    def _handle_comparison(self, opcode: str) -> str | None:
        """Handle comparison operations."""
        if len(self.stack) < 2:
            # Try to recover with placeholder values
            if len(self.stack) == 1:
                left = self.stack.pop()
                right = self._create_stack_value("0", "integer")
                logger.warning(
                    "Stack underflow for %s, using 0 for right operand", opcode
                )
            else:
                # Generate a TRUE result to continue execution
                self.stack.append(self._create_stack_value("TRUE", "boolean"))
                return f"// ERROR: Stack underflow for {opcode} - assuming TRUE"
        else:
            right = self.stack.pop()
            left = self.stack.pop()

        op_map = {
            "EQ": "=",
            "NE": "<>",
            "LT": "<",
            "GT": ">",
            "LE": "<=",
            "GE": ">=",
        }
        op = op_map.get(opcode, opcode)

        result = f"{left.expression} {op} {right.expression}"
        self.stack.append(self._create_stack_value(result, "boolean"))
        return None

    def _handle_typed_comparison(self, opcode: str) -> str | None:
        """Handle typed comparison operations."""
        # Extract base operation
        base_op = opcode.split("_")[0]
        return self._handle_comparison(base_op)

    def _handle_logical(self, opcode: str) -> str | None:
        """Handle logical operations."""
        if opcode == "NOT":
            if not self.stack:
                return "// ERROR: Stack underflow for NOT"
            operand = self.stack.pop()
            result = f"NOT {operand.expression}"
            self.stack.append(self._create_stack_value(result, "boolean"))
        else:
            if len(self.stack) < 2:
                return f"// ERROR: Stack underflow for {opcode}"
            right = self.stack.pop()
            left = self.stack.pop()
            result = f"{left.expression} {opcode} {right.expression}"
            self.stack.append(self._create_stack_value(result, "boolean"))
        return None

    def _handle_assignment(self, opcode: str, operands: list[Any]) -> str | None:
        """Handle assignment operations."""
        if not self.stack:
            return f"// ERROR: Stack underflow for {opcode}"

        value = self.stack.pop()

        if operands:
            # Direct assignment to a variable
            var_idx = operands[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")
            return f"{var_name} = {value.expression}"
        if self.stack:
            # Assignment to whatever is on the stack (lvalue)
            lvalue = self.stack.pop()
            return f"{lvalue.expression} = {value.expression}"
        return "// ERROR: No lvalue for assignment"

    def _handle_store(self, opcode: str, operands: list[Any]) -> str | None:
        """Handle STORE operations."""
        if not self.stack:
            return f"// ERROR: Stack underflow for {opcode}"

        value = self.stack.pop()
        if operands:
            var_idx = operands[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")
            return f"{var_name} = {value.expression}"
        return f"// {opcode} {value.expression}"

    def _handle_call(self, opcode: str, operands: list[Any]) -> str | None:
        """Handle function calls."""
        method_name = "unknown_method"
        arg_count = 0

        # Parse operands - typically [method_index, arg_count] or just [method_index]
        if operands:
            method_idx = operands[0]
            method_name = self.methods.get(method_idx, f"method_{method_idx}")

        # Check if arg count is provided
        if len(operands) > 1:
            arg_count = operands[1]
        else:
            # Try to infer from opcode name (e.g., CALL_FUNC_2 has 2 args)
            parts = opcode.split("_")
            if parts and parts[-1].isdigit():
                arg_count = int(parts[-1])

        # Pop arguments from stack in reverse order (last pushed = first arg)
        args: list[str] = []
        for _ in range(arg_count):
            if self.stack:
                arg = self.stack.pop()
                args.insert(0, arg.expression)  # Insert at beginning to maintain order
            else:
                args.insert(0, "/* missing arg */")

        # Handle object method calls (DOT before CALL means object.method())
        if self.stack and len(self.stack) > 0 and "." in str(self.stack[-1].expression):
            # This might be an object reference for the method
            obj_ref = self.stack[-1]
            if obj_ref.expression.endswith(f".{method_name}"):
                # The method name was already combined with object
                self.stack.pop()
                method_call = f"{obj_ref.expression}"
            else:
                method_call = method_name
        else:
            method_call = method_name

        # Build the function call
        arg_list = ", ".join(args)
        result = f"{method_call}({arg_list})"

        if "VOID" in opcode:
            # Void call, return as statement
            return result
        # Non-void call, push result
        self.stack.append(self._create_stack_value(result, None))
        return None

    def _handle_dot(self, operands: list[Any]) -> str | None:
        """Handle field access."""
        if not self.stack:
            return "// ERROR: Stack underflow for DOT"

        obj = self.stack.pop()
        field_name = "unknown_field"
        if operands:
            field_idx = operands[0]
            field_name = self.fields.get(field_idx, f"field_{field_idx}")

        result = f"{obj.expression}.{field_name}"
        self.stack.append(self._create_stack_value(result, None))
        return None

    def _handle_index(self) -> str | None:
        """Handle array indexing."""
        if len(self.stack) < 2:
            return "// ERROR: Stack underflow for INDEX"

        index = self.stack.pop()
        array = self.stack.pop()

        result = f"{array.expression}[{index.expression}]"
        self.stack.append(self._create_stack_value(result, None))
        return None

    def _handle_return(self) -> str | None:
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

        # Extract target type from opcode
        # Common patterns: CONVERT_TO_INT, CAST_INT, TO_STRING, etc.
        target_type = None
        converted_expr = value.expression

        if "INT" in opcode and "UINT" not in opcode:
            target_type = "integer"
            converted_expr = f"Integer({value.expression})"

        elif "LONG" in opcode:
            target_type = "long"
            converted_expr = f"Long({value.expression})"

        elif "DOUBLE" in opcode or "REAL" in opcode:
            target_type = "double"
            converted_expr = f"Double({value.expression})"

        elif "DECIMAL" in opcode or "DEC" in opcode:
            target_type = "decimal"
            converted_expr = f"Dec({value.expression})"

        elif "STRING" in opcode or "STR" in opcode:
            target_type = "string"
            converted_expr = f"String({value.expression})"

        elif "BOOL" in opcode or "BOOLEAN" in opcode:
            target_type = "boolean"
            # PowerBuilder uses TRUE/FALSE
            converted_expr = f"({value.expression} <> 0)"

        elif "DATE" in opcode:
            target_type = "date"
            converted_expr = f"Date({value.expression})"

        elif "TIME" in opcode:
            target_type = "time"
            converted_expr = f"Time({value.expression})"

        elif "DATETIME" in opcode or "TIMESTAMP" in opcode:
            target_type = "datetime"
            converted_expr = f"DateTime({value.expression})"

        elif "CHAR" in opcode:
            target_type = "char"
            converted_expr = f"Char({value.expression})"

        elif "ANY" in opcode:
            target_type = "any"
            # ANY type doesn't need explicit conversion in PowerBuilder
            converted_expr = value.expression
        else:
            # Generic cast if we can't determine the type
            converted_expr = f"/* cast {opcode} */ {value.expression}"

        # Create new stack value with type information
        self.stack.append(self._create_stack_value(converted_expr, target_type))
        return None

    def _handle_database(self, opcode: str, operands: list[Any]) -> str | None:
        """Handle database operations."""
        # Handle common database operations
        if opcode == "DB_OPEN" and operands:
            return f"// Open database connection: {operands[0]}"
        if opcode == "DB_CLOSE":
            return "// Close database connection"
        if opcode == "DB_EXECUTE" and self.stack:
            sql = self.stack.pop()
            return f"EXECUTE IMMEDIATE {sql.expression}"
        if opcode == "DB_FETCH":
            return "FETCH NEXT"
        if opcode == "DB_COMMIT":
            return "COMMIT"
        if opcode == "DB_ROLLBACK":
            return "ROLLBACK"
        # Generic database operation
        return f"// Database operation: {opcode} {operands}"


# Backwards compatibility aliases
StackEmulator = ExpressionReconstructor
ExpressionLifter = ExpressionReconstructor
