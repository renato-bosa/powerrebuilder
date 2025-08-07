"""Output format validator for decompiled PowerBuilder code.

This module validates that the formatted output follows PowerBuilder syntax rules
and formatting conventions.
"""

import logging
import re
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error in the output."""

    line_number: int
    message: str
    severity: str = "error"  # "error", "warning", "info"


class OutputValidator:
    """Validates decompiled PowerBuilder code output."""

    # Block structure pairs
    BLOCK_PAIRS = {
        "function": "end function",
        "subroutine": "end subroutine",
        "event": "end event",
        "if": "end if",
        "choose case": "end choose",
        "for": "next",
        "do while": "loop",
        "do": "loop",
        "try": "end try",
        "window": "end window",
        "userobject": "end userobject",
        "application": "end application",
    }

    # Keywords that start a block
    BLOCK_START_KEYWORDS = set(BLOCK_PAIRS.keys())

    # Keywords that end a block
    BLOCK_END_KEYWORDS = set(BLOCK_PAIRS.values())

    # Valid PowerBuilder keywords (comprehensive)
    KEYWORDS = {
        # Logical operators
        "and",
        "or",
        "not",
        "true",
        "false",
        "null",  # Control flow
        "if",
        "then",
        "else",
        "elseif",
        "end",
        "for",
        "to",
        "step",
        "next",
        "do",
        "while",
        "until",
        "loop",
        "choose",
        "case",
        # Function/Event keywords
        "function",
        "subroutine",
        "event",
        "on",  # Access modifiers
        "public",
        "private",
        "protected",
        "global",
        "local",  # Data types
        "integer",
        "long",
        "string",
        "boolean",
        "decimal",
        "double",
        "real",
        "char",
        "blob",
        "date",
        "time",
        "datetime",
        "any",
        "uint",
        "ulong",
        "longlong",
        "byte",
        "longptr",  # Control keywords
        "return",
        "exit",
        "continue",
        "halt",
        "close",  # Exception handling
        "try",
        "catch",
        "finally",
        "throw",
        "throws",  # Object references
        "this",
        "super",
        "parent",
        "parentwindow",  # Variable declarations
        "constant",
        "readonly",
        "ref",
        "indirect",  # Object types
        "window",
        "userobject",
        "menu",
        "structure",
        "application",
        "datawindow",
        "datastore",
        "transaction",  # Inheritance
        "from",
        "type",
        "forward",
        "prototypes",
        "alias",  # SQL keywords
        "select",
        "insert",
        "update",
        "delete",
        "where",
        "using",
        "sqlca",
        "commit",
        "rollback",  # Special
        "destroy",
        "create",
        "post",
        "trigger",
        "dynamic",
        "system",
        "library",
        "rpcfunc",
        "external",
    }

    # Patterns for validation
    IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    FUNCTION_PATTERN = re.compile(
        r"^\s*(public|private|protected|global)?\s*(function|subroutine)\s+(\w+\s+)?(\w+)\s*\("
    )
    EVENT_PATTERN = re.compile(r"^\s*event\s+(\w+)\s*\(")
    VARIABLE_DECLARATION_PATTERN = re.compile(
        r"^\s*(constant\s+)?(integer|long|string|boolean|decimal|double|real|char|blob|date|time|datetime|any|uint|ulong|longlong|byte|longptr)\s+(\w+)"
    )
    GLOBAL_VARIABLE_PATTERN = re.compile(r"^\s*(global|shared)\s+variables")
    INSTANCE_VARIABLE_PATTERN = re.compile(r"^\s*instance\s+variables")
    PROPERTY_PATTERN = re.compile(
        r"^\s*(public|private|protected)?\s*property\s+(\w+)\s+(\w+)"
    )
    TYPE_DECLARATION_PATTERN = re.compile(
        r"^\s*(global\s+)?type\s+(\w+)\s+from\s+(\w+)"
    )
    FORWARD_DECLARATION_PATTERN = re.compile(
        r"^\s*forward\s+(prototypes|global\s+type)"
    )
    SQL_PATTERN = re.compile(
        r"^\s*(select|insert|update|delete|declare|execute|fetch|close|open)\s+",
        re.IGNORECASE,
    )
    ASSIGNMENT_PATTERN = re.compile(r"^\s*(\w+(?:\[\d+\])?(?:\.\w+)*)\s*=\s*(.+)$")
    ARRAY_DECLARATION_PATTERN = re.compile(r"^\s*(\w+)\s+(\w+)\[\]")

    def __init__(self) -> None:
        """Initialize the validator."""
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []

    def validate(self, lines: list[str]) -> tuple[bool, list[ValidationError]]:
        """Validate the output lines.

        Args:
            lines: List of output lines to validate

        Returns:
            Tuple of (is_valid, errors) where is_valid is True if no errors found
        """
        self.errors = []
        self.warnings = []

        # Run all validation checks
        self._validate_block_structure(lines)
        self._validate_indentation(lines)
        self._validate_syntax_patterns(lines)
        self._validate_identifiers(lines)
        self._validate_comments(lines)
        self._validate_powerbuilder_constructs(lines)
        self._validate_variable_declarations(lines)
        self._validate_sql_statements(lines)

        # Combine errors and warnings
        all_issues = self.errors + self.warnings

        # Return validation result
        return len(self.errors) == 0, all_issues

    def _validate_block_structure(self, lines: list[str]) -> None:
        """Validate that all blocks are properly closed."""
        block_stack: list[str] = deque()

        for i, line in enumerate(lines, 1):
            stripped = line.strip().lower()
            if not stripped or stripped.startswith("//"):
                continue

            # Check for block start
            for start_keyword in self.BLOCK_START_KEYWORDS:
                # Check for exact keyword match with word boundaries
                if start_keyword == "do":
                    # Special handling for "do" - must be standalone or followed by while/until
                    if stripped == "do" or stripped.startswith(
                        ("do while", "do until")
                    ):
                        if "while" in stripped:
                            block_stack.append(("do while", i))
                        else:
                            block_stack.append(("do", i))
                        break
                elif stripped == start_keyword or stripped.startswith(
                    start_keyword + " "
                ):
                    block_stack.append((start_keyword, i))
                    break

            # Check for block end
            for end_keyword in self.BLOCK_END_KEYWORDS:
                # Special handling for "loop" which can be followed by "until" or "while"
                if end_keyword == "loop":
                    if stripped == "loop" or stripped.startswith("loop "):
                        # This handles "loop", "loop until condition", "loop while condition"
                        if not block_stack:
                            self.errors.append(
                                ValidationError(
                                    i,
                                    f"Unexpected '{stripped}' without matching block start",
                                )
                            )
                        else:
                            expected_start = None
                            for start, end in self.BLOCK_PAIRS.items():
                                if end == end_keyword:
                                    expected_start = start
                                    break

                            if expected_start:
                                # Pop matching blocks
                                if block_stack and (
                                    block_stack[-1][0] == expected_start
                                    or block_stack[-1][0] == "do"
                                ):
                                    block_stack.pop()
                                # Mismatched block
                                elif block_stack:
                                    actual_start, start_line = block_stack[-1]
                                    self.errors.append(
                                        ValidationError(
                                            i,
                                            f"Expected 'end {actual_start}' but found '{stripped}' (started at line {start_line})",
                                        )
                                    )
                                else:
                                    self.errors.append(
                                        ValidationError(
                                            i,
                                            f"Unexpected '{stripped}'",
                                        )
                                    )
                        break
                elif stripped.startswith(end_keyword) or stripped == end_keyword:
                    if not block_stack:
                        self.errors.append(
                            ValidationError(
                                i,
                                f"Unexpected '{end_keyword}' without matching block start",
                            )
                        )
                    else:
                        expected_start = None
                        for start, end in self.BLOCK_PAIRS.items():
                            if end == end_keyword:
                                expected_start = start
                                break

                        if expected_start:
                            # Pop matching blocks
                            if block_stack and block_stack[-1][0] == expected_start:
                                block_stack.pop()
                            # Mismatched block
                            elif block_stack:
                                actual_start, start_line = block_stack[-1]
                                self.errors.append(
                                    ValidationError(
                                        i,
                                        f"Expected 'end {actual_start}' but found '{end_keyword}' (started at line {start_line})",
                                    )
                                )
                            else:
                                self.errors.append(
                                    ValidationError(
                                        i,
                                        f"Unexpected '{end_keyword}'",
                                    )
                                )
                    break

        # Check for unclosed blocks
        while block_stack:
            block_type, start_line = block_stack.pop()
            self.errors.append(
                ValidationError(
                    len(lines),
                    f"Unclosed '{block_type}' block started at line {start_line}",
                )
            )

    def _validate_indentation(self, lines: list[str]) -> None:
        """Validate consistent indentation."""
        indent_size = None

        for i, line in enumerate(lines, 1):
            if not line.strip() or line.strip().startswith("//"):
                continue

            # Calculate actual indentation
            actual_indent = len(line) - len(line.lstrip())

            # Determine indent size from first indented line
            if indent_size is None and actual_indent > 0:
                indent_size = actual_indent

            # Check if indentation is consistent
            if indent_size and actual_indent % indent_size != 0:
                self.warnings.append(
                    ValidationError(
                        i,
                        f"Inconsistent indentation: {actual_indent} spaces (expected multiple of {indent_size})",
                        "warning",
                    )
                )

    def _validate_syntax_patterns(self, lines: list[str]) -> None:
        """Validate common syntax patterns."""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # Skip "end function" and similar end keywords
            if stripped.lower().startswith("end "):
                continue

            # Check function/subroutine declarations
            if any(
                keyword in stripped.lower() for keyword in ["function", "subroutine"]
            ) and not self.FUNCTION_PATTERN.match(line):
                # More lenient check
                if "function" in stripped.lower() and "(" in stripped:
                    pass  # Probably valid
                else:
                    self.warnings.append(
                        ValidationError(
                            i,
                            "Function/subroutine declaration may have invalid syntax",
                            "warning",
                        )
                    )

            # Check for common syntax errors
            if stripped.endswith(", "):
                self.warnings.append(
                    ValidationError(
                        i,
                        "Line ends with comma - possible incomplete statement",
                        "warning",
                    )
                )

            # Check for unbalanced parentheses
            if stripped.count("(") != stripped.count(")"):
                self.errors.append(
                    ValidationError(
                        i,
                        "Unbalanced parentheses",
                    )
                )

            # Check for unbalanced quotes (simple check)
            quote_count = stripped.count('"')
            if quote_count % 2 != 0:
                self.warnings.append(
                    ValidationError(
                        i,
                        "Odd number of quotes - possible unterminated string",
                        "warning",
                    )
                )

    def _validate_identifiers(self, lines: list[str]) -> None:
        """Validate identifier naming."""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # Extract potential identifiers from variable declarations
            var_match = self.VARIABLE_DECLARATION_PATTERN.match(stripped)
            if var_match:
                identifier = var_match.group(2)
                if not self.IDENTIFIER_PATTERN.match(identifier):
                    self.errors.append(
                        ValidationError(
                            i,
                            f"Invalid identifier: '{identifier}'",
                        )
                    )

    def _validate_comments(self, lines: list[str]) -> None:
        """Validate comment formatting."""
        for i, line in enumerate(lines, 1):
            if "//" in line:
                # Check if comment is properly formatted
                comment_start = line.find("//")
                if comment_start > 0:
                    # Inline comment - check spacing
                    if comment_start > 0 and line[comment_start - 1] not in " \t":
                        self.warnings.append(
                            ValidationError(
                                i,
                                "Comment should be preceded by whitespace",
                                "warning",
                            )
                        )

    def format_errors(self, errors: list[ValidationError]) -> str:
        """Format validation errors for display.

        Args:
            errors: List of validation errors

        Returns:
            Formatted error string
        """
        if not errors:
            return "No validation errors found."

        output = []

        # Group by severity
        error_list = [e for e in errors if e.severity == "error"]
        warning_list = [e for e in errors if e.severity == "warning"]
        info_list = [e for e in errors if e.severity == "info"]

        if error_list:
            output.append(f"Errors ({len(error_list)}):")
            for error in error_list:
                output.append(f"  Line {error.line_number}: {error.message}")

        if warning_list:
            if output:
                output.append("")
            output.append(f"Warnings ({len(warning_list)}):")
            for warning in warning_list:
                output.append(f"  Line {warning.line_number}: {warning.message}")

        if info_list:
            if output:
                output.append("")
            output.append(f"Info ({len(info_list)}):")
            for info in info_list:
                output.append(f"  Line {info.line_number}: {info.message}")

        return "\n".join(output)

    def _validate_powerbuilder_constructs(self, lines: list[str]) -> None:
        """Validate PowerBuilder-specific constructs."""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            # Check for global/instance variable blocks
            if self.GLOBAL_VARIABLE_PATTERN.match(stripped):
                continue
            if self.INSTANCE_VARIABLE_PATTERN.match(stripped):
                continue
            if stripped.lower() == "end variables":
                continue

            # Check for forward declarations
            if self.FORWARD_DECLARATION_PATTERN.match(stripped):
                continue
            if (
                stripped.lower() == "end prototypes"
                or stripped.lower() == "end forward"
            ):
                continue

            # Validate type declarations
            type_match = self.TYPE_DECLARATION_PATTERN.match(stripped)
            if type_match:
                type_match.group(2)
                parent_type = type_match.group(3)

                # Check if parent type is valid
                valid_parent_types = {
                    "window",
                    "userobject",
                    "menu",
                    "structure",
                    "application",
                    "datawindow",
                    "datastore",
                    "transaction",
                    "nonvisualobject",
                    "exception",
                    "error",
                    "throwable",
                }
                if (
                    parent_type.lower() not in valid_parent_types
                    and not self.IDENTIFIER_PATTERN.match(parent_type)
                ):
                    self.warnings.append(
                        ValidationError(
                            i,
                            f"Unusual parent type '{parent_type}' for type declaration",
                            "warning",
                        )
                    )

            # Check for property declarations
            if self.PROPERTY_PATTERN.match(stripped):
                # Properties should be in a type declaration
                if not any(
                    line.strip().lower().startswith("type ") for line in lines[:i]
                ):
                    self.warnings.append(
                        ValidationError(
                            i,
                            "Property declaration outside of type definition",
                            "warning",
                        )
                    )

    def _validate_variable_declarations(self, lines: list[str]) -> None:
        """Validate variable declarations with PowerBuilder-specific rules."""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # Check variable declarations
            var_match = self.VARIABLE_DECLARATION_PATTERN.match(stripped)
            if var_match:
                var_match.group(2)
                var_name = var_match.group(3)

                # Check for reserved words used as variable names
                if var_name.lower() in self.KEYWORDS:
                    self.errors.append(
                        ValidationError(
                            i,
                            f"Reserved keyword '{var_name}' used as variable name",
                        )
                    )

                # Check for array declarations
                if "[" in stripped and "]" in stripped:
                    # Validate array syntax
                    if not re.search(r"\w+\s*\[\s*(\d+|\s*)\s*\]", stripped):
                        self.warnings.append(
                            ValidationError(
                                i,
                                "Invalid array declaration syntax",
                                "warning",
                            )
                        )

            # Check for assignment patterns
            assign_match = self.ASSIGNMENT_PATTERN.match(stripped)
            if assign_match:
                assign_match.group(1)
                rhs = assign_match.group(2)

                # Check for common assignment errors
                if "=" in rhs and not any(
                    op in rhs for op in ["==", "!=", "<=", ">=", "<>"]
                ):
                    self.warnings.append(
                        ValidationError(
                            i,
                            "Possible nested assignment in expression",
                            "warning",
                        )
                    )

    def _validate_sql_statements(self, lines: list[str]) -> None:
        """Validate embedded SQL statements."""
        in_sql = False
        sql_start_line = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            # Check for SQL statement start
            if self.SQL_PATTERN.match(stripped):
                in_sql = True
                sql_start_line = i

                # Check for USING SQLCA
                if not any(
                    "using" in l.lower() and "sqlca" in l.lower()
                    for l in lines[i : i + 5]
                ):
                    self.warnings.append(
                        ValidationError(
                            i,
                            "SQL statement without explicit USING clause",
                            "warning",
                        )
                    )

            # Check for SQL end (semicolon)
            if in_sql and "" in stripped:
                in_sql = False

            # Check for dynamic SQL
            if "execute immediate" in stripped.lower():
                self.warnings.append(
                    ValidationError(
                        i,
                        "Dynamic SQL detected - ensure proper parameter handling",
                        "warning",
                    )
                )

        # Check for unclosed SQL
        if in_sql:
            self.errors.append(
                ValidationError(
                    sql_start_line,
                    f"Unclosed SQL statement started at line {sql_start_line}",
                )
            )
