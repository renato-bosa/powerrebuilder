"""Stack-based emulator for PowerBuilder P-code expression reconstruction.

This module implements a stack machine emulator that reconstructs high-level
expressions from low-level P-code stack operations.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union

from .control_flow_analyzer import ControlBlock
from .pcode_decoder_v2 import PCodeInstruction

logger = logging.getLogger(__name__)


@dataclass
class StackValue:
    """Represents a value on the emulation stack."""
    expression: str
    type: Optional[str] = None
    is_lvalue: bool = False


class StackEmulator:
    """Emulates P-code execution to reconstruct expressions."""
    
    def __init__(self):
        """Initialize the emulator."""
        self.stack: List[StackValue] = []
        self.locals: Dict[int, str] = {}
        self.strings: Dict[int, str] = {}
        self.methods: Dict[int, str] = {}
        self.fields: Dict[int, str] = {}
        
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
                logger.warning(f"Failed to emulate {inst.opcode_name} at {inst.address:04X}: {e}")
                block.statements.append(f"// Failed to emulate: {inst.text_format}")
        
        # Check for leftover stack values
        if self.stack:
            logger.warning(f"Stack not empty after block: {len(self.stack)} values")
            for val in self.stack:
                block.statements.append(f"// Leftover: {val.expression}")
    
    def _emulate_instruction(self, inst: PCodeInstruction) -> Optional[str]:
        """Emulate a single instruction.
        
        Args:
            inst: Instruction to emulate
            
        Returns:
            Generated statement if any, None otherwise
        """
        opcode = inst.opcode_name
        
        # Push operations
        if opcode.startswith("PUSH_"):
            return self._handle_push(inst)
        
        # Arithmetic operations
        elif opcode in ["ADD", "SUB", "MUL", "DIV", "POW", "NEG", "PLUS"]:
            return self._handle_arithmetic(opcode)
        
        # Type-specific arithmetic
        elif opcode.startswith("ADD_") or opcode.startswith("SUB_") or \
             opcode.startswith("MUL_") or opcode.startswith("DIV_") or \
             opcode.startswith("POW_") or opcode.startswith("NEG_"):
            return self._handle_typed_arithmetic(opcode)
        
        # Comparison operations
        elif opcode in ["LE", "LT", "GE", "GT", "EQ", "NE"]:
            return self._handle_comparison(opcode)
        
        # Type-specific comparisons
        elif (opcode.startswith("LE_") or opcode.startswith("LT_") or
              opcode.startswith("GE_") or opcode.startswith("GT_") or
              opcode.startswith("EQ_") or opcode.startswith("NE_")):
            return self._handle_typed_comparison(opcode)
        
        # Boolean operations
        elif opcode in ["AND", "OR", "NOT"]:
            return self._handle_boolean(opcode)
        
        # Control flow
        elif opcode in ["JUMPTRUE", "JUMPFALSE", "JUMP"]:
            return self._handle_jump(inst)
        
        # Store operations
        elif opcode.startswith("STORE_"):
            return self._handle_store(inst)
        
        # Function calls
        elif opcode in ["CALL_FUNCTION", "GLOBFUNCCALL", "DOTFUNCCALL", 
                       "DLLFUNCCALL", "EVENTCALL"]:
            return self._handle_call(inst)
        
        # Object operations
        elif opcode == "DOT":
            return self._handle_dot(inst)
        
        elif opcode == "INDEX":
            return self._handle_index()
        
        elif opcode == "NEW":
            return self._handle_new(inst)
        
        # Type conversions
        elif opcode.startswith("CNV_"):
            return self._handle_conversion(opcode)
        
        # Return
        elif opcode == "RETURN":
            return self._handle_return()
        
        # Database operations
        elif opcode.startswith("DB"):
            return self._handle_database(inst)
        
        # Default
        else:
            logger.debug(f"Unhandled opcode: {opcode}")
            return f"// {inst.text_format}"
    
    def _handle_push(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle PUSH operations."""
        opcode = inst.opcode_name
        
        if opcode == "PUSH_CONST_INT":
            value = inst.operand_values[0] if inst.operand_values else 0
            self.stack.append(StackValue(str(value), "integer"))
            
        elif opcode == "PUSH_CONST_STRING":
            idx = inst.operand_values[0] if inst.operand_values else 0
            string_val = self.strings.get(idx, f'"string_{idx}"')
            self.stack.append(StackValue(string_val, "string"))
            
        elif opcode == "PUSH_CONST_BOOL":
            value = inst.operand_values[0] if inst.operand_values else 0
            bool_str = "true" if value else "false"
            self.stack.append(StackValue(bool_str, "boolean"))
            
        elif opcode == "PUSH_LOCAL_VAR":
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = self.locals.get(idx, f"local{idx}")
            self.stack.append(StackValue(var_name, None, True))
            
        elif opcode == "PUSH_GLOBAL_VAR":
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = f"global{idx}"
            self.stack.append(StackValue(var_name, None, True))
            
        elif opcode == "PUSH_THIS":
            self.stack.append(StackValue("this", "object", True))
            
        elif opcode == "PUSH_PARENT":
            self.stack.append(StackValue("parent", "object", True))
            
        else:
            # Generic push
            self.stack.append(StackValue(f"{opcode}({inst.operand_values})"))
        
        return None
    
    def _handle_arithmetic(self, opcode: str) -> Optional[str]:
        """Handle arithmetic operations."""
        if opcode in ["ADD", "SUB", "MUL", "DIV", "POW"]:
            if len(self.stack) < 2:
                logger.warning(f"{opcode} with insufficient stack")
                return None
            
            right = self.stack.pop()
            left = self.stack.pop()
            
            op_map = {
                "ADD": "+",
                "SUB": "-",
                "MUL": "*",
                "DIV": "/",
                "POW": "^"
            }
            
            op = op_map.get(opcode, opcode)
            expr = f"({left.expression} {op} {right.expression})"
            self.stack.append(StackValue(expr))
            
        elif opcode == "NEG":
            if not self.stack:
                return None
            value = self.stack.pop()
            self.stack.append(StackValue(f"-{value.expression}"))
            
        elif opcode == "PLUS":
            # Unary plus, no-op
            pass
        
        return None
    
    def _handle_typed_arithmetic(self, opcode: str) -> Optional[str]:
        """Handle type-specific arithmetic operations."""
        # Extract operation and type
        parts = opcode.split('_', 1)
        if len(parts) == 2:
            op = parts[0]
            type_name = parts[1].lower()
            
            if op in ["ADD", "SUB", "MUL", "DIV", "POW"]:
                if len(self.stack) < 2:
                    return None
                
                right = self.stack.pop()
                left = self.stack.pop()
                
                op_map = {
                    "ADD": "+",
                    "SUB": "-",
                    "MUL": "*",
                    "DIV": "/",
                    "POW": "^"
                }
                
                operator = op_map.get(op, op)
                expr = f"({left.expression} {operator} {right.expression})"
                self.stack.append(StackValue(expr, type_name))
                
            elif op == "NEG":
                if not self.stack:
                    return None
                value = self.stack.pop()
                self.stack.append(StackValue(f"-{value.expression}", type_name))
        
        return None
    
    def _handle_comparison(self, opcode: str) -> Optional[str]:
        """Handle comparison operations."""
        if len(self.stack) < 2:
            return None
        
        right = self.stack.pop()
        left = self.stack.pop()
        
        op_map = {
            "LE": "<=",
            "LT": "<",
            "GE": ">=",
            "GT": ">",
            "EQ": "=",
            "NE": "<>"
        }
        
        op = op_map.get(opcode, opcode)
        expr = f"({left.expression} {op} {right.expression})"
        self.stack.append(StackValue(expr, "boolean"))
        
        return None
    
    def _handle_typed_comparison(self, opcode: str) -> Optional[str]:
        """Handle type-specific comparison operations."""
        # Extract operation
        for prefix in ["LE_", "LT_", "GE_", "GT_", "EQ_", "NE_"]:
            if opcode.startswith(prefix):
                base_op = prefix.rstrip('_')
                return self._handle_comparison(base_op)
        
        return None
    
    def _handle_boolean(self, opcode: str) -> Optional[str]:
        """Handle boolean operations."""
        if opcode == "NOT":
            if not self.stack:
                return None
            value = self.stack.pop()
            self.stack.append(StackValue(f"not {value.expression}", "boolean"))
            
        elif opcode in ["AND", "OR"]:
            if len(self.stack) < 2:
                return None
            
            right = self.stack.pop()
            left = self.stack.pop()
            
            op = "and" if opcode == "AND" else "or"
            expr = f"({left.expression} {op} {right.expression})"
            self.stack.append(StackValue(expr, "boolean"))
        
        return None
    
    def _handle_jump(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle jump operations."""
        opcode = inst.opcode_name
        
        if opcode in ["JUMPTRUE", "JUMPFALSE"]:
            if not self.stack:
                return None
            
            condition = self.stack.pop()
            # The actual jump is handled by control flow analyzer
            # We just note the condition was consumed
            
        # JUMP is unconditional, nothing to do
        
        return None
    
    def _handle_store(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle store operations."""
        opcode = inst.opcode_name
        
        if not self.stack:
            return None
        
        value = self.stack.pop()
        
        if opcode == "STORE_LOCAL_VAR":
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = self.locals.get(idx, f"local{idx}")
            return f"{var_name} = {value.expression}"
            
        elif opcode == "STORE_GLOBAL_VAR":
            idx = inst.operand_values[0] if inst.operand_values else 0
            var_name = f"global{idx}"
            return f"{var_name} = {value.expression}"
            
        elif opcode == "STORE_FIELD":
            if not self.stack:
                return f"field{inst.operand_values[0]} = {value.expression}"
            
            obj = self.stack.pop()
            idx = inst.operand_values[0] if inst.operand_values else 0
            field_name = self.fields.get(idx, f"field{idx}")
            return f"{obj.expression}.{field_name} = {value.expression}"
            
        elif opcode == "STORE_ARRAY":
            if len(self.stack) < 2:
                return None
            
            index = self.stack.pop()
            array = self.stack.pop()
            return f"{array.expression}[{index.expression}] = {value.expression}"
            
        elif opcode == "STORE_RETURN_VAL":
            return f"return {value.expression}"
        
        return None
    
    def _handle_call(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle function calls."""
        opcode = inst.opcode_name
        idx = inst.operand_values[0] if inst.operand_values else 0
        
        # Get function name
        if opcode == "GLOBFUNCCALL":
            func_name = self.methods.get(idx, f"global_function{idx}")
        elif opcode == "DOTFUNCCALL":
            func_name = self.methods.get(idx, f"method{idx}")
        else:
            func_name = self.methods.get(idx, f"function{idx}")
        
        # Pop arguments (we don't know the exact count, so estimate)
        args = []
        # Simple heuristic: pop values until we hit an lvalue or empty stack
        while self.stack and not self.stack[-1].is_lvalue:
            args.insert(0, self.stack.pop().expression)
        
        # For dot calls, we need the object
        if opcode == "DOTFUNCCALL" and self.stack:
            obj = self.stack.pop()
            call_expr = f"{obj.expression}.{func_name}({', '.join(args)})"
        else:
            call_expr = f"{func_name}({', '.join(args)})"
        
        # Push result (functions usually return a value)
        self.stack.append(StackValue(call_expr))
        
        # If it's a procedure call (no return value used), generate statement
        # This is a heuristic - would need more context to be sure
        return None
    
    def _handle_dot(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle field access."""
        if not self.stack:
            return None
        
        obj = self.stack.pop()
        idx = inst.operand_values[0] if inst.operand_values else 0
        field_name = self.fields.get(idx, f"field{idx}")
        
        self.stack.append(StackValue(f"{obj.expression}.{field_name}", None, True))
        
        return None
    
    def _handle_index(self) -> Optional[str]:
        """Handle array indexing."""
        if len(self.stack) < 2:
            return None
        
        index = self.stack.pop()
        array = self.stack.pop()
        
        self.stack.append(StackValue(f"{array.expression}[{index.expression}]", None, True))
        
        return None
    
    def _handle_new(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle object creation."""
        idx = inst.operand_values[0] if inst.operand_values else 0
        class_name = f"class{idx}"  # Would need class name table
        
        # Pop constructor arguments
        args = []
        # Similar to function calls
        while self.stack and not self.stack[-1].is_lvalue:
            args.insert(0, self.stack.pop().expression)
        
        expr = f"create {class_name}"
        if args:
            expr += f"({', '.join(args)})"
        
        self.stack.append(StackValue(expr, class_name))
        
        return None
    
    def _handle_conversion(self, opcode: str) -> Optional[str]:
        """Handle type conversions."""
        if not self.stack:
            return None
        
        value = self.stack.pop()
        
        # Parse conversion type
        parts = opcode.split('_')
        if len(parts) >= 4:  # CNV_FROM_TO_TYPE
            from_type = parts[1]
            to_type = parts[3] if len(parts) > 3 else parts[2]
            
            # Some conversions are implicit, others need explicit cast
            if to_type.lower() in ["string", "str"]:
                expr = f"string({value.expression})"
            elif to_type.lower() in ["int", "integer"]:
                expr = f"integer({value.expression})"
            elif to_type.lower() in ["long"]:
                expr = f"long({value.expression})"
            elif to_type.lower() in ["double", "float", "real"]:
                expr = f"double({value.expression})"
            elif to_type.lower() in ["bool", "boolean"]:
                expr = f"boolean({value.expression})"
            else:
                expr = f"{to_type}({value.expression})"
            
            self.stack.append(StackValue(expr, to_type.lower()))
        else:
            # Unknown conversion, keep original
            self.stack.append(value)
        
        return None
    
    def _handle_return(self) -> Optional[str]:
        """Handle return statement."""
        if self.stack:
            value = self.stack.pop()
            return f"return {value.expression}"
        else:
            return "return"
    
    def _handle_database(self, inst: PCodeInstruction) -> Optional[str]:
        """Handle database operations."""
        opcode = inst.opcode_name
        
        if opcode == "DBSTART":
            return "// Start transaction"
        elif opcode == "DBCOMMIT":
            return "COMMIT"
        elif opcode == "DBROLLBACK":
            return "ROLLBACK"
        elif opcode == "DBCLOSE":
            return "CLOSE cursor_name"
        elif opcode == "DBOPEN":
            return "OPEN cursor_name"
        # Add more database operations as needed
        
        return f"// {inst.text_format}"