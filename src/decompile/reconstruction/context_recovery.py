"""Context recovery system for missing operands and type inference.

This module provides sophisticated context analysis and recovery capabilities
to handle missing stack values, infer types, and reconstruct control flow.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from src.decompile.pcode.decoder import PCodeInstruction

from .enhanced_stack import StackValue, StackValueOrigin, StackValueType

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context that can be analyzed."""

    VARIABLE = auto()  # Variable usage context
    METHOD = auto()  # Method call context
    FIELD = auto()  # Field access context
    CONTROL_FLOW = auto()  # Control flow context
    TYPE = auto()  # Type information context
    SCOPE = auto()  # Scope/visibility context


@dataclass
class VariableInfo:
    """Information about a variable."""

    name: str
    inferred_type: StackValueType = StackValueType.UNKNOWN
    first_seen: int = -1  # Offset where first encountered
    assignments: list[int] = field(default_factory=list)  # Assignment offsets
    usages: list[int] = field(default_factory=list)  # Usage offsets
    is_parameter: bool = False
    is_return_value: bool = False
    confidence: float = 0.5


@dataclass
class MethodInfo:
    """Information about a method."""

    name: str
    return_type: StackValueType = StackValueType.UNKNOWN
    parameter_types: list[StackValueType] = field(default_factory=list)
    parameter_count: int = 0
    is_void: bool = False
    call_sites: list[int] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class ControlFlowInfo:
    """Information about control flow structures."""

    type: str  # if, while, for, try, etc.
    start_offset: int
    end_offset: int = -1
    condition_type: StackValueType = StackValueType.BOOLEAN
    nested_level: int = 0
    has_else: bool = False


