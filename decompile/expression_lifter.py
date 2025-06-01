"""Expression lifter for PowerBuilder P-code.

This module lifts low-level stack operations into high-level expressions,
working in conjunction with the stack emulator.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Tuple, Any
from enum import Enum, auto

from .pcode_decoder_v2 import PCodeInstruction

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
    data_type: Optional[str] = None
    children: List['Expression'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_string(self) -> str:
        """Convert expression to PowerBuilder syntax."""
        if self.type == ExpressionType.LITERAL:
            return str(self.value)
        
        elif self.type == ExpressionType.VARIABLE:
            return str(self.value)
        
        elif self.type == ExpressionType.BINARY_OP:
            if len(self.children) == 2:
                left = self.children[0].to_string()
                right = self.children[1].to_string()
                op = self.value
                
                # Handle precedence
                if self._needs_parens(self.children[0], self):
                    left = f"({left})"
                if self._needs_parens(self.children[1], self):
                    right = f"({right})"
                
                return f"{left} {op} {right}"
        
        elif self.type == ExpressionType.UNARY_OP:
            if self.children:
                operand = self.children[0].to_string()
                if self.value == '-':
                    return f"-{operand}"
                elif self.value == 'not':
                    return f"not {operand}"
                else:
                    return f"{self.value}({operand})"
        
        elif self.type == ExpressionType.CALL:
            func_name = self.value
            args = [child.to_string() for child in self.children]
            return f"{func_name}({', '.join(args)})"
        
        elif self.type == ExpressionType.FIELD_ACCESS:
            if self.children:
                obj = self.children[0].to_string()
                field = self.value
                return f"{obj}.{field}"
        
        elif self.type == ExpressionType.ARRAY_ACCESS:
            if len(self.children) == 2:
                array = self.children[0].to_string()
                index = self.children[1].to_string()
                return f"{array}[{index}]"
        
        elif self.type == ExpressionType.CAST:
            if self.children:
                expr = self.children[0].to_string()
                cast_type = self.value
                return f"{cast_type}({expr})"
        
        elif self.type == ExpressionType.CONDITIONAL:
            if len(self.children) == 3:
                cond = self.children[0].to_string()
                then_expr = self.children[1].to_string()
                else_expr = self.children[2].to_string()
                return f"if({cond}, {then_expr}, {else_expr})"
        
        return f"<{self.type.name}: {self.value}>"
    
    def _needs_parens(self, child: 'Expression', parent: 'Expression') -> bool:
        """Check if child expression needs parentheses."""
        if child.type != ExpressionType.BINARY_OP:
            return False
        
        # Operator precedence (higher number = higher precedence)
        precedence = {
            '^': 5,
            '*': 4, '/': 4, '%': 4,
            '+': 3, '-': 3,
            '<': 2, '<=': 2, '>': 2, '>=': 2,
            '=': 1, '<>': 1,
            'and': 0,
            'or': -1
        }
        
        child_prec = precedence.get(child.value, 0)
        parent_prec = precedence.get(parent.value, 0)
        
        return child_prec < parent_prec


class ExpressionLifter:
    """Lifts P-code instructions to high-level expressions."""
    
    def __init__(self):
        """Initialize the expression lifter."""
        self.stack: List[Expression] = []
        self.locals: Dict[int, str] = {}
        self.globals: Dict[int, str] = {}
        self.strings: Dict[int, str] = {}
        self.methods: Dict[int, str] = {}
        self.fields: Dict[int, str] = {}
        self.constants: Dict[int, Any] = {}
    
    def lift_instruction_sequence(self, instructions: List[PCodeInstruction]) -> List[Union[Expression, str]]:
        """Lift a sequence of instructions to expressions and statements.
        
        Returns:
            List of expressions and statement strings
        """
        results = []
        
        for inst in instructions:
            result = self.lift_instruction(inst)
            if result:
                results.append(result)
        
        # Handle any remaining stack values
        while self.stack:
            expr = self.stack.pop()
            results.append(f"// Orphan expression: {expr.to_string()}")
        
        return results
    
    def lift_instruction(self, inst: PCodeInstruction) -> Optional[Union[Expression, str]]:
        """Lift a single instruction.
        
        Returns:
            Expression, statement string, or None
        """
        opcode = inst.opcode_name
        
        # Push operations
        if opcode.startswith("PUSH_"):
            self._handle_push(inst)
            return None
        
        # Binary operations
        elif opcode in self._get_binary_ops():
            self._handle_binary_op(opcode)
            return None
        
        # Unary operations
        elif opcode in self._get_unary_ops():
            self._handle_unary_op(opcode)
            return None
        
        # Store operations
        elif opcode.startswith("STORE_"):
            return self._handle_store(inst)
        
        # Load operations
        elif opcode.startswith("LOAD_"):
            self._handle_load(inst)
            return None
        
        # Function calls
        elif self._is_call_opcode(opcode):
            return self._handle_call(inst)
        
        # Control flow
        elif opcode in ["RETURN", "HALT", "EXIT"]:
            return self._handle_control_flow(inst)
        
        # Type conversions
        elif opcode.startswith("CNV_"):
            self._handle_conversion(inst)
            return None
        
        # Object operations
        elif opcode == "DOT":
            self._handle_dot(inst)
            return None
        
        elif opcode == "INDEX":
            self._handle_index()
            return None
        
        elif opcode == "NEW":
            self._handle_new(inst)
            return None
        
        # Default
        else:
            return f"// Unhandled: {inst.text_format}"
    
    def _get_binary_ops(self) -> Dict[str, str]:
        """Get mapping of binary operation opcodes to operators."""
        return {
            "ADD": "+", "ADD_INT": "+", "ADD_LONG": "+", "ADD_FLOAT": "+",
            "SUB": "-", "SUB_INT": "-", "SUB_LONG": "-", "SUB_FLOAT": "-",
            "MUL": "*", "MUL_INT": "*", "MUL_LONG": "*", "MUL_FLOAT": "*",
            "DIV": "/", "DIV_INT": "/", "DIV_LONG": "/", "DIV_FLOAT": "/",
            "POW": "^", "POW_INT": "^", "POW_LONG": "^", "POW_FLOAT": "^",
            "MOD": "%", "MOD_INT": "%",
            "AND": "and", "OR": "or",
            "EQ": "=", "NE": "<>", "LT": "<", "LE": "<=", "GT": ">", "GE": ">=",
            "EQ_INT": "=", "NE_INT": "<>", "LT_INT": "<", "LE_INT": "<=",
            "GT_INT": ">", "GE_INT": ">=",
        }
    
    def _get_unary_ops(self) -> Dict[str, str]:
        """Get mapping of unary operation opcodes to operators."""
        return {
            "NEG": "-", "NEG_INT": "-", "NEG_LONG": "-", "NEG_FLOAT": "-",
            "NOT": "not",
            "INCR": "++", "DECR": "--",
            "INCR_INT": "++", "DECR_INT": "--",
        }
    
    def _is_call_opcode(self, opcode: str) -> bool:
        """Check if opcode is a function call."""
        return opcode in [
            "CALL", "GLOBFUNCCALL", "DOTFUNCCALL", "DLLFUNCCALL",
            "EVENTCALL", "FUNCCALL", "METHODCALL"
        ]
    
    def _handle_push(self, inst: PCodeInstruction) -> None:
        """Handle PUSH operations."""
        opcode = inst.opcode_name
        
        if opcode == "PUSH_CONST_INT":
            value = inst.operand_values[0] if inst.operand_values else 0
            expr = Expression(ExpressionType.LITERAL, value, "integer")
            self.stack.append(expr)
        
        elif opcode == "PUSH_CONST_STRING":
            idx = inst.operand_values[0] if inst.operand_values else 0
            value = self.strings.get(idx, f'"string_{idx}"')
            expr = Expression(ExpressionType.LITERAL, value, "string")
            self.stack.append(expr)
        
        elif opcode == "PUSH_CONST_BOOL":
            value = inst.operand_values[0] if inst.operand_values else 0
            bool_val = "true" if value else "false"
            expr = Expression(ExpressionType.LITERAL, bool_val, "boolean")
            self.stack.append(expr)
        
        elif opcode == "PUSH_CONST_NULL":
            expr = Expression(ExpressionType.LITERAL, "null", "null")
            self.stack.append(expr)
        
        elif opcode == "PUSH_CONST_REAL":
            value = inst.operand_values[0] if inst.operand_values else 0.0
            expr = Expression(ExpressionType.LITERAL, str(value), "real")
            self.stack.append(expr)
        
        elif opcode in ["PUSH_LOCAL_VAR", "PUSH_LOCAL_REF"]:
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = self.locals.get(idx, f"local_{idx}")
            expr = Expression(ExpressionType.VARIABLE, var_name)
            self.stack.append(expr)
        
        elif opcode in ["PUSH_GLOBAL_VAR", "PUSH_GLOBAL_REF"]:
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = self.globals.get(idx, f"global_{idx}")
            expr = Expression(ExpressionType.VARIABLE, var_name)
            self.stack.append(expr)
        
        elif opcode == "PUSH_THIS":
            expr = Expression(ExpressionType.VARIABLE, "this", "object")
            self.stack.append(expr)
        
        elif opcode == "PUSH_PARENT":
            expr = Expression(ExpressionType.VARIABLE, "parent", "object")
            self.stack.append(expr)
        
        elif opcode == "PUSH_CONST_DATE":
            # Date constant
            value = inst.operand_values[0] if inst.operand_values else 0
            expr = Expression(ExpressionType.LITERAL, f"date({value})", "date")
            self.stack.append(expr)
        
        elif opcode == "PUSH_CONST_TIME":
            # Time constant
            value = inst.operand_values[0] if inst.operand_values else 0
            expr = Expression(ExpressionType.LITERAL, f"time({value})", "time")
            self.stack.append(expr)
        
        else:
            # Generic push
            expr = Expression(ExpressionType.LITERAL, f"{opcode}({inst.operand_values})")
            self.stack.append(expr)
    
    def _handle_binary_op(self, opcode: str) -> None:
        """Handle binary operations."""
        op_map = self._get_binary_ops()
        
        if opcode in op_map:
            if len(self.stack) < 2:
                logger.warning(f"{opcode} with insufficient stack")
                return
            
            right = self.stack.pop()
            left = self.stack.pop()
            
            operator = op_map[opcode]
            
            # Determine result type
            result_type = self._infer_binary_type(left.data_type, right.data_type, operator)
            
            expr = Expression(
                ExpressionType.BINARY_OP,
                operator,
                result_type,
                children=[left, right]
            )
            self.stack.append(expr)
    
    def _handle_unary_op(self, opcode: str) -> None:
        """Handle unary operations."""
        op_map = self._get_unary_ops()
        
        if opcode in op_map:
            if not self.stack:
                logger.warning(f"{opcode} with empty stack")
                return
            
            operand = self.stack.pop()
            operator = op_map[opcode]
            
            # Special handling for increment/decrement
            if operator in ["++", "--"]:
                # These modify the variable and return the value
                if operand.type == ExpressionType.VARIABLE:
                    # Create assignment expression
                    one = Expression(ExpressionType.LITERAL, "1", "integer")
                    op = "+" if operator == "++" else "-"
                    
                    binary_expr = Expression(
                        ExpressionType.BINARY_OP,
                        op,
                        operand.data_type,
                        children=[operand, one]
                    )
                    
                    # Push the original value back (pre-increment)
                    self.stack.append(operand)
                    # Note: The assignment would be handled separately
                    return
            
            expr = Expression(
                ExpressionType.UNARY_OP,
                operator,
                operand.data_type,
                children=[operand]
            )
            self.stack.append(expr)
    
    def _handle_store(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle store operations."""
        if not self.stack:
            return None
        
        value = self.stack.pop()
        opcode = inst.opcode_name
        
        if opcode == "STORE_LOCAL_VAR":
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = self.locals.get(idx, f"local_{idx}")
            return f"{var_name} = {value.to_string()}"
        
        elif opcode == "STORE_GLOBAL_VAR":
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = self.globals.get(idx, f"global_{idx}")
            return f"{var_name} = {value.to_string()}"
        
        elif opcode == "STORE_FIELD":
            if not self.stack:
                return None
            
            obj = self.stack.pop()
            idx = inst.operand_values[0] if inst.operand_values else 0
            field_name = self.fields.get(idx, f"field_{idx}")
            return f"{obj.to_string()}.{field_name} = {value.to_string()}"
        
        elif opcode == "STORE_ARRAY":
            if len(self.stack) < 2:
                return None
            
            index = self.stack.pop()
            array = self.stack.pop()
            return f"{array.to_string()}[{index.to_string()}] = {value.to_string()}"
        
        elif opcode == "STORE_RETURN_VAL":
            return f"return {value.to_string()}"
        
        return None
    
    def _handle_load(self, inst: PCodeInstruction) -> None:
        """Handle load operations."""
        opcode = inst.opcode_name
        
        if opcode == "LOAD_LOCAL_VAR":
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = self.locals.get(idx, f"local_{idx}")
            expr = Expression(ExpressionType.VARIABLE, var_name)
            self.stack.append(expr)
        
        elif opcode == "LOAD_GLOBAL_VAR":
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = self.globals.get(idx, f"global_{idx}")
            expr = Expression(ExpressionType.VARIABLE, var_name)
            self.stack.append(expr)
        
        elif opcode == "LOAD_FIELD":
            if not self.stack:
                return
            
            obj = self.stack.pop()
            idx = inst.operand_values[0] if inst.operand_values else 0
            field_name = self.fields.get(idx, f"field_{idx}")
            
            expr = Expression(
                ExpressionType.FIELD_ACCESS,
                field_name,
                children=[obj]
            )
            self.stack.append(expr)
    
    def _handle_call(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle function calls."""
        opcode = inst.opcode_name
        idx = inst.operand_values[0] if inst.operand_values else 0
        
        # Get function name
        if isinstance(idx, int):
            func_name = self.methods.get(idx, f"function_{idx:04x}")
        else:
            func_name = self.methods.get(idx, f"function_{idx}")
        
        # Get argument count (if available)
        arg_count = inst.operand_values[1] if len(inst.operand_values) > 1 else None
        
        # Pop arguments
        args = []
        if arg_count is not None:
            for _ in range(arg_count):
                if self.stack:
                    args.insert(0, self.stack.pop())
        else:
            # Estimate arguments - pop until we hit a likely non-argument
            while self.stack and len(args) < 10:  # Reasonable limit
                expr = self.stack[-1]
                # Stop if we hit something that's likely not an argument
                if expr.type == ExpressionType.VARIABLE and expr.value in ["this", "parent"]:
                    break
                args.insert(0, self.stack.pop())
        
        # Handle method calls
        if opcode == "DOTFUNCCALL" and self.stack:
            obj = self.stack.pop()
            call_expr = Expression(
                ExpressionType.CALL,
                f"{obj.to_string()}.{func_name}",
                children=args
            )
        else:
            call_expr = Expression(
                ExpressionType.CALL,
                func_name,
                children=args
            )
        
        # Check if this is a statement (void call) or expression
        # This is a heuristic - we'd need more context to be certain
        if opcode == "EVENTCALL":
            # Event calls are typically statements
            return call_expr.to_string()
        else:
            # Function calls typically return values
            self.stack.append(call_expr)
            return None
    
    def _handle_control_flow(self, inst: PCodeInstruction) -> str:
        """Handle control flow statements."""
        opcode = inst.opcode_name
        
        if opcode == "RETURN":
            if self.stack:
                value = self.stack.pop()
                return f"return {value.to_string()}"
            else:
                return "return"
        
        elif opcode == "HALT":
            return "halt"
        
        elif opcode == "EXIT":
            return "exit"
        
        return f"// {inst.text_format}"
    
    def _handle_conversion(self, inst: PCodeInstruction) -> None:
        """Handle type conversions."""
        if not self.stack:
            return
        
        operand = self.stack.pop()
        opcode = inst.opcode_name
        
        # Parse conversion type
        parts = opcode.split('_')
        if len(parts) >= 4:  # CNV_FROM_TO_TYPE
            to_type = parts[3] if len(parts) > 3 else parts[2]
            
            # Map to PowerBuilder type names
            type_map = {
                "INT": "integer",
                "LONG": "long",
                "FLOAT": "real",
                "DOUBLE": "double",
                "STRING": "string",
                "BOOL": "boolean",
                "DEC": "decimal",
                "UINT": "unsignedinteger",
                "ULONG": "unsignedlong"
            }
            
            pb_type = type_map.get(to_type.upper(), to_type.lower())
            
            expr = Expression(
                ExpressionType.CAST,
                pb_type,
                pb_type,
                children=[operand]
            )
            self.stack.append(expr)
        else:
            # Unknown conversion, push back unchanged
            self.stack.append(operand)
    
    def _handle_dot(self, inst: PCodeInstruction) -> None:
        """Handle field access."""
        if not self.stack:
            return
        
        obj = self.stack.pop()
        idx = inst.operand_values[0] if inst.operand_values else 0
        field_name = self.fields.get(idx, f"field_{idx}")
        
        expr = Expression(
            ExpressionType.FIELD_ACCESS,
            field_name,
            children=[obj]
        )
        self.stack.append(expr)
    
    def _handle_index(self) -> None:
        """Handle array indexing."""
        if len(self.stack) < 2:
            return
        
        index = self.stack.pop()
        array = self.stack.pop()
        
        expr = Expression(
            ExpressionType.ARRAY_ACCESS,
            None,
            children=[array, index]
        )
        self.stack.append(expr)
    
    def _handle_new(self, inst: PCodeInstruction) -> None:
        """Handle object creation."""
        idx = inst.operand_values[0] if inst.operand_values else 0
        class_name = f"class_{idx}"  # Would need class name table
        
        # Get constructor argument count if available
        arg_count = inst.operand_values[1] if len(inst.operand_values) > 1 else 0
        
        # Pop constructor arguments
        args = []
        for _ in range(arg_count):
            if self.stack:
                args.insert(0, self.stack.pop())
        
        # Create expression
        expr = Expression(
            ExpressionType.CALL,
            f"create {class_name}",
            class_name,
            children=args
        )
        self.stack.append(expr)
    
    def _infer_binary_type(self, left_type: Optional[str], right_type: Optional[str], 
                          operator: str) -> Optional[str]:
        """Infer result type of binary operation."""
        # Comparison operators always return boolean
        if operator in ["=", "<>", "<", "<=", ">", ">="]:
            return "boolean"
        
        # Boolean operators
        if operator in ["and", "or"]:
            return "boolean"
        
        # Arithmetic operators - use type promotion rules
        if not left_type or not right_type:
            return None
        
        # Simple type promotion
        numeric_types = ["integer", "long", "real", "double", "decimal"]
        if left_type in numeric_types and right_type in numeric_types:
            # Return the "larger" type
            if "double" in [left_type, right_type]:
                return "double"
            elif "real" in [left_type, right_type]:
                return "real"
            elif "decimal" in [left_type, right_type]:
                return "decimal"
            elif "long" in [left_type, right_type]:
                return "long"
            else:
                return "integer"
        
        # String concatenation
        if operator == "+" and ("string" in [left_type, right_type]):
            return "string"
        
        return None