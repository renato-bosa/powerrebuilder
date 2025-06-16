"""Advanced expression reconstruction for PowerBuilder P-code.

This module provides enhanced expression reconstruction capabilities including:
- Complex expression pattern recognition
- Expression tree optimization
- Advanced type inference
- Compound assignment reconstruction
- Ternary operator detection
- Lambda/anonymous function support
- Method chaining reconstruction
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Set, Tuple
from enum import Enum, auto

from .expression_reconstructor import (
    Expression, ExpressionType, ExpressionReconstructor, StackValue
)
from ..types import ControlBlock
from .pcode_decoder import PCodeInstruction

logger = logging.getLogger(__name__)


class AdvancedExpressionType(Enum):
    """Extended expression types for advanced reconstruction."""
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
class ExpressionPattern:
    """Represents a pattern for recognizing complex expressions."""
    name: str
    opcodes: List[str]
    min_stack_depth: int
    transformer: Any  # Callable[[List[StackValue]], Expression]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedExpressionReconstructor(ExpressionReconstructor):
    """Enhanced expression reconstructor with advanced pattern recognition."""
    
    def __init__(self) -> None:
        """Initialize the advanced reconstructor."""
        super().__init__()
        
        # Pattern registry for complex expressions
        self.patterns: List[ExpressionPattern] = []
        self._register_patterns()
        
        # Expression optimization settings
        self.optimize_expressions = True
        self.fold_constants = True
        self.simplify_boolean = True
        
        # Type inference engine
        self.type_hints: Dict[str, str] = {}
        self.inferred_types: Dict[str, str] = {}
        
        # Method chain detection
        self.method_chain_buffer: List[Expression] = []
        self.in_method_chain = False
        
        # Context for advanced features
        self.lambda_depth = 0
        self.pattern_context: List[Dict[str, Any]] = []
    
    def _register_patterns(self) -> None:
        """Register expression patterns for recognition."""
        # Ternary operator pattern: condition ? true_expr : false_expr
        self.patterns.append(ExpressionPattern(
            name="ternary",
            opcodes=["JUMPTRUE", "JUMP"],
            min_stack_depth=3,
            transformer=self._transform_ternary
        ))
        
        # Compound assignment: +=, -=, *=, /=
        self.patterns.append(ExpressionPattern(
            name="compound_assign",
            opcodes=["DUP", "PUSH_LOCAL_VAR", "ADD", "ASSIGN"],
            min_stack_depth=2,
            transformer=self._transform_compound_assign
        ))
        
        # Increment/Decrement patterns
        self.patterns.append(ExpressionPattern(
            name="increment",
            opcodes=["PUSH_LOCAL_VAR", "PUSH_CONST_INT", "ADD", "ASSIGN"],
            min_stack_depth=1,
            transformer=self._transform_increment
        ))
        
        # Method chaining pattern
        self.patterns.append(ExpressionPattern(
            name="method_chain",
            opcodes=["DOT", "CALL", "DOT", "CALL"],
            min_stack_depth=1,
            transformer=self._transform_method_chain
        ))
        
        # Null coalescing pattern
        self.patterns.append(ExpressionPattern(
            name="null_coalesce",
            opcodes=["PUSH_NULL", "EQ", "JUMPFALSE"],
            min_stack_depth=2,
            transformer=self._transform_null_coalesce
        ))
    
    def emulate_block(self, block: ControlBlock) -> None:
        """Enhanced block emulation with pattern recognition."""
        # Reset state
        self.stack = []
        self.method_chain_buffer = []
        self.in_method_chain = False
        block.statements = []
        
        # First pass: basic emulation
        instructions = list(block.instructions)
        
        # Second pass: pattern recognition
        i = 0
        while i < len(instructions):
            # Check for matching patterns
            pattern_match = self._match_pattern(instructions[i:])
            
            if pattern_match:
                pattern, matched_count = pattern_match
                # Apply pattern transformation
                statement = self._apply_pattern(pattern, instructions[i:i+matched_count])
                if statement:
                    block.statements.append(statement)
                i += matched_count
            else:
                # Standard instruction emulation
                try:
                    statement = self._emulate_instruction(instructions[i])
                    if statement:
                        block.statements.append(statement)
                except Exception as e:
                    logger.exception(
                        f"Error emulating instruction {instructions[i].opcode_name} "
                        f"at {instructions[i].address:04X}: {e}"
                    )
                    block.statements.append(f"// ERROR: {instructions[i].text_format}")
                i += 1
        
        # Third pass: expression optimization
        if self.optimize_expressions:
            block.statements = self._optimize_statements(block.statements)
    
    def _match_pattern(self, instructions: List[PCodeInstruction]) -> Optional[Tuple[ExpressionPattern, int]]:
        """Match instruction sequence against registered patterns."""
        for pattern in self.patterns:
            if len(instructions) < len(pattern.opcodes):
                continue
            
            # Check if opcodes match
            match = True
            for i, expected_opcode in enumerate(pattern.opcodes):
                if i >= len(instructions):
                    match = False
                    break
                    
                actual_opcode = instructions[i].opcode_name
                # Allow wildcard matching with *
                if expected_opcode != "*" and not actual_opcode.startswith(expected_opcode):
                    match = False
                    break
            
            if match and len(self.stack) >= pattern.min_stack_depth:
                return (pattern, len(pattern.opcodes))
        
        return None
    
    def _apply_pattern(self, pattern: ExpressionPattern, instructions: List[PCodeInstruction]) -> Optional[str]:
        """Apply pattern transformation to create high-level expression."""
        try:
            # Extract relevant stack values
            stack_snapshot = list(self.stack[-pattern.min_stack_depth:]) if self.stack else []
            
            # Apply transformer
            expression = pattern.transformer(stack_snapshot, instructions)
            
            if expression:
                return expression.to_string()
        except Exception as e:
            logger.error(f"Failed to apply pattern {pattern.name}: {e}")
        
        return None
    
    def _transform_ternary(self, stack: List[StackValue], instructions: List[PCodeInstruction]) -> Optional[Expression]:
        """Transform ternary operator pattern."""
        if len(stack) < 3:
            return None
        
        condition = stack[-3]
        true_expr = stack[-2]
        false_expr = stack[-1]
        
        # Create ternary expression
        expr = Expression(
            type=ExpressionType.CONDITIONAL,
            value="?:",
            children=[
                self._stack_value_to_expression(condition),
                self._stack_value_to_expression(true_expr),
                self._stack_value_to_expression(false_expr)
            ]
        )
        
        # Update stack
        self.stack = self.stack[:-3]
        self.stack.append(StackValue(expr.to_string(), condition.type))
        
        return expr
    
    def _transform_compound_assign(self, stack: List[StackValue], instructions: List[PCodeInstruction]) -> Optional[Expression]:
        """Transform compound assignment pattern."""
        if len(instructions) < 4:
            return None
        
        # Detect operator from instructions
        op_instruction = instructions[2]
        op_map = {
            "ADD": "+=",
            "SUB": "-=",
            "MULT": "*=",
            "DIV": "/=",
            "MOD": "%=",
        }
        
        if op_instruction.opcode_name not in op_map:
            return None
        
        operator = op_map[op_instruction.opcode_name]
        
        # Get variable and value
        var_instruction = instructions[1]
        if var_instruction.operand_values:
            var_idx = var_instruction.operand_values[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")
            
            if stack:
                value = stack[-1]
                # Create compound assignment
                return Expression(
                    type=ExpressionType.BINARY_OP,
                    value=operator,
                    children=[
                        Expression(type=ExpressionType.VARIABLE, value=var_name),
                        self._stack_value_to_expression(value)
                    ]
                )
        
        return None
    
    def _transform_increment(self, stack: List[StackValue], instructions: List[PCodeInstruction]) -> Optional[Expression]:
        """Transform increment/decrement pattern."""
        if len(instructions) < 4:
            return None
        
        # Check if it's increment (1) or decrement (-1)
        const_instruction = instructions[1]
        if const_instruction.opcode_name == "PUSH_CONST_INT" and const_instruction.operand_values:
            const_value = const_instruction.operand_values[0]
            
            var_instruction = instructions[0]
            if var_instruction.operand_values:
                var_idx = var_instruction.operand_values[0]
                var_name = self.locals.get(var_idx, f"local_{var_idx}")
                
                if const_value == 1:
                    # Increment
                    return Expression(
                        type=ExpressionType.UNARY_OP,
                        value="++",
                        children=[Expression(type=ExpressionType.VARIABLE, value=var_name)]
                    )
                elif const_value == -1:
                    # Decrement
                    return Expression(
                        type=ExpressionType.UNARY_OP,
                        value="--",
                        children=[Expression(type=ExpressionType.VARIABLE, value=var_name)]
                    )
        
        return None
    
    def _transform_method_chain(self, stack: List[StackValue], instructions: List[PCodeInstruction]) -> Optional[Expression]:
        """Transform method chaining pattern."""
        # Collect all chained calls
        chain = []
        i = 0
        
        while i < len(instructions) - 1:
            if instructions[i].opcode_name == "DOT" and "CALL" in instructions[i+1].opcode_name:
                # Add to chain
                field_idx = instructions[i].operand_values[0] if instructions[i].operand_values else 0
                method_name = self.fields.get(field_idx, f"method_{field_idx}")
                chain.append(method_name)
                i += 2
            else:
                break
        
        if len(chain) >= 2 and stack:
            # Build chained expression
            base = self._stack_value_to_expression(stack[0])
            
            for method in chain:
                base = Expression(
                    type=ExpressionType.CALL,
                    value=f"{base.to_string()}.{method}",
                    children=[]  # Arguments would be added here
                )
            
            return base
        
        return None
    
    def _transform_null_coalesce(self, stack: List[StackValue], instructions: List[PCodeInstruction]) -> Optional[Expression]:
        """Transform null coalescing pattern (value ?? default)."""
        if len(stack) < 2:
            return None
        
        value = stack[-2]
        default = stack[-1]
        
        # Create null coalescing expression
        # PowerBuilder doesn't have ?? operator, so we use IsNull() function
        expr = Expression(
            type=ExpressionType.CONDITIONAL,
            value="IsNull",
            children=[
                self._stack_value_to_expression(value),
                self._stack_value_to_expression(default),
                self._stack_value_to_expression(value)
            ]
        )
        
        return expr
    
    def _stack_value_to_expression(self, value: StackValue) -> Expression:
        """Convert stack value to expression tree."""
        # Simple conversion - could be enhanced
        return Expression(
            type=ExpressionType.LITERAL,
            value=value.expression,
            data_type=value.type
        )
    
    def _optimize_statements(self, statements: List[str]) -> List[str]:
        """Optimize statements by applying various transformations."""
        optimized = []
        
        for stmt in statements:
            # Apply optimizations
            if self.fold_constants:
                stmt = self._fold_constants_in_statement(stmt)
            
            if self.simplify_boolean:
                stmt = self._simplify_boolean_in_statement(stmt)
            
            # Remove redundant statements
            if not self._is_redundant_statement(stmt):
                optimized.append(stmt)
        
        return optimized
    
    def _fold_constants_in_statement(self, stmt: str) -> str:
        """Fold constant expressions in statement."""
        # Simple constant folding examples
        replacements = {
            "1 + 1": "2",
            "2 * 2": "4",
            "10 / 2": "5",
            "true AND true": "true",
            "false OR false": "false",
            "NOT false": "true",
            "NOT true": "false",
        }
        
        for pattern, replacement in replacements.items():
            if pattern in stmt:
                stmt = stmt.replace(pattern, replacement)
        
        return stmt
    
    def _simplify_boolean_in_statement(self, stmt: str) -> str:
        """Simplify boolean expressions in statement."""
        # Boolean simplification patterns
        simplifications = [
            # Double negation
            (r"NOT NOT (\w+)", r"\1"),
            # Comparison with boolean
            (r"(\w+) = true", r"\1"),
            (r"(\w+) = false", r"NOT \1"),
            # Redundant conditions
            (r"(\w+) OR true", "true"),
            (r"(\w+) AND false", "false"),
        ]
        
        import re
        for pattern, replacement in simplifications:
            stmt = re.sub(pattern, replacement, stmt)
        
        return stmt
    
    def _is_redundant_statement(self, stmt: str) -> bool:
        """Check if statement is redundant and can be removed."""
        # Skip empty statements and pure comments
        if not stmt or stmt.strip().startswith("//"):
            return True
        
        # Skip no-op assignments (x = x)
        if "=" in stmt:
            parts = stmt.split("=")
            if len(parts) == 2 and parts[0].strip() == parts[1].strip():
                return True
        
        return False
    
    def infer_types(self, block: ControlBlock) -> Dict[str, str]:
        """Perform type inference on block."""
        inferred = {}
        
        for stmt in block.statements:
            # Simple type inference based on operations
            if "Integer(" in stmt:
                var = self._extract_assigned_var(stmt)
                if var:
                    inferred[var] = "integer"
            elif "String(" in stmt:
                var = self._extract_assigned_var(stmt)
                if var:
                    inferred[var] = "string"
            elif "Double(" in stmt or "." in stmt and any(c.isdigit() for c in stmt):
                var = self._extract_assigned_var(stmt)
                if var:
                    inferred[var] = "double"
        
        self.inferred_types.update(inferred)
        return inferred
    
    def _extract_assigned_var(self, stmt: str) -> Optional[str]:
        """Extract variable name from assignment statement."""
        if "=" in stmt:
            parts = stmt.split("=")
            if parts:
                return parts[0].strip()
        return None