"""Pattern recognition engine for PowerBuilder idioms and common constructs.

This module provides sophisticated pattern matching capabilities to recognize
common PowerBuilder programming idioms, control structures, and API patterns.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from src.decompile.pcode.decoder import PCodeInstruction

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be recognized."""

    CONTROL_FLOW = auto()  # if/else, loops, try/catch
    FUNCTION_CALL = auto()  # Method calls, API calls
    ASSIGNMENT = auto()  # Variable assignments
    COMPARISON = auto()  # Comparison operations
    ARITHMETIC = auto()  # Math operations
    STRING_OPERATION = auto()  # String manipulation
    OBJECT_ACCESS = auto()  # Object field/method access
    ARRAY_ACCESS = auto()  # Array indexing
    TYPE_CONVERSION = auto()  # Type casting
    DATABASE = auto()  # SQL operations
    UI_EVENT = auto()  # UI event handling
    POWERBUILDER_API = auto()  # PB-specific API calls


@dataclass
class PatternTemplate:
    """Template for matching instruction patterns."""

    name: str
    pattern_type: PatternType
    opcodes: list[str]  # Sequence of opcodes to match
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    generator: Callable | None = None  # Function to generate code

    def matches(self, instructions: list[PCodeInstruction], start_idx: int) -> bool:
        """Check if pattern matches at given position."""
        if start_idx + len(self.opcodes) > len(instructions):
            return False

        for i, expected_opcode in enumerate(self.opcodes):
            actual_opcode = instructions[start_idx + i].opcode_name
            if not self._opcode_matches(actual_opcode, expected_opcode):
                return False

        return True

    def _opcode_matches(self, actual: str, expected: str) -> bool:
        """Check if actual opcode matches expected (with wildcards)."""
        if expected == "*":  # Wildcard
            return True
        if expected.startswith("PUSH_"):  # Any push operation
            return actual.startswith("PUSH_")
        if expected.endswith("*"):  # Prefix match
            return actual.startswith(expected[:-1])
        return actual == expected


@dataclass
class PatternMatch:
    """A matched pattern with context."""

    template: PatternTemplate
    start_offset: int
    end_offset: int
    instructions: list[PCodeInstruction]
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


