"""Enhanced output generation with rich PowerBuilder syntax and confidence scoring.

This module provides sophisticated output formatting capabilities that generate
high-quality PowerBuilder source code with proper indentation, documentation,
and confidence indicators.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class OutputStyle(Enum):
    """Output formatting styles."""

    COMPACT = auto()  # Minimal formatting
    STANDARD = auto()  # Standard PowerBuilder formatting
    DOCUMENTED = auto()  # Includes documentation comments
    DEBUG = auto()  # Includes debug information


class ConfidenceLevel(Enum):
    """Confidence levels for generated code."""

    VERY_LOW = auto()  # 0.0 - 0.2
    LOW = auto()  # 0.2 - 0.4
    MEDIUM = auto()  # 0.4 - 0.7
    HIGH = auto()  # 0.7 - 0.9
    VERY_HIGH = auto()  # 0.9 - 1.0


@dataclass
class FormattedStatement:
    """A formatted statement with metadata."""

    code: str
    confidence: float
    indentation_level: int = 0
    is_comment: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_confidence_level(self) -> ConfidenceLevel:
        """Get confidence level enum."""
        if self.confidence < 0.2:
            return ConfidenceLevel.VERY_LOW
        if self.confidence < 0.4:
            return ConfidenceLevel.LOW
        if self.confidence < 0.7:
            return ConfidenceLevel.MEDIUM
        if self.confidence < 0.9:
            return ConfidenceLevel.HIGH
        return ConfidenceLevel.VERY_HIGH


class PowerBuilderOutputFormatter:
    """Enhanced formatter for PowerBuilder source code output."""

    def __init__(self, style: OutputStyle = OutputStyle.STANDARD) -> None:
        """Initialize the output formatter.

        Args:
            style: Output formatting style
        """
        self.style = style
        self.indentation_size = 4
        self.current_indent = 0
        self.line_width = 120

        # PowerBuilder syntax patterns
        self.pb_keywords = {
            "if",
            "then",
            "else",
            "elseif",
            "end if",
            "choose",
            "case",
            "end choose",
            "for",
            "to",
            "step",
            "next",
            "do",
            "while",
            "loop",
            "exit",
            "continue",
            "try",
            "catch",
            "finally",
            "end try",
            "throw",
            "function",
            "subroutine",
            "event",
            "on",
            "end function",
            "end subroutine",
            "end event",
            "end on",
            "private",
            "public",
            "protected",
            "global",
            "shared",
            "readonly",
            "constant",
            "ref",
            "by value",
            "by reference",
            "return",
            "call",
            "post",
            "trigger",
            "open",
            "close",
            "create",
            "destroy",
            "using",
            "destroy using",
            "and",
            "or",
            "not",
            "true",
            "false",
            "null",
        }

        # Control structure patterns
        self.control_patterns = {
            "if_start": re.compile(r"^\s*if\s+.*\s+then\s*$", re.IGNORECASE),
            "if_end": re.compile(r"^\s*end\s+if\s*$", re.IGNORECASE),
            "else": re.compile(r"^\s*else\s*$", re.IGNORECASE),
            "elseif": re.compile(r"^\s*elseif\s+.*\s+then\s*$", re.IGNORECASE),
            "for_start": re.compile(r"^\s*for\s+\w+\s*=.*\s+to\s+.*$", re.IGNORECASE),
            "for_end": re.compile(r"^\s*next\s*$", re.IGNORECASE),
            "while_start": re.compile(r"^\s*do\s+while\s+.*$", re.IGNORECASE),
            "while_end": re.compile(r"^\s*loop\s*$", re.IGNORECASE),
            "function_start": re.compile(
                r"^\s*(public|private|protected)?\s*(function|subroutine)\s+\w+",
                re.IGNORECASE,
            ),
            "function_end": re.compile(
                r"^\s*end\s+(function|subroutine)\s*$", re.IGNORECASE
            ),
        }

    def format_statements(
        self, statements: list[str], confidences: list[float] | None = None
    ) -> str:
        """Format a list of statements into proper PowerBuilder code.

        Args:
            statements: List of statement strings
            confidences: Optional confidence scores for each statement

        Returns:
            Formatted PowerBuilder source code
        """
        if not statements:
            return ""

        # Create formatted statements
        formatted_statements = []
        for i, stmt in enumerate(statements):
            confidence = confidences[i] if confidences and i < len(confidences) else 0.8

            formatted_stmt = FormattedStatement(
                code=stmt,
                confidence=confidence,
                is_comment=stmt.strip().startswith("//"),
            )
            formatted_statements.append(formatted_stmt)

        # Apply formatting rules
        self.current_indent = 0
        formatted_lines = []

        for stmt in formatted_statements:
            formatted_line = self._format_statement(stmt)
            if formatted_line:
                formatted_lines.append(formatted_line)

        # Join lines and apply final formatting
        result = "\n".join(formatted_lines)

        # Apply style-specific post-processing
        if self.style == OutputStyle.DOCUMENTED:
            result = self._add_documentation(result, formatted_statements)
        elif self.style == OutputStyle.DEBUG:
            result = self._add_debug_info(result, formatted_statements)

        return result

    def _format_statement(self, stmt: FormattedStatement) -> str:
        """Format a single statement with proper indentation and syntax."""
        code = stmt.code.strip()
        if not code:
            return ""

        # Skip empty comments unless in debug mode
        if stmt.is_comment and self.style != OutputStyle.DEBUG:
            if code == "//" or "ERROR" not in code:
                return ""

        # Determine indentation changes
        indent_change = self._calculate_indent_change(code)

        # Apply indentation before the statement for end constructs
        if self._is_end_construct(code):
            self.current_indent = max(0, self.current_indent - 1)

        # Format the line
        indent_str = " " * (self.current_indent * self.indentation_size)
        formatted_line = f"{indent_str}{code}"

        # Apply indentation after the statement for start constructs
        if self._is_start_construct(code):
            self.current_indent += 1

        # Add confidence indicator if needed
        if self.style == OutputStyle.DEBUG:
            confidence_indicator = self._get_confidence_indicator(stmt.confidence)
            formatted_line += f"  {confidence_indicator}"
        elif self.style == OutputStyle.DOCUMENTED and stmt.confidence < 0.5:
            formatted_line += "  // Low confidence"

        # Handle line wrapping if needed
        if len(formatted_line) > self.line_width and self.style != OutputStyle.COMPACT:
            formatted_line = self._wrap_line(formatted_line, indent_str)

        return formatted_line

    def _calculate_indent_change(self, code: str) -> int:
        """Calculate indentation change for a statement."""
        code_lower = code.lower().strip()

        # Start constructs increase indentation
        if any(
            pattern.match(code)
            for pattern in [
                self.control_patterns["if_start"],
                self.control_patterns["for_start"],
                self.control_patterns["while_start"],
                self.control_patterns["function_start"],
            ]
        ):
            return 1

        # End constructs decrease indentation
        if any(
            pattern.match(code)
            for pattern in [
                self.control_patterns["if_end"],
                self.control_patterns["for_end"],
                self.control_patterns["while_end"],
                self.control_patterns["function_end"],
            ]
        ):
            return -1

        # Special cases
        if self.control_patterns["else"].match(code) or self.control_patterns[
            "elseif"
        ].match(code):
            return 0  # Same level as if

        return 0

    def _is_start_construct(self, code: str) -> bool:
        """Check if statement is a control structure start."""
        return any(
            pattern.match(code)
            for pattern in [
                self.control_patterns["if_start"],
                self.control_patterns["for_start"],
                self.control_patterns["while_start"],
                self.control_patterns["function_start"],
            ]
        )

    def _is_end_construct(self, code: str) -> bool:
        """Check if statement is a control structure end."""
        return any(
            pattern.match(code)
            for pattern in [
                self.control_patterns["if_end"],
                self.control_patterns["for_end"],
                self.control_patterns["while_end"],
                self.control_patterns["function_end"],
            ]
        ) or self.control_patterns["else"].match(code)

    def _get_confidence_indicator(self, confidence: float) -> str:
        """Get confidence indicator string."""
        if confidence >= 0.9:
            return "✓✓✓"
        if confidence >= 0.7:
            return "✓✓ "
        if confidence >= 0.5:
            return "✓  "
        if confidence >= 0.3:
            return "?  "
        return "!! "

    def _wrap_line(self, line: str, indent_str: str) -> str:
        """Wrap long lines for better readability."""
        if len(line) <= self.line_width:
            return line

        # Try to break at logical points
        break_points = [" and ", " or ", ", ", " = ", " + ", " - ", " * ", " / "]

        for break_point in break_points:
            if break_point in line:
                parts = line.split(break_point, 1)
                if len(parts) == 2:
                    first_part = parts[0]
                    second_part = parts[1]

                    if len(first_part) < self.line_width - 20:  # Leave some margin
                        continuation_indent = (
                            indent_str + "    "
                        )  # Extra indent for continuation
                        return f"{first_part}{break_point}\n{continuation_indent}{second_part.strip()}"

        # If no good break point, just return as is
        return line

    def _add_documentation(
        self, code: str, statements: list[FormattedStatement]
    ) -> str:
        """Add documentation comments for better understanding."""
        lines = code.split("\n")
        documented_lines = []

        # Add header comment
        documented_lines.append("// Generated PowerBuilder code")
        documented_lines.append(
            "// Confidence levels: ✓✓✓ High, ✓✓ Medium, ✓ Low, ? Very Low"
        )
        documented_lines.append("")

        # Process each line
        for i, line in enumerate(lines):
            documented_lines.append(line)

            # Add explanatory comments for complex constructs
            if i < len(statements):
                stmt = statements[i]
                if stmt.confidence < 0.5 and not stmt.is_comment:
                    documented_lines.append(
                        "    // Note: Low confidence reconstruction"
                    )

        # Add footer with statistics
        total_statements = len([s for s in statements if not s.is_comment])
        high_confidence = len(
            [s for s in statements if s.confidence >= 0.7 and not s.is_comment]
        )

        documented_lines.append("")
        documented_lines.append(
            f"// Reconstruction summary: {high_confidence}/{total_statements} statements with high confidence"
        )

        return "\n".join(documented_lines)

    def _add_debug_info(self, code: str, statements: list[FormattedStatement]) -> str:
        """Add debug information for development purposes."""
        lines = code.split("\n")
        debug_lines = []

        # Add debug header
        debug_lines.append("/* DEBUG MODE - Enhanced P-code Reconstruction */")
        debug_lines.append(
            "/* Confidence Legend: ✓✓✓=High, ✓✓=Medium, ✓=Low, ?=Very Low, !!=Error */"
        )
        debug_lines.append("")

        # Add detailed statistics
        if statements:
            total = len(statements)
            comments = len([s for s in statements if s.is_comment])
            code_statements = total - comments

            confidence_dist = {
                "very_high": len([s for s in statements if s.confidence >= 0.9]),
                "high": len([s for s in statements if 0.7 <= s.confidence < 0.9]),
                "medium": len([s for s in statements if 0.4 <= s.confidence < 0.7]),
                "low": len([s for s in statements if 0.2 <= s.confidence < 0.4]),
                "very_low": len([s for s in statements if s.confidence < 0.2]),
            }

            debug_lines.append(
                f"/* Statistics: {code_statements} code statements, {comments} comments */"
            )
            debug_lines.append(
                f"/* Confidence: {confidence_dist['very_high']} very high, "
                f"{confidence_dist['high']} high, {confidence_dist['medium']} medium, "
                f"{confidence_dist['low']} low, {confidence_dist['very_low']} very low */"
            )
            debug_lines.append("")

        # Add the code
        debug_lines.extend(lines)

        debug_lines.append("")
        debug_lines.append("/* End of reconstructed code */")

        return "\n".join(debug_lines)

    def format_method_signature(
        self,
        method_name: str,
        return_type: str | None = None,
        parameters: list[tuple[str, str]] | None = None,
        access_modifier: str = "public",
    ) -> str:
        """Format a PowerBuilder method signature.

        Args:
            method_name: Name of the method
            return_type: Return type (None for subroutine)
            parameters: List of (name, type) tuples
            access_modifier: Access modifier

        Returns:
            Formatted method signature
        """
        signature_parts = [access_modifier]

        if return_type:
            signature_parts.extend(["function", return_type, method_name])
        else:
            signature_parts.extend(["subroutine", method_name])

        signature = " ".join(signature_parts)

        if parameters:
            param_strs = []
            for param_name, param_type in parameters:
                param_strs.append(f"{param_type} {param_name}")
            signature += f"({', '.join(param_strs)})"
        else:
            signature += "()"

        return signature

    def format_variable_declaration(
        self,
        var_name: str,
        var_type: str,
        initial_value: str | None = None,
        access_modifier: str | None = None,
    ) -> str:
        """Format a PowerBuilder variable declaration.

        Args:
            var_name: Variable name
            var_type: Variable type
            initial_value: Initial value if any
            access_modifier: Access modifier if any

        Returns:
            Formatted variable declaration
        """
        parts = []

        if access_modifier:
            parts.append(access_modifier)

        parts.extend([var_type, var_name])

        declaration = " ".join(parts)

        if initial_value:
            declaration += f" = {initial_value}"

        return declaration

    def get_formatting_statistics(self) -> dict[str, Any]:
        """Get formatting statistics."""
        return {
            "style": self.style.name,
            "indentation_size": self.indentation_size,
            "line_width": self.line_width,
            "current_indent": self.current_indent,
        }
