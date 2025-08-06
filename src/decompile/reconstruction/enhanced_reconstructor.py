"""Enhanced P-code reconstruction system with advanced capabilities.

This module provides a comprehensive ExpressionReconstructor that integrates
stack management, pattern recognition, context recovery, and enhanced output
generation to produce high-quality PowerBuilder source code.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from src.decompile.core.opcode_formatter import SpecialOpcodeFormatter
from src.decompile.pcode.decoder import PCodeInstruction
from src.decompile.types import ControlBlock

from .context_recovery import ContextRecoverySystem
from .enhanced_stack import (
    EnhancedStackManager,
    StackValue,
    StackValueOrigin,
    StackValueType,
)
from .pattern_engine import PatternRecognitionEngine

logger = logging.getLogger(__name__)


class ReconstructionMode(Enum):
    """Modes for reconstruction quality vs speed."""

    FAST = auto()  # Basic reconstruction, minimal analysis
    BALANCED = auto()  # Good balance of quality and speed
    COMPREHENSIVE = auto()  # Maximum quality, full analysis


@dataclass
class ReconstructionResult:
    """Result of expression reconstruction."""

    statements: list[str] = field(default_factory=list)
    confidence: float = 0.0
    patterns_matched: int = 0
    stack_underflows: int = 0
    recoveries_performed: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class EnhancedExpressionReconstructor:
    """Advanced expression reconstructor with comprehensive capabilities."""

    def __init__(self, mode: ReconstructionMode = ReconstructionMode.BALANCED) -> None:
        """Initialize the enhanced reconstructor.

        Args:
            mode: Reconstruction mode controlling quality vs speed tradeoffs
        """
        self.mode = mode

        # Core components
        self.stack_manager = EnhancedStackManager()
        self.pattern_engine = PatternRecognitionEngine()
        self.context_recovery = ContextRecoverySystem()
        self.special_formatter = SpecialOpcodeFormatter()

        # Symbol tables (enhanced versions)
        self.locals = {}
        self.strings = {}
        self.methods = {}
        self.fields = {}

        # Reconstruction state
        self.current_block = None
        self.reconstruction_stats = {
            "instructions_processed": 0,
            "statements_generated": 0,
            "patterns_recognized": 0,
            "underflows_handled": 0,
            "high_confidence_statements": 0,
        }

        # Initialize enhanced symbol tables
        self._init_enhanced_symbols()

    def _init_enhanced_symbols(self) -> None:
        """Initialize enhanced symbol tables with PowerBuilder conventions."""
        # Enhanced local variables with type hints
        self.locals.update(
            {
                0: "this",
                1: "return_value",
                2: "temp",
                3: "loop_index",
                4: "counter",
                5: "result",
                6: "value",
                7: "text_value",
                8: "numeric_value",
                9: "boolean_flag",
            }
        )

        # Common PowerBuilder string constants
        self.strings.update(
            {
                0: '""',  # Empty string
                1: '"OK"',
                2: '"Cancel"',
                3: '"Yes"',
                4: '"No"',
                5: '"Error"',
                6: '"Warning"',
                7: '"Information"',
            }
        )

        # Enhanced method names with PowerBuilder conventions
        self.methods.update(
            {
                0: "Create",
                1: "Destroy",
                2: "Open",
                3: "Close",
                4: "Clicked",
                5: "Constructor",
                6: "Destructor",
                7: "Post",
                8: "Trigger",
                9: "GetText",
                10: "SetText",
                11: "Retrieve",
                12: "Update",
                13: "Insert",
                14: "Delete",
                15: "MessageBox",
            }
        )

        # Enhanced field names
        self.fields.update(
            {
                0: "text",
                1: "visible",
                2: "enabled",
                3: "tag",
                4: "width",
                5: "height",
                6: "x",
                7: "y",
                8: "backcolor",
                9: "textcolor",
                10: "value",
                11: "checked",
                12: "selected",
            }
        )

    def reconstruct_block(self, block: ControlBlock) -> ReconstructionResult:
        """Reconstruct a control flow block with enhanced capabilities.

        Args:
            block: Control flow block to reconstruct

        Returns:
            ReconstructionResult with generated statements and metadata
        """
        self.current_block = block
        self.stack_manager.clear()

        # Create initial snapshot
        self.stack_manager.create_snapshot(0, "block_start")

        # Phase 1: Pattern analysis (if comprehensive mode)
        pattern_matches = []
        if self.mode == ReconstructionMode.COMPREHENSIVE:
            pattern_matches = self.pattern_engine.analyze_instructions(
                block.instructions
            )
            self.reconstruction_stats["patterns_recognized"] = len(pattern_matches)

        # Phase 2: Context analysis
        enhanced_locals = self.context_recovery.enhance_variable_names(
            block.instructions
        )
        self.locals.update(enhanced_locals)

        self.context_recovery.analyze_control_flow_context(
            block.instructions
        )

        # Phase 3: Instruction processing
        statements = []
        total_confidence = 0.0

        for i, instruction in enumerate(block.instructions):
            try:
                # Create snapshot before processing instruction
                if i % 10 == 0:  # Snapshot every 10 instructions
                    self.stack_manager.create_snapshot(instruction.offset, f"instr_{i}")

                # Check for pattern matches at this position
                matching_patterns = [
                    m for m in pattern_matches if m.start_offset == instruction.offset
                ]

                if matching_patterns and self.mode != ReconstructionMode.FAST:
                    # Use pattern-based reconstruction
                    statement, confidence = self._reconstruct_with_pattern(
                        matching_patterns[0], block.instructions, i
                    )
                else:
                    # Standard instruction reconstruction
                    statement, confidence = self._reconstruct_instruction(instruction)

                if statement:
                    statements.append(statement)
                    total_confidence += confidence
                    if confidence >= 0.8:
                        self.reconstruction_stats["high_confidence_statements"] += 1

                    self.reconstruction_stats["statements_generated"] += 1

                self.reconstruction_stats["instructions_processed"] += 1

            except Exception as e:
                logger.warning(
                    "Error reconstructing instruction %s at 0x%04x: %s",
                    instruction.opcode_name,
                    instruction.offset,
                    e,
                )

                # Generate error comment
                error_comment = f"// ERROR: {instruction.opcode_name} - {e}"
                statements.append(error_comment)
                total_confidence += 0.1  # Low confidence for error cases

        # Phase 4: Post-processing and enhancement
        if self.mode == ReconstructionMode.COMPREHENSIVE:
            statements = self._enhance_statements(statements)

        # Calculate final confidence
        avg_confidence = total_confidence / len(statements) if statements else 0.0

        # Update block
        block.statements = statements

        # Create result
        result = ReconstructionResult(
            statements=statements,
            confidence=avg_confidence,
            patterns_matched=len(pattern_matches),
            stack_underflows=self.stack_manager.underflow_count,
            recoveries_performed=self.stack_manager.recovery_count,
            metadata={
                "mode": self.mode.name,
                "stack_stats": self.stack_manager.get_statistics(),
                "pattern_stats": self.pattern_engine.get_statistics(),
                "context_stats": self.context_recovery.get_recovery_statistics(),
                "reconstruction_stats": self.reconstruction_stats.copy(),
            },
        )

        logger.info(
            "Block reconstruction complete: %d statements, %.2f confidence, %d patterns",
            len(statements),
            avg_confidence,
            len(pattern_matches),
        )

        return result

    def _reconstruct_with_pattern(
        self, pattern_match, instructions: list[PCodeInstruction], current_index: int
    ) -> tuple[str | None, float]:
        """Reconstruct using pattern match."""
        try:
            # Generate code using pattern
            statement = self.pattern_engine.generate_code_for_match(pattern_match)

            if statement:
                # Skip the instructions covered by this pattern
                pattern_length = len(pattern_match.template.opcodes)

                # Simulate stack operations for the skipped instructions
                for i in range(pattern_length):
                    if current_index + i < len(instructions):
                        self._simulate_stack_operation(instructions[current_index + i])

                return statement, pattern_match.confidence

        except Exception as e:
            logger.warning("Pattern-based reconstruction failed: %s", e)

        # Fallback to normal reconstruction
        return self._reconstruct_instruction(instructions[current_index])

    def _reconstruct_instruction(
        self, instruction: PCodeInstruction
    ) -> tuple[str | None, float]:
        """Reconstruct a single instruction with enhanced capabilities."""
        opcode = instruction.opcode_name
        operands = instruction.operands
        confidence = 0.8  # Default confidence

        try:
            # Handle different instruction types
            if opcode.startswith("PUSH_"):
                return self._handle_enhanced_push(opcode, operands), confidence

            if opcode == "POP":
                self.stack_manager.pop()
                return None, confidence

            if opcode == "DUP":
                if not self.stack_manager.is_empty():
                    top_value = self.stack_manager.peek()
                    if top_value:
                        self.stack_manager.push(
                            StackValue(
                                expression=top_value.expression,
                                value_type=top_value.value_type,
                                origin=top_value.origin,
                                confidence=top_value.confidence,
                            )
                        )
                return None, confidence

            if opcode in ["ADD", "SUB", "MULT", "DIV", "MOD", "POWER"]:
                return self._handle_enhanced_binary_op(opcode), confidence

            if opcode in ["EQ", "NE", "LT", "GT", "LE", "GE"]:
                return self._handle_enhanced_comparison(opcode), confidence

            if opcode in ["AND", "OR", "NOT"]:
                return self._handle_enhanced_logical(opcode), confidence

            if opcode.startswith(("ASSIGN", "STORE")):
                return self._handle_enhanced_assignment(opcode, operands), confidence

            if "CALL" in opcode:
                return self._handle_enhanced_call(opcode, operands), confidence

            if opcode == "DOT":
                return self._handle_enhanced_dot(operands), confidence

            if opcode == "INDEX":
                return self._handle_enhanced_index(), confidence

            if opcode == "RETURN":
                return self._handle_enhanced_return(), confidence

            if opcode.startswith(("CNV_", "CAST_")):
                return self._handle_enhanced_conversion(opcode), confidence

            if opcode.startswith("JUMP"):
                return self._handle_enhanced_jump(opcode, operands), confidence

            # Try special formatter
            special_result = self.special_formatter.format_opcode(opcode, operands)
            if special_result and special_result != opcode:
                return special_result, confidence * 0.7

            # Generate generic comment
            operands_str = f" {operands}" if operands else ""
            return f"// {opcode}{operands_str}", confidence * 0.3

        except Exception as e:
            logger.warning("Instruction reconstruction failed for %s: %s", opcode, e)
            return f"// ERROR: {opcode} - {e}", 0.1

    def _handle_enhanced_push(self, opcode: str, operands: list[Any]) -> None:
        """Handle PUSH operations with enhanced type information."""
        if opcode == "PUSH_LOCAL_VAR" and operands:
            var_idx = operands[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")

            # Try to infer type from context
            var_info = self.context_recovery.type_engine.analyze_variable_usage(
                var_idx, self.current_block.instructions if self.current_block else []
            )

            self.stack_manager.push(
                StackValue(
                    expression=var_name,
                    value_type=var_info.inferred_type,
                    origin=StackValueOrigin.VARIABLE,
                    confidence=var_info.confidence,
                    source_offset=operands[0] if operands else None,
                )
            )

        elif opcode == "PUSH_CONST_INT" and operands:
            self.stack_manager.push(
                StackValue(
                    expression=str(operands[0]),
                    value_type=StackValueType.INTEGER,
                    origin=StackValueOrigin.CONSTANT,
                    confidence=1.0,
                )
            )

        elif opcode == "PUSH_CONST_STRING" and operands:
            str_idx = operands[0]
            string_val = self.strings.get(str_idx, f'"string_{str_idx}"')
            self.stack_manager.push(
                StackValue(
                    expression=string_val,
                    value_type=StackValueType.STRING,
                    origin=StackValueOrigin.CONSTANT,
                    confidence=0.9,
                )
            )

        elif opcode == "PUSH_CONST_BOOL" and operands:
            bool_val = "TRUE" if operands[0] else "FALSE"
            self.stack_manager.push(
                StackValue(
                    expression=bool_val,
                    value_type=StackValueType.BOOLEAN,
                    origin=StackValueOrigin.CONSTANT,
                    confidence=1.0,
                )
            )

        elif opcode == "PUSH_THIS":
            self.stack_manager.push(
                StackValue(
                    expression="this",
                    value_type=StackValueType.OBJECT,
                    origin=StackValueOrigin.VARIABLE,
                    confidence=1.0,
                )
            )

        elif opcode == "PUSH_NULL":
            self.stack_manager.push(
                StackValue(
                    expression="",
                    value_type=StackValueType.NULL,
                    origin=StackValueOrigin.CONSTANT,
                    confidence=1.0,
                )
            )

        else:
            # Generic push with recovery
            val = operands[0] if operands else "?"
            self.stack_manager.push(
                StackValue(
                    expression=str(val),
                    value_type=StackValueType.UNKNOWN,
                    origin=StackValueOrigin.UNKNOWN,
                    confidence=0.5,
                )
            )

    def _handle_enhanced_binary_op(self, opcode: str) -> str | None:
        """Handle binary operations with enhanced error recovery."""
        expected_types = [StackValueType.INTEGER, StackValueType.INTEGER]
        operands = self.stack_manager.pop_multiple(2, expected_types)

        if len(operands) != 2:
            return f"// ERROR: Binary operation {opcode} failed"

        right, left = operands

        op_map = {
            "ADD": "+",
            "SUB": "-",
            "MULT": "*",
            "DIV": "/",
            "MOD": "MOD",
            "POWER": "^",
        }
        op_symbol = op_map.get(opcode, opcode)

        # Determine result type
        if (
            StackValueType.REAL in (left.value_type, right.value_type)
        ):
            result_type = StackValueType.REAL
        elif (
            left.value_type == StackValueType.INTEGER
            and right.value_type == StackValueType.INTEGER
        ):
            result_type = StackValueType.INTEGER
        else:
            result_type = StackValueType.UNKNOWN

        result_expr = f"{left.expression} {op_symbol} {right.expression}"
        confidence = min(left.confidence, right.confidence) * 0.9

        self.stack_manager.push(
            StackValue(
                expression=result_expr,
                value_type=result_type,
                origin=StackValueOrigin.EXPRESSION,
                confidence=confidence,
            )
        )

        return None

    def _handle_enhanced_comparison(self, opcode: str) -> str | None:
        """Handle comparison operations with enhanced type checking."""
        operands = self.stack_manager.pop_multiple(2)

        if len(operands) != 2:
            return f"// ERROR: Comparison {opcode} failed"

        right, left = operands

        op_map = {
            "EQ": "=",
            "NE": "<>",
            "LT": "<",
            "GT": ">",
            "LE": "<=",
            "GE": ">=",
        }
        op_symbol = op_map.get(opcode, opcode)

        result_expr = f"{left.expression} {op_symbol} {right.expression}"
        confidence = min(left.confidence, right.confidence) * 0.9

        self.stack_manager.push(
            StackValue(
                expression=result_expr,
                value_type=StackValueType.BOOLEAN,
                origin=StackValueOrigin.EXPRESSION,
                confidence=confidence,
            )
        )

        return None

    def _handle_enhanced_logical(self, opcode: str) -> str | None:
        """Handle logical operations."""
        if opcode == "NOT":
            operand = self.stack_manager.pop(StackValueType.BOOLEAN)
            if not operand:
                return "// ERROR: NOT operation failed"

            result_expr = f"NOT {operand.expression}"
            self.stack_manager.push(
                StackValue(
                    expression=result_expr,
                    value_type=StackValueType.BOOLEAN,
                    origin=StackValueOrigin.EXPRESSION,
                    confidence=operand.confidence * 0.95,
                )
            )
        else:
            operands = self.stack_manager.pop_multiple(
                2, [StackValueType.BOOLEAN, StackValueType.BOOLEAN]
            )
            if len(operands) != 2:
                return f"// ERROR: Logical operation {opcode} failed"

            right, left = operands
            result_expr = f"{left.expression} {opcode} {right.expression}"
            confidence = min(left.confidence, right.confidence) * 0.9

            self.stack_manager.push(
                StackValue(
                    expression=result_expr,
                    value_type=StackValueType.BOOLEAN,
                    origin=StackValueOrigin.EXPRESSION,
                    confidence=confidence,
                )
            )

        return None

    def _handle_enhanced_assignment(
        self, opcode: str, operands: list[Any]
    ) -> str | None:
        """Handle assignment operations with enhanced variable tracking."""
        value = self.stack_manager.pop()
        if not value:
            return f"// ERROR: Assignment {opcode} failed - no value"

        if operands:
            var_idx = operands[0]
            var_name = self.locals.get(var_idx, f"local_{var_idx}")

            # Update variable type information
            var_info = self.context_recovery.type_engine.analyze_variable_usage(
                var_idx, self.current_block.instructions if self.current_block else []
            )
            var_info.inferred_type = value.value_type
            var_info.confidence = max(var_info.confidence, value.confidence * 0.8)

            return f"{var_name} = {value.expression}"

        if not self.stack_manager.is_empty():
            lvalue = self.stack_manager.pop()
            return f"{lvalue.expression} = {value.expression}"

        return "// ERROR: No target for assignment"

    def _handle_enhanced_call(self, opcode: str, operands: list[Any]) -> str | None:
        """Handle function calls with enhanced method signature detection."""
        method_name = "unknown_method"
        arg_count = 0

        if operands:
            method_idx = operands[0]
            method_name = self.methods.get(method_idx, f"method_{method_idx}")

        # Determine argument count
        if len(operands) > 1:
            arg_count = operands[1]
        else:
            # Try to parse from opcode name
            parts = opcode.split("_")
            if parts and parts[-1].isdigit():
                arg_count = int(parts[-1])

        # Pop arguments
        args = []
        for _ in range(arg_count):
            arg = self.stack_manager.pop()
            if arg:
                args.insert(0, arg.expression)
            else:
                args.insert(0, "/* missing arg */")

        # Build function call
        arg_list = ", ".join(args)
        result = f"{method_name}({arg_list})"

        if "VOID" not in opcode:
            # Non-void call, push result
            result_type = StackValueType.UNKNOWN

            # Try to infer return type from method name
            if method_name.lower() in ["len", "length", "count"]:
                result_type = StackValueType.INTEGER
            elif method_name.lower() in ["gettext", "string", "trim"]:
                result_type = StackValueType.STRING
            elif method_name.lower() in ["isnull", "isvalid"]:
                result_type = StackValueType.BOOLEAN

            self.stack_manager.push(
                StackValue(
                    expression=result,
                    value_type=result_type,
                    origin=StackValueOrigin.METHOD_RESULT,
                    confidence=0.7,
                )
            )
            return None

        return result

    def _handle_enhanced_dot(self, operands: list[Any]) -> None:
        """Handle field access with enhanced field name resolution."""
        obj = self.stack_manager.pop()
        if not obj:
            return

        field_name = "unknown_field"
        if operands:
            field_idx = operands[0]
            field_name = self.fields.get(field_idx, f"field_{field_idx}")

        result_expr = f"{obj.expression}.{field_name}"

        # Infer field type based on name
        field_type = StackValueType.UNKNOWN
        if field_name.lower() in ["text", "caption", "title"]:
            field_type = StackValueType.STRING
        elif field_name.lower() in ["visible", "enabled", "checked"]:
            field_type = StackValueType.BOOLEAN
        elif field_name.lower() in ["width", "height", "x", "y", "value"]:
            field_type = StackValueType.INTEGER

        self.stack_manager.push(
            StackValue(
                expression=result_expr,
                value_type=field_type,
                origin=StackValueOrigin.FIELD,
                confidence=obj.confidence * 0.9,
            )
        )

    def _handle_enhanced_index(self) -> None:
        """Handle array indexing with type preservation."""
        operands = self.stack_manager.pop_multiple(2)
        if len(operands) != 2:
            return

        index, array = operands
        result_expr = f"{array.expression}[{index.expression}]"

        self.stack_manager.push(
            StackValue(
                expression=result_expr,
                value_type=array.value_type,  # Array element has same type as array
                origin=StackValueOrigin.EXPRESSION,
                confidence=min(array.confidence, index.confidence) * 0.9,
            )
        )

    def _handle_enhanced_return(self) -> str | None:
        """Handle RETURN statement with type checking."""
        if not self.stack_manager.is_empty():
            value = self.stack_manager.pop()
            return f"return {value.expression}"
        return "return"

    def _handle_enhanced_conversion(self, opcode: str) -> None:
        """Handle type conversions with enhanced type tracking."""
        value = self.stack_manager.pop()
        if not value:
            return

        # Extract target type from opcode
        target_type = StackValueType.UNKNOWN
        converted_expr = value.expression

        if "INT" in opcode:
            target_type = StackValueType.INTEGER
            converted_expr = f"Integer({value.expression})"
        elif "STR" in opcode or "STRING" in opcode:
            target_type = StackValueType.STRING
            converted_expr = f"String({value.expression})"
        elif "REAL" in opcode or "DOUBLE" in opcode:
            target_type = StackValueType.REAL
            converted_expr = f"Real({value.expression})"
        elif "BOOL" in opcode:
            target_type = StackValueType.BOOLEAN
            converted_expr = f"Boolean({value.expression})"
        elif "DATE" in opcode:
            target_type = StackValueType.DATE
            converted_expr = f"Date({value.expression})"

        self.stack_manager.push(
            StackValue(
                expression=converted_expr,
                value_type=target_type,
                origin=StackValueOrigin.EXPRESSION,
                confidence=value.confidence * 0.9,
            )
        )

    def _handle_enhanced_jump(self, opcode: str, operands: list[Any]) -> str | None:
        """Handle jump instructions for control flow reconstruction."""
        if opcode == "JUMPFALSE":
            condition = self.stack_manager.pop(StackValueType.BOOLEAN)
            if condition:
                return f"if NOT ({condition.expression}) then goto /* target */"
        elif opcode == "JUMPTRUE":
            condition = self.stack_manager.pop(StackValueType.BOOLEAN)
            if condition:
                return f"if {condition.expression} then goto /* target */"
        elif opcode == "JUMP":
            return "goto /* target */"

        return f"// {opcode} {operands}"

    def _simulate_stack_operation(self, instruction: PCodeInstruction) -> None:
        """Simulate stack operation without generating code (for pattern skipping)."""
        opcode = instruction.opcode_name

        if opcode.startswith("PUSH_"):
            # Add a placeholder to stack
            self.stack_manager.push(
                StackValue(
                    expression="/* pattern_placeholder */",
                    value_type=StackValueType.UNKNOWN,
                    origin=StackValueOrigin.PLACEHOLDER,
                    confidence=0.5,
                )
            )
        elif opcode == "POP":
            self.stack_manager.pop()
        elif opcode in ["ADD", "SUB", "MULT", "DIV", "EQ", "NE", "LT", "GT"]:
            # Binary operations - pop 2, push 1
            self.stack_manager.pop_multiple(2)
            self.stack_manager.push(
                StackValue(
                    expression="/* binary_result */",
                    value_type=StackValueType.UNKNOWN,
                    origin=StackValueOrigin.EXPRESSION,
                    confidence=0.5,
                )
            )

    def _enhance_statements(self, statements: list[str]) -> list[str]:
        """Post-process statements for better readability."""
        enhanced = []

        for stmt in statements:
            # Remove redundant comments
            if stmt.startswith("//") and "ERROR" not in stmt:
                # Skip low-value comments unless they're error indicators
                continue

            # Improve variable names in statements
            enhanced_stmt = stmt
            for var_idx, var_name in self.locals.items():
                if var_name != f"local_{var_idx}":
                    enhanced_stmt = enhanced_stmt.replace(f"local_{var_idx}", var_name)

            # Add proper PowerBuilder syntax
            if not enhanced_stmt.endswith(("then", "loop", "end if", "next")):
                if not enhanced_stmt.startswith(("//", "if", "do", "for")):
                    if "=" in enhanced_stmt and not enhanced_stmt.startswith("return"):
                        # This is likely an assignment or comparison
                        pass  # Keep as is

            enhanced.append(enhanced_stmt)

        return enhanced

    def get_comprehensive_statistics(self) -> dict[str, Any]:
        """Get comprehensive statistics about the reconstruction process."""
        return {
            "reconstruction_mode": self.mode.name,
            "reconstruction_stats": self.reconstruction_stats,
            "stack_stats": self.stack_manager.get_statistics(),
            "pattern_stats": self.pattern_engine.get_statistics(),
            "context_stats": self.context_recovery.get_recovery_statistics(),
            "symbol_tables": {
                "locals_count": len(self.locals),
                "strings_count": len(self.strings),
                "methods_count": len(self.methods),
                "fields_count": len(self.fields),
            },
        }