class PowerBuilderPatternLibrary:
    """Library of common PowerBuilder programming patterns."""

    def __init__(self) -> None:
        """Initialize the pattern library."""
        self.templates: list[PatternTemplate] = []
        self._build_standard_patterns()

    def _build_standard_patterns(self) -> None:
        """Build the standard set of PowerBuilder patterns."""
        # Control flow patterns
        self._add_control_flow_patterns()

        # Function call patterns
        self._add_function_call_patterns()

        # Assignment patterns
        self._add_assignment_patterns()

        # Comparison patterns
        self._add_comparison_patterns()

        # PowerBuilder API patterns
        self._add_powerbuilder_api_patterns()

        # Database patterns
        self._add_database_patterns()

        # UI patterns
        self._add_ui_patterns()

    def _add_control_flow_patterns(self) -> None:
        """Add control flow patterns."""
        # Simple if statement
        self.templates.append(
            PatternTemplate(
                name="if_statement",
                pattern_type=PatternType.CONTROL_FLOW,
                opcodes=["*", "JUMPFALSE"],
                confidence=0.9,
                generator=self._generate_if_statement,
            )
        )

        # Simple if-else
        self.templates.append(
            PatternTemplate(
                name="if_else_statement",
                pattern_type=PatternType.CONTROL_FLOW,
                opcodes=["*", "JUMPFALSE", "*", "JUMP"],
                confidence=0.95,
                generator=self._generate_if_else_statement,
            )
        )

        # While loop
        self.templates.append(
            PatternTemplate(
                name="while_loop",
                pattern_type=PatternType.CONTROL_FLOW,
                opcodes=["*", "JUMPFALSE", "*", "JUMP"],
                confidence=0.8,
                metadata={"loop_type": "while"},
                generator=self._generate_while_loop,
            )
        )

        # For loop (typical pattern)
        self.templates.append(
            PatternTemplate(
                name="for_loop",
                pattern_type=PatternType.CONTROL_FLOW,
                opcodes=[
                    "PUSH_CONST_INT",
                    "STORE_LOCAL_VAR",
                    "*",
                    "PUSH_LOCAL_VAR",
                    "*",
                    "LT",
                    "JUMPFALSE",
                ],
                confidence=0.85,
                metadata={"loop_type": "for"},
                generator=self._generate_for_loop,
            )
        )

    def _add_function_call_patterns(self) -> None:
        """Add function call patterns."""
        # Simple function call
        self.templates.append(
            PatternTemplate(
                name="function_call",
                pattern_type=PatternType.FUNCTION_CALL,
                opcodes=["PUSH_*", "CALL_FUNC"],
                confidence=0.9,
                generator=self._generate_function_call,
            )
        )

        # Method call with object
        self.templates.append(
            PatternTemplate(
                name="method_call",
                pattern_type=PatternType.FUNCTION_CALL,
                opcodes=["PUSH_*", "DOT", "CALL_FUNC"],
                confidence=0.95,
                generator=self._generate_method_call,
            )
        )

        # MessageBox pattern
        self.templates.append(
            PatternTemplate(
                name="messagebox",
                pattern_type=PatternType.POWERBUILDER_API,
                opcodes=["PUSH_CONST_STRING", "PUSH_CONST_STRING", "MESSAGEBOX"],
                confidence=0.98,
                generator=self._generate_messagebox,
            )
        )

    def _add_assignment_patterns(self) -> None:
        """Add assignment patterns."""
        # Simple variable assignment
        self.templates.append(
            PatternTemplate(
                name="variable_assignment",
                pattern_type=PatternType.ASSIGNMENT,
                opcodes=["PUSH_*", "STORE_LOCAL_VAR"],
                confidence=0.95,
                generator=self._generate_variable_assignment,
            )
        )

        # Field assignment
        self.templates.append(
            PatternTemplate(
                name="field_assignment",
                pattern_type=PatternType.ASSIGNMENT,
                opcodes=["PUSH_*", "PUSH_THIS", "DOT", "STORE"],
                confidence=0.9,
                generator=self._generate_field_assignment,
            )
        )

    def _add_comparison_patterns(self) -> None:
        """Add comparison patterns."""
        # Equality check
        self.templates.append(
            PatternTemplate(
                name="equality_check",
                pattern_type=PatternType.COMPARISON,
                opcodes=["PUSH_*", "PUSH_*", "EQ"],
                confidence=0.9,
                generator=self._generate_equality_check,
            )
        )

        # IsNull check
        self.templates.append(
            PatternTemplate(
                name="isnull_check",
                pattern_type=PatternType.COMPARISON,
                opcodes=["PUSH_*", "ISNULL"],
                confidence=0.95,
                generator=self._generate_isnull_check,
            )
        )

    def _add_powerbuilder_api_patterns(self) -> None:
        """Add PowerBuilder-specific API patterns."""
        # SetText pattern
        self.templates.append(
            PatternTemplate(
                name="settext",
                pattern_type=PatternType.POWERBUILDER_API,
                opcodes=["PUSH_CONST_STRING", "PUSH_*", "DOT", "SETTEXT"],
                confidence=0.95,
                generator=self._generate_settext,
            )
        )

        # GetText pattern
        self.templates.append(
            PatternTemplate(
                name="gettext",
                pattern_type=PatternType.POWERBUILDER_API,
                opcodes=["PUSH_*", "DOT", "GETTEXT"],
                confidence=0.95,
                generator=self._generate_gettext,
            )
        )

        # Visible property
        self.templates.append(
            PatternTemplate(
                name="set_visible",
                pattern_type=PatternType.POWERBUILDER_API,
                opcodes=["PUSH_CONST_BOOL", "PUSH_*", "DOT", "SETVISIBLE"],
                confidence=0.9,
                generator=self._generate_set_visible,
            )
        )

    def _add_database_patterns(self) -> None:
        """Add database operation patterns."""
        # SQL Execute
        self.templates.append(
            PatternTemplate(
                name="sql_execute",
                pattern_type=PatternType.DATABASE,
                opcodes=["PUSH_CONST_STRING", "EXECUTE"],
                confidence=0.95,
                generator=self._generate_sql_execute,
            )
        )

        # DataWindow Retrieve
        self.templates.append(
            PatternTemplate(
                name="datawindow_retrieve",
                pattern_type=PatternType.DATABASE,
                opcodes=["PUSH_*", "DOT", "RETRIEVE"],
                confidence=0.9,
                generator=self._generate_datawindow_retrieve,
            )
        )

    def _add_ui_patterns(self) -> None:
        """Add UI-related patterns."""
        # Open window
        self.templates.append(
            PatternTemplate(
                name="open_window",
                pattern_type=PatternType.UI_EVENT,
                opcodes=["PUSH_*", "OPEN"],
                confidence=0.9,
                generator=self._generate_open_window,
            )
        )

        # Close window
        self.templates.append(
            PatternTemplate(
                name="close_window",
                pattern_type=PatternType.UI_EVENT,
                opcodes=["PUSH_THIS", "CLOSE"],
                confidence=0.95,
                generator=self._generate_close_window,
            )
        )

    # Pattern generators
    def _generate_if_statement(self, match: PatternMatch) -> str:
        """Generate if statement code."""
        condition_instr = match.instructions[0]
        return f"if {condition_instr.operands[0] if condition_instr.operands else 'condition'} then"

    def _generate_if_else_statement(self, match: PatternMatch) -> str:
        """Generate if-else statement code."""
        condition_instr = match.instructions[0]
        return f"if {condition_instr.operands[0] if condition_instr.operands else 'condition'} then\nelse\nend if"

    def _generate_while_loop(self, match: PatternMatch) -> str:
        """Generate while loop code."""
        condition_instr = match.instructions[0]
        return f"do while {condition_instr.operands[0] if condition_instr.operands else 'condition'}\nloop"

    def _generate_for_loop(self, match: PatternMatch) -> str:
        """Generate for loop code."""
        start_val = (
            match.instructions[0].operands[0] if match.instructions[0].operands else 1
        )
        (match.instructions[1].operands[0] if match.instructions[1].operands else 0)
        return f"for i = {start_val} to /* end_value */\nnext"

    def _generate_function_call(self, match: PatternMatch) -> str:
        """Generate function call code."""
        call_instr = match.instructions[-1]
        func_name = (
            f"function_{call_instr.operands[0]}"
            if call_instr.operands
            else "unknown_function"
        )
        return f"{func_name}()"

    def _generate_method_call(self, match: PatternMatch) -> str:
        """Generate method call code."""
        dot_instr = match.instructions[-2]
        match.instructions[-1]
        method_name = (
            f"method_{dot_instr.operands[0]}"
            if dot_instr.operands
            else "unknown_method"
        )
        return f"object.{method_name}()"

    def _generate_messagebox(self, match: PatternMatch) -> str:
        """Generate MessageBox call."""
        return "MessageBox(title, message)"

    def _generate_variable_assignment(self, match: PatternMatch) -> str:
        """Generate variable assignment."""
        store_instr = match.instructions[-1]
        var_idx = store_instr.operands[0] if store_instr.operands else 0
        return f"local_{var_idx} = value"

    def _generate_field_assignment(self, match: PatternMatch) -> str:
        """Generate field assignment."""
        dot_instr = match.instructions[-2]
        field_name = (
            f"field_{dot_instr.operands[0]}" if dot_instr.operands else "unknown_field"
        )
        return f"this.{field_name} = value"

    def _generate_equality_check(self, match: PatternMatch) -> str:
        """Generate equality check."""
        return "value1 = value2"

    def _generate_isnull_check(self, match: PatternMatch) -> str:
        """Generate IsNull check."""
        return "IsNull(value)"

    def _generate_settext(self, match: PatternMatch) -> str:
        """Generate SetText call."""
        return "control.text = string_value"

    def _generate_gettext(self, match: PatternMatch) -> str:
        """Generate GetText call."""
        return "value = control.text"

    def _generate_set_visible(self, match: PatternMatch) -> str:
        """Generate set visible call."""
        bool_val = (
            match.instructions[0].operands[0]
            if match.instructions[0].operands
            else True
        )
        return f"control.visible = {'true' if bool_val else 'false'}"

    def _generate_sql_execute(self, match: PatternMatch) -> str:
        """Generate SQL execute."""
        return "EXECUTE IMMEDIATE sql_statement"

    def _generate_datawindow_retrieve(self, match: PatternMatch) -> str:
        """Generate DataWindow retrieve."""
        return "dw_control.Retrieve()"

    def _generate_open_window(self, match: PatternMatch) -> str:
        """Generate open window."""
        return "Open(window_name)"

    def _generate_close_window(self, match: PatternMatch) -> str:
        """Generate close window."""
        return "Close(this)"