class TypeInferenceEngine:
    """Engine for inferring types from context and usage patterns."""

    def __init__(self) -> None:
        """Initialize the type inference engine."""
        self.variable_contexts: dict[int, VariableInfo] = {}
        self.method_contexts: dict[int, MethodInfo] = {}
        self.string_contexts: dict[int, str] = {}
        self.field_contexts: dict[int, str] = {}

        # PowerBuilder type inference rules
        self.pb_type_patterns = {
            # Common PowerBuilder types based on names
            re.compile(
                r".*_str$|.*_string$|.*text.*", re.IGNORECASE
            ): StackValueType.STRING,
            re.compile(
                r".*_int$|.*_integer$|.*count.*|.*index.*", re.IGNORECASE
            ): StackValueType.INTEGER,
            re.compile(
                r".*_bool$|.*_boolean$|.*flag.*|is_.*", re.IGNORECASE
            ): StackValueType.BOOLEAN,
            re.compile(r".*_date$|.*_dt$|.*date.*", re.IGNORECASE): StackValueType.DATE,
            re.compile(r".*_time$|.*time.*", re.IGNORECASE): StackValueType.TIME,
            re.compile(
                r".*_real$|.*_double$|.*amount.*|.*price.*", re.IGNORECASE
            ): StackValueType.REAL,
        }

        # Common PowerBuilder method signatures
        self.pb_method_signatures = {
            "messagebox": MethodInfo(
                "MessageBox",
                StackValueType.INTEGER,
                [StackValueType.STRING, StackValueType.STRING],
                2,
            ),
            "isnull": MethodInfo(
                "IsNull", StackValueType.BOOLEAN, [StackValueType.UNKNOWN], 1
            ),
            "len": MethodInfo(
                "Len", StackValueType.INTEGER, [StackValueType.STRING], 1
            ),
            "mid": MethodInfo(
                "Mid",
                StackValueType.STRING,
                [StackValueType.STRING, StackValueType.INTEGER, StackValueType.INTEGER],
                3,
            ),
            "upper": MethodInfo(
                "Upper", StackValueType.STRING, [StackValueType.STRING], 1
            ),
            "lower": MethodInfo(
                "Lower", StackValueType.STRING, [StackValueType.STRING], 1
            ),
            "trim": MethodInfo(
                "Trim", StackValueType.STRING, [StackValueType.STRING], 1
            ),
            "string": MethodInfo(
                "String", StackValueType.STRING, [StackValueType.UNKNOWN], 1
            ),
            "integer": MethodInfo(
                "Integer", StackValueType.INTEGER, [StackValueType.UNKNOWN], 1
            ),
            "real": MethodInfo(
                "Real", StackValueType.REAL, [StackValueType.UNKNOWN], 1
            ),
            "date": MethodInfo(
                "Date", StackValueType.DATE, [StackValueType.UNKNOWN], 1
            ),
        }

    def analyze_variable_usage(
        self, var_idx: int, instructions: list[PCodeInstruction]
    ) -> VariableInfo:
        """Analyze variable usage patterns to infer type and purpose."""
        if var_idx in self.variable_contexts:
            return self.variable_contexts[var_idx]

        var_info = VariableInfo(name=f"local_{var_idx}")

        # Analyze all instructions that reference this variable
        for i, instr in enumerate(instructions):
            if self._instruction_references_variable(instr, var_idx):
                if var_info.first_seen == -1:
                    var_info.first_seen = instr.offset

                if instr.opcode_name.startswith(
                    "STORE"
                ) or instr.opcode_name.startswith("ASSIGN"):
                    var_info.assignments.append(instr.offset)
                else:
                    var_info.usages.append(instr.offset)

                # Infer type from context
                inferred_type = self._infer_type_from_instruction_context(
                    instr, instructions, i
                )
                if inferred_type != StackValueType.UNKNOWN:
                    if var_info.inferred_type == StackValueType.UNKNOWN:
                        var_info.inferred_type = inferred_type
                        var_info.confidence = 0.7
                    elif var_info.inferred_type == inferred_type:
                        var_info.confidence = min(1.0, var_info.confidence + 0.1)

        # Apply PowerBuilder naming conventions
        self._apply_naming_conventions(var_info)

        self.variable_contexts[var_idx] = var_info
        return var_info

    def infer_missing_operand_type(
        self, instruction: PCodeInstruction, operand_position: int
    ) -> StackValueType:
        """Infer the type of a missing operand based on instruction context."""
        opcode = instruction.opcode_name

        # Type inference based on opcodes
        type_patterns = {
            # Arithmetic operations typically work with numbers
            ("ADD", "SUB", "MULT", "DIV", "MOD"): StackValueType.INTEGER,
            ("ADD_REAL", "SUB_REAL", "MULT_REAL", "DIV_REAL"): StackValueType.REAL,
            # Comparison operations
            (
                "EQ",
                "NE",
                "LT",
                "GT",
                "LE",
                "GE",
            ): StackValueType.UNKNOWN,  # Could be any comparable type
            ("EQ_STR", "NE_STR"): StackValueType.STRING,
            ("EQ_INT", "NE_INT", "LT_INT", "GT_INT"): StackValueType.INTEGER,
            # Logical operations
            ("AND", "OR", "NOT"): StackValueType.BOOLEAN,
            # String operations
            ("CONCAT", "CONCAT_STR"): StackValueType.STRING,
            # Type conversions
            ("CNV_INT", "CAST_INT"): StackValueType.INTEGER,
            ("CNV_STR", "CAST_STR"): StackValueType.STRING,
            ("CNV_REAL", "CAST_REAL"): StackValueType.REAL,
            ("CNV_BOOL", "CAST_BOOL"): StackValueType.BOOLEAN,
        }

        # Check if opcode matches any pattern
        for opcodes, stack_type in type_patterns.items():
            if opcode in opcodes:
                return stack_type

        # Special cases based on opcode patterns
        if opcode.endswith("_INT"):
            return StackValueType.INTEGER
        if opcode.endswith("_STR"):
            return StackValueType.STRING
        if opcode.endswith("_REAL") or opcode.endswith("_DOUBLE"):
            return StackValueType.REAL
        if opcode.endswith("_BOOL") or opcode.endswith("_BOOLEAN"):
            return StackValueType.BOOLEAN

        # Method-specific inference
        if "CALL" in opcode:
            return self._infer_method_parameter_type(instruction, operand_position)

        return StackValueType.UNKNOWN

    def recover_variable_name(self, var_idx: int) -> str:
        """Recover or generate a meaningful variable name."""
        if var_idx in self.variable_contexts:
            var_info = self.variable_contexts[var_idx]
            if var_info.inferred_type != StackValueType.UNKNOWN:
                return self._generate_typed_variable_name(
                    var_idx, var_info.inferred_type
                )

        # Standard PowerBuilder variable patterns
        common_names = {
            0: "this",
            1: "return_value",
            2: "temp",
            3: "i",  # Common loop counter
            4: "j",  # Another loop counter
            5: "result",
            6: "value",
            7: "count",
            8: "index",
            9: "flag",
        }

        return common_names.get(var_idx, f"local_{var_idx}")

    def recover_method_name(self, method_idx: int) -> str:
        """Recover or generate a meaningful method name."""
        if method_idx in self.method_contexts:
            return self.method_contexts[method_idx].name

        # Common PowerBuilder methods
        common_methods = {
            0: "create",
            1: "destroy",
            2: "open",
            3: "close",
            4: "clicked",
            5: "constructor",
            6: "destructor",
            7: "post",
            8: "trigger",
            9: "event",
            10: "retrieve",
            11: "update",
            12: "insert",
            13: "delete",
        }

        return common_methods.get(method_idx, f"method_{method_idx}")

    def recover_field_name(self, field_idx: int) -> str:
        """Recover or generate a meaningful field name."""
        if field_idx in self.field_contexts:
            return self.field_contexts[field_idx]

        # Common PowerBuilder control properties
        common_fields = {
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
            10: "font",
            11: "border",
            12: "value",
            13: "checked",
            14: "selected",
        }

        return common_fields.get(field_idx, f"field_{field_idx}")

    def _instruction_references_variable(
        self, instruction: PCodeInstruction, var_idx: int
    ) -> bool:
        """Check if instruction references a specific variable."""
        if not instruction.operands:
            return False

        opcode = instruction.opcode_name

        # Variable reference opcodes
        var_opcodes = [
            "PUSH_LOCAL_VAR",
            "STORE_LOCAL_VAR",
            "ASSIGN_LOCAL_VAR",
            "PUSH_GLOBAL_VAR",
            "STORE_GLOBAL_VAR",
            "ASSIGN_GLOBAL_VAR",
        ]

        if opcode in var_opcodes and instruction.operands[0] == var_idx:
            return True

        return False

    def _infer_type_from_instruction_context(
        self,
        instruction: PCodeInstruction,
        all_instructions: list[PCodeInstruction],
        current_index: int,
    ) -> StackValueType:
        """Infer type from the instruction's context."""
        opcode = instruction.opcode_name

        # Look at surrounding instructions for context
        prev_instr = all_instructions[current_index - 1] if current_index > 0 else None
        next_instr = (
            all_instructions[current_index + 1]
            if current_index < len(all_instructions) - 1
            else None
        )

        # String operations context
        if opcode in ["CONCAT", "CONCAT_STR"] or (
            prev_instr and prev_instr.opcode_name == "PUSH_CONST_STRING"
        ):
            return StackValueType.STRING

        # Numeric operations context
        if opcode in ["ADD", "SUB", "MULT", "DIV"] or (
            prev_instr and prev_instr.opcode_name == "PUSH_CONST_INT"
        ):
            return StackValueType.INTEGER

        # Boolean operations context
        if opcode in ["AND", "OR", "NOT"] or (
            next_instr and next_instr.opcode_name in ["JUMPFALSE", "JUMPTRUE"]
        ):
            return StackValueType.BOOLEAN

        # Type conversion context
        if opcode.startswith("CNV_") or opcode.startswith("CAST_"):
            if "INT" in opcode:
                return StackValueType.INTEGER
            if "STR" in opcode:
                return StackValueType.STRING
            if "REAL" in opcode or "DOUBLE" in opcode:
                return StackValueType.REAL
            if "BOOL" in opcode:
                return StackValueType.BOOLEAN

        return StackValueType.UNKNOWN

    def _apply_naming_conventions(self, var_info: VariableInfo) -> None:
        """Apply PowerBuilder naming conventions to improve variable names."""
        # Apply type-based naming
        if var_info.inferred_type == StackValueType.STRING:
            var_info.name = var_info.name.replace("local_", "str_")
        elif var_info.inferred_type == StackValueType.INTEGER:
            var_info.name = var_info.name.replace("local_", "int_")
        elif var_info.inferred_type == StackValueType.BOOLEAN:
            var_info.name = var_info.name.replace("local_", "bool_")
        elif var_info.inferred_type == StackValueType.REAL:
            var_info.name = var_info.name.replace("local_", "real_")

    def _generate_typed_variable_name(
        self, var_idx: int, var_type: StackValueType
    ) -> str:
        """Generate a variable name based on its inferred type."""
        type_prefixes = {
            StackValueType.STRING: "str",
            StackValueType.INTEGER: "int",
            StackValueType.BOOLEAN: "bool",
            StackValueType.REAL: "real",
            StackValueType.DATE: "date",
            StackValueType.TIME: "time",
            StackValueType.DATETIME: "datetime",
        }

        prefix = type_prefixes.get(var_type, "var")
        return f"{prefix}_{var_idx}"

    def _infer_method_parameter_type(
        self, instruction: PCodeInstruction, param_position: int
    ) -> StackValueType:
        """Infer method parameter type based on known method signatures."""
        if not instruction.operands:
            return StackValueType.UNKNOWN

        method_idx = instruction.operands[0] if instruction.operands else -1
        method_name = self.recover_method_name(method_idx).lower()

        # Check known method signatures
        if method_name in self.pb_method_signatures:
            signature = self.pb_method_signatures[method_name]
            if param_position < len(signature.parameter_types):
                return signature.parameter_types[param_position]

        return StackValueType.UNKNOWN


