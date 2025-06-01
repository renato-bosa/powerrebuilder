"""Stack simulator for PowerBuilder P-code.

This module simulates the P-code execution stack to reconstruct high-level
expressions and statements from low-level stack operations.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ValueType(Enum):
    """Types of values on the stack."""
    CONSTANT = "constant"
    VARIABLE = "variable"
    FIELD = "field"
    EXPRESSION = "expression"
    FUNCTION_CALL = "function_call"
    ARRAY_ACCESS = "array_access"
    UNKNOWN = "unknown"


@dataclass
class StackValue:
    """Represents a value on the stack during simulation."""
    type: ValueType
    value: Any
    data_type: Optional[str] = None
    source_addr: Optional[int] = None
    
    def __str__(self) -> str:
        if self.type == ValueType.CONSTANT:
            if isinstance(self.value, str):
                return f'"{self.value}"'
            return str(self.value)
        elif self.type == ValueType.VARIABLE:
            return f"var_{self.value}"
        elif self.type == ValueType.FIELD:
            return f"field_{self.value}"
        elif self.type == ValueType.EXPRESSION:
            return str(self.value)
        elif self.type == ValueType.FUNCTION_CALL:
            return str(self.value)
        elif self.type == ValueType.ARRAY_ACCESS:
            return str(self.value)
        else:
            return f"?{self.value}"


@dataclass
class Expression:
    """Represents a high-level expression."""
    operator: str
    operands: List[Union[StackValue, 'Expression']]
    result_type: Optional[str] = None
    
    def __str__(self) -> str:
        if self.operator == "call":
            # Function call
            func_name = self.operands[0]
            args = self.operands[1:] if len(self.operands) > 1 else []
            arg_str = ", ".join(str(arg) for arg in args)
            return f"{func_name}({arg_str})"
        elif self.operator == "[]":
            # Array access
            array = self.operands[0]
            index = self.operands[1]
            return f"{array}[{index}]"
        elif self.operator == ".":
            # Field access
            obj = self.operands[0]
            field = self.operands[1]
            return f"{obj}.{field}"
        elif len(self.operands) == 1:
            # Unary operator
            return f"{self.operator}{self.operands[0]}"
        elif len(self.operands) == 2:
            # Binary operator
            left, right = self.operands
            return f"({left} {self.operator} {right})"
        else:
            # Generic
            return f"{self.operator}({', '.join(str(op) for op in self.operands)})"


@dataclass
class SimulatorState:
    """Current state of the stack simulator."""
    stack: List[StackValue] = field(default_factory=list)
    locals: Dict[int, StackValue] = field(default_factory=dict)
    fields: Dict[int, StackValue] = field(default_factory=dict)
    statements: List[str] = field(default_factory=list)
    current_addr: int = 0
    
    def push(self, value: StackValue) -> None:
        """Push a value onto the stack."""
        self.stack.append(value)
        logger.debug(f"[{self.current_addr:04X}] PUSH: {value} (depth={len(self.stack)})")
    
    def pop(self) -> Optional[StackValue]:
        """Pop a value from the stack."""
        if not self.stack:
            logger.warning(f"[{self.current_addr:04X}] Stack underflow!")
            return None
        value = self.stack.pop()
        logger.debug(f"[{self.current_addr:04X}] POP: {value} (depth={len(self.stack)})")
        return value
    
    def peek(self, offset: int = 0) -> Optional[StackValue]:
        """Peek at stack value without popping."""
        if offset >= len(self.stack):
            return None
        return self.stack[-(offset + 1)]
    
    def add_statement(self, stmt: str) -> None:
        """Add a reconstructed statement."""
        self.statements.append(stmt)
        logger.info(f"[{self.current_addr:04X}] STATEMENT: {stmt}")


class StackSimulator:
    """Simulates P-code execution to reconstruct high-level code."""
    
    def __init__(self):
        self.state = SimulatorState()
        self.string_pool: Dict[int, str] = {}
        self.function_names: Dict[int, str] = {}
        
    def simulate_instruction(self, addr: int, opcode: str, operands: List[Any]) -> None:
        """Simulate a single P-code instruction."""
        self.state.current_addr = addr
        
        # Dispatch based on opcode
        handler = getattr(self, f"_handle_{opcode.lower()}", None)
        if handler:
            handler(operands)
        else:
            self._handle_unknown(opcode, operands)
    
    def _handle_push_const(self, operands: List[Any]) -> None:
        """Handle PUSH_CONST instruction."""
        if operands:
            value = operands[0]
            self.state.push(StackValue(ValueType.CONSTANT, value, source_addr=self.state.current_addr))
    
    def _handle_push_string(self, operands: List[Any]) -> None:
        """Handle PUSH_STRING instruction."""
        if operands:
            string_idx = operands[0]
            string_val = self.string_pool.get(string_idx, f"string_{string_idx}")
            self.state.push(StackValue(ValueType.CONSTANT, string_val, "string", self.state.current_addr))
    
    def _handle_load_var(self, operands: List[Any]) -> None:
        """Handle LOAD_VAR instruction."""
        if operands:
            var_idx = operands[0]
            # Check if variable is in locals
            if var_idx in self.state.locals:
                value = self.state.locals[var_idx]
            else:
                value = StackValue(ValueType.VARIABLE, var_idx, source_addr=self.state.current_addr)
            self.state.push(value)
    
    def _handle_store_var(self, operands: List[Any]) -> None:
        """Handle STORE_VAR instruction."""
        if operands:
            var_idx = operands[0]
            value = self.state.pop()
            if value:
                self.state.locals[var_idx] = value
                # Generate assignment statement
                self.state.add_statement(f"var_{var_idx} = {value}")
    
    def _handle_load_field(self, operands: List[Any]) -> None:
        """Handle LOAD_FIELD instruction."""
        if operands:
            field_idx = operands[0]
            obj = self.state.pop()  # Object reference
            if obj:
                field_expr = Expression(".", [obj, StackValue(ValueType.FIELD, field_idx)])
                self.state.push(StackValue(ValueType.EXPRESSION, field_expr, source_addr=self.state.current_addr))
    
    def _handle_store_field(self, operands: List[Any]) -> None:
        """Handle STORE_FIELD instruction."""
        if operands:
            field_idx = operands[0]
            value = self.state.pop()
            obj = self.state.pop()
            if value and obj:
                self.state.add_statement(f"{obj}.field_{field_idx} = {value}")
    
    def _handle_add(self, operands: List[Any]) -> None:
        """Handle ADD instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("+", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, source_addr=self.state.current_addr))
    
    def _handle_sub(self, operands: List[Any]) -> None:
        """Handle SUB instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("-", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, source_addr=self.state.current_addr))
    
    def _handle_mul(self, operands: List[Any]) -> None:
        """Handle MUL instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("*", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, source_addr=self.state.current_addr))
    
    def _handle_div(self, operands: List[Any]) -> None:
        """Handle DIV instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("/", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, source_addr=self.state.current_addr))
    
    def _handle_compare(self, operands: List[Any]) -> None:
        """Handle COMPARE instruction."""
        if operands:
            op_type = operands[0]  # EQ, NE, LT, GT, LE, GE
            right = self.state.pop()
            left = self.state.pop()
            if left and right:
                op_map = {
                    0: "==", 1: "!=", 2: "<", 3: ">", 4: "<=", 5: ">="
                }
                op_str = op_map.get(op_type, "??")
                expr = Expression(op_str, [left, right])
                self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_call_function(self, operands: List[Any]) -> None:
        """Handle CALL_FUNCTION instruction."""
        if operands:
            func_idx = operands[0]
            arg_count = operands[1] if len(operands) > 1 else 0
            
            # Pop arguments in reverse order
            args = []
            for _ in range(arg_count):
                arg = self.state.pop()
                if arg:
                    args.insert(0, arg)
            
            # Get function name
            func_name = self.function_names.get(func_idx, f"func_{func_idx}")
            
            # Create function call expression
            call_expr = Expression("call", [StackValue(ValueType.CONSTANT, func_name)] + args)
            result = StackValue(ValueType.FUNCTION_CALL, call_expr, source_addr=self.state.current_addr)
            
            self.state.push(result)
    
    def _handle_return(self, operands: List[Any]) -> None:
        """Handle RETURN instruction."""
        if self.state.stack:
            value = self.state.pop()
            self.state.add_statement(f"return {value}")
        else:
            self.state.add_statement("return")
    
    def _handle_jump(self, operands: List[Any]) -> None:
        """Handle JUMP instruction."""
        # Control flow will be handled by control flow analyzer
        pass
    
    def _handle_jump_if_false(self, operands: List[Any]) -> None:
        """Handle JUMP_IF_FALSE instruction."""
        condition = self.state.pop()
        # Control flow will be handled by control flow analyzer
        # For now, just note the condition
        logger.debug(f"Conditional jump with condition: {condition}")
    
    def _handle_array_access(self, operands: List[Any]) -> None:
        """Handle array access."""
        index = self.state.pop()
        array = self.state.pop()
        if array and index:
            expr = Expression("[]", [array, index])
            self.state.push(StackValue(ValueType.ARRAY_ACCESS, expr, source_addr=self.state.current_addr))
    
    def _handle_dup(self, operands: List[Any]) -> None:
        """Handle DUP instruction - duplicate top of stack."""
        if self.state.stack:
            top = self.state.stack[-1]
            self.state.push(top)
    
    def _handle_pop(self, operands: List[Any]) -> None:
        """Handle POP instruction - discard top of stack."""
        self.state.pop()
    
    def _handle_compare_eq(self, operands: List[Any]) -> None:
        """Handle COMPARE_EQ instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("==", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_compare_ne(self, operands: List[Any]) -> None:
        """Handle COMPARE_NE instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("!=", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_compare_lt(self, operands: List[Any]) -> None:
        """Handle COMPARE_LT instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("<", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_compare_gt(self, operands: List[Any]) -> None:
        """Handle COMPARE_GT instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression(">", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_compare_le(self, operands: List[Any]) -> None:
        """Handle COMPARE_LE instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("<=", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_compare_ge(self, operands: List[Any]) -> None:
        """Handle COMPARE_GE instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression(">=", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_and(self, operands: List[Any]) -> None:
        """Handle AND instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("and", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_or(self, operands: List[Any]) -> None:
        """Handle OR instruction."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("or", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_not(self, operands: List[Any]) -> None:
        """Handle NOT instruction."""
        value = self.state.pop()
        if value:
            expr = Expression("not", [value])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_concat(self, operands: List[Any]) -> None:
        """Handle string concatenation."""
        right = self.state.pop()
        left = self.state.pop()
        if left and right:
            expr = Expression("+", [left, right])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "string", self.state.current_addr))
    
    def _handle_new(self, operands: List[Any]) -> None:
        """Handle object creation."""
        if operands:
            class_idx = operands[0]
            # Create object creation expression
            expr = Expression("new", [StackValue(ValueType.CONSTANT, f"class_{class_idx}")])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, source_addr=self.state.current_addr))
    
    def _handle_cast(self, operands: List[Any]) -> None:
        """Handle type casting."""
        value = self.state.pop()
        if value and operands:
            target_type = operands[0]
            expr = Expression("cast", [value, StackValue(ValueType.CONSTANT, target_type)])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, str(target_type), self.state.current_addr))
    
    def _handle_instanceof(self, operands: List[Any]) -> None:
        """Handle instanceof checks."""
        value = self.state.pop()
        if value and operands:
            type_idx = operands[0]
            expr = Expression("instanceof", [value, StackValue(ValueType.CONSTANT, f"type_{type_idx}")])
            self.state.push(StackValue(ValueType.EXPRESSION, expr, "boolean", self.state.current_addr))
    
    def _handle_throw(self, operands: List[Any]) -> None:
        """Handle exception throwing."""
        exception = self.state.pop()
        if exception:
            self.state.add_statement(f"throw {exception}")
    
    def _handle_load_param(self, operands: List[Any]) -> None:
        """Handle loading function parameters."""
        if operands:
            param_idx = operands[0]
            value = StackValue(ValueType.VARIABLE, f"param_{param_idx}", source_addr=self.state.current_addr)
            self.state.push(value)
    
    def _handle_string(self, operands: List[Any]) -> None:
        """Handle STRING pseudo-instruction from decoder."""
        if operands:
            string_val = operands[0]
            # Remove prefix if present
            if string_val.startswith("UTF8:"):
                string_val = string_val[5:]
            self.state.push(StackValue(ValueType.CONSTANT, string_val, "string", self.state.current_addr))
    
    def _handle_char(self, operands: List[Any]) -> None:
        """Handle CHAR pseudo-instruction from decoder."""
        if operands:
            char_val = operands[0]
            self.state.push(StackValue(ValueType.CONSTANT, char_val, "char", self.state.current_addr))
    
    def _handle_jump_if_true(self, operands: List[Any]) -> None:
        """Handle JUMP_IF_TRUE instruction."""
        condition = self.state.pop()
        # Control flow will be handled by control flow analyzer
        logger.debug(f"Conditional jump (if true) with condition: {condition}")
    
    def _handle_nop(self, operands: List[Any]) -> None:
        """Handle NOP instruction - no operation."""
        pass
    
    def _handle_marker(self, operands: List[Any]) -> None:
        """Handle MARKER instruction - used for debugging/profiling."""
        pass
    
    def _handle_unknown(self, opcode: str, operands: List[Any]) -> None:
        """Handle unknown opcodes."""
        logger.warning(f"[{self.state.current_addr:04X}] Unknown opcode: {opcode} {operands}")
        # Try to maintain stack balance
        if "STORE" in opcode:
            self.state.pop()  # Assume stores consume a value
        elif "LOAD" in opcode or "PUSH" in opcode:
            # Assume loads/pushes produce a value
            self.state.push(StackValue(ValueType.UNKNOWN, f"{opcode}({operands})", source_addr=self.state.current_addr))
    
    def get_statements(self) -> List[str]:
        """Get all reconstructed statements."""
        return self.state.statements
    
    def get_stack_depth(self) -> int:
        """Get current stack depth."""
        return len(self.state.stack)
    
    def reset(self) -> None:
        """Reset simulator state."""
        self.state = SimulatorState()