class PatternRecognitionEngine:
    """Engine for recognizing patterns in P-code instruction sequences."""

    def __init__(self) -> None:
        """Initialize the pattern recognition engine."""
        self.library = PowerBuilderPatternLibrary()
        self.matches: list[PatternMatch] = []
        self.recognition_stats = {
            "total_patterns": len(self.library.templates),
            "matches_found": 0,
            "high_confidence_matches": 0,
        }

    def analyze_instructions(
        self, instructions: list[PCodeInstruction]
    ) -> list[PatternMatch]:
        """Analyze instruction sequence and find pattern matches."""
        self.matches.clear()

        for i in range(len(instructions)):
            for template in self.library.templates:
                if template.matches(instructions, i):
                    match = PatternMatch(
                        template=template,
                        start_offset=instructions[i].offset,
                        end_offset=instructions[
                            min(i + len(template.opcodes) - 1, len(instructions) - 1)
                        ].offset,
                        instructions=instructions[i : i + len(template.opcodes)],
                        confidence=template.confidence,
                    )
                    self.matches.append(match)

                    if template.confidence >= 0.9:
                        self.recognition_stats["high_confidence_matches"] += 1

        self.recognition_stats["matches_found"] = len(self.matches)

        # Sort matches by confidence and position
        self.matches.sort(key=lambda m: (-m.confidence, m.start_offset))

        logger.info(
            "Pattern analysis complete: found %d matches (%d high confidence)",
            len(self.matches),
            self.recognition_stats["high_confidence_matches"],
        )

        return self.matches

    def get_best_matches(self, min_confidence: float = 0.8) -> list[PatternMatch]:
        """Get matches above a confidence threshold."""
        return [m for m in self.matches if m.confidence >= min_confidence]

    def get_matches_by_type(self, pattern_type: PatternType) -> list[PatternMatch]:
        """Get all matches of a specific pattern type."""
        return [m for m in self.matches if m.template.pattern_type == pattern_type]

    def generate_code_for_match(self, match: PatternMatch) -> str | None:
        """Generate PowerBuilder code for a pattern match."""
        if match.template.generator:
            try:
                return match.template.generator(match)
            except Exception as e:
                logger.warning(
                    "Failed to generate code for pattern %s: %s",
                    match.template.name,
                    e,
                )

        # Fallback - use template name as comment
        return f"// {match.template.name} pattern (confidence: {match.confidence:.2f})"

    def get_statistics(self) -> dict[str, Any]:
        """Get pattern recognition statistics."""
        pattern_type_counts = {}
        for match in self.matches:
            ptype = match.template.pattern_type.name
            pattern_type_counts[ptype] = pattern_type_counts.get(ptype, 0) + 1

        return {
            **self.recognition_stats,
            "pattern_type_distribution": pattern_type_counts,
            "average_confidence": sum(m.confidence for m in self.matches)
            / len(self.matches)
            if self.matches
            else 0,
        }