class ContextRecoverySystem:
    """System for recovering missing context and operands."""

    def __init__(self) -> None:
        """Initialize the context recovery system."""
        self.type_engine = TypeInferenceEngine()
        self.control_flow_stack: list[ControlFlowInfo] = []
        self.recovered_values: dict[int, StackValue] = {}  # offset -> recovered value

    def recover_missing_operand(
        self,
        instruction: PCodeInstruction,
        operand_position: int,
        context_instructions: list[PCodeInstruction],
    ) -> StackValue:
        """Recover a missing operand using context analysis."""
        # Try type inference first
        inferred_type = self.type_engine.infer_missing_operand_type(
            instruction, operand_position
        )

        # Generate appropriate placeholder based on inferred type
        if inferred_type == StackValueType.STRING:
            expression = '""'  # Empty string default
        elif inferred_type == StackValueType.INTEGER:
            expression = "0"  # Zero default
        elif inferred_type == StackValueType.BOOLEAN:
            expression = "FALSE"  # Boolean false default
        elif inferred_type == StackValueType.REAL:
            expression = "0.0"  # Real zero default
        else:
            expression = f"/* missing_operand_{operand_position} */"

        recovered_value = StackValue(
            expression=expression,
            value_type=inferred_type,
            origin=StackValueOrigin.RECOVERED,
            confidence=0.3,  # Low confidence for recovered values
            source_offset=instruction.offset,
            metadata={
                "recovery_reason": "missing_operand",
                "instruction": instruction.opcode_name,
                "position": operand_position,
            },
        )

        self.recovered_values[instruction.offset] = recovered_value

        logger.info(
            "Recovered missing operand at offset 0x%04x: %s (type: %s, confidence: %.2f)",
            instruction.offset,
            expression,
            inferred_type.name,
            recovered_value.confidence,
        )

        return recovered_value

    def enhance_variable_names(
        self, instructions: list[PCodeInstruction]
    ) -> dict[int, str]:
        """Enhance variable names using context analysis."""
        enhanced_names = {}

        # Analyze each variable usage
        variable_indices = set()
        for instr in instructions:
            if (
                instr.opcode_name in ["PUSH_LOCAL_VAR", "STORE_LOCAL_VAR"]
                and instr.operands
            ):
                variable_indices.add(instr.operands[0])

        # Enhance names for each variable
        for var_idx in variable_indices:
            var_info = self.type_engine.analyze_variable_usage(var_idx, instructions)
            enhanced_names[var_idx] = var_info.name

        return enhanced_names

    def analyze_control_flow_context(
        self, instructions: list[PCodeInstruction]
    ) -> list[ControlFlowInfo]:
        """Analyze control flow structures to provide context for reconstruction."""
        control_structures = []
        jump_targets = {}

        # First pass: identify jump targets
        for instr in instructions:
            if (
                instr.opcode_name in ["JUMP", "JUMPTRUE", "JUMPFALSE"]
                and instr.operands
            ):
                target_offset = instr.offset + instr.operands[0]  # Relative jump
                jump_targets[target_offset] = jump_targets.get(target_offset, 0) + 1

        # Second pass: identify control structures
        for i, instr in enumerate(instructions):
            if instr.opcode_name == "JUMPFALSE":
                # Potential if statement or loop
                cf_info = ControlFlowInfo(
                    type="if_or_loop",
                    start_offset=instr.offset,
                    condition_type=StackValueType.BOOLEAN,
                )
                control_structures.append(cf_info)

            elif instr.opcode_name == "JUMP":
                # Potential else or loop continue
                cf_info = ControlFlowInfo(
                    type="jump",
                    start_offset=instr.offset,
                )
                control_structures.append(cf_info)

        return control_structures

    def get_recovery_statistics(self) -> dict[str, Any]:
        """Get statistics about context recovery operations."""
        return {
            "recovered_values_count": len(self.recovered_values),
            "variables_analyzed": len(self.type_engine.variable_contexts),
            "methods_identified": len(self.type_engine.method_contexts),
            "control_structures": len(self.control_flow_stack),
        }
