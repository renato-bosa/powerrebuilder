"""Format reconstructed PowerBuilder code.

This module provides formatting capabilities for reconstructed PowerBuilder code,
handling indentation, line breaks, spacing, and different formatting styles.
"""

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from src.decompile.reconstruction.expression import Expression
from src.decompile.types import BlockType, ControlBlock

logger = logging.getLogger(__name__)


class FormattingStyle(Enum):
    """Available formatting styles for PowerBuilder code."""

    COMPACT = auto()  # Minimal spacing, single-line where possible
    STANDARD = auto()  # Standard PowerBuilder IDE formatting
    VERBOSE = auto()  # Extra spacing and comments for readability


@dataclass
class FormattingOptions:
    """Options for code formatting."""

    style: FormattingStyle = FormattingStyle.STANDARD
    indent_size: int = 4
    use_tabs: bool = False
    max_line_length: int = 120
    align_assignments: bool = True
    align_declarations: bool = True
    blank_lines_between_methods: int = 1
    blank_lines_between_sections: int = 2
    add_space_after_comma: bool = True
    add_space_around_operators: bool = True
    uppercase_keywords: bool = False
    lowercase_keywords: bool = True
    preserve_original_case: bool = False
    wrap_long_lines: bool = True
    indent_case_statements: bool = True
    indent_sql_statements: bool = True


class PowerBuilderFormatter:
    """Formats reconstructed PowerBuilder code."""

    def __init__(self, options: FormattingOptions | None = None) -> None:
        """Initialize the formatter.

        Args:
            options: Formatting options (uses defaults if None)
        """
        self.options = options or FormattingOptions()
        self.indent_level = 0
        self._indent_str = (
            "\t" if self.options.use_tabs else " " * self.options.indent_size
        )

    def format_object(
        self, blocks: list[ControlBlock], metadata: dict[str, Any]
    ) -> str:
        """Format a complete PowerBuilder object.

        Args:
            blocks: List of control flow blocks
            metadata: Object metadata

        Returns:
            Formatted PowerBuilder code
        """
        lines = []

        # Add header comment if verbose
        if self.options.style == FormattingStyle.VERBOSE:
            lines.extend(self._format_header_comment(metadata))
            lines.append("")

        # Format based on object type
        object_type = metadata.get("type", "unknown")

        if object_type == "window":
            lines.extend(self._format_window(blocks, metadata))
        elif object_type == "userobject":
            lines.extend(self._format_userobject(blocks, metadata))
        elif object_type == "function":
            lines.extend(self._format_function(blocks, metadata))
        elif object_type == "event":
            lines.extend(self._format_event(blocks, metadata))
        elif object_type == "application":
            lines.extend(self._format_application(blocks, metadata))
        else:
            lines.extend(self._format_generic(blocks, metadata))

        # Join lines and apply final formatting
        return self._finalize_formatting("\n".join(lines))

    def format_expression(self, expr: Expression) -> str:
        """Format a single expression.

        Args:
            expr: Expression to format

        Returns:
            Formatted expression string
        """
        formatted = expr.to_string()

        # Apply operator spacing
        if self.options.add_space_around_operators:
            formatted = self._add_operator_spacing(formatted)

        # Apply comma spacing
        if self.options.add_space_after_comma:
            formatted = self._add_comma_spacing(formatted)

        return formatted

    def format_block(self, block: ControlBlock) -> list[str]:
        """Format a control flow block.

        Args:
            block: Control block to format

        Returns:
            List of formatted lines
        """
        lines = []

        if block.type == BlockType.IF:
            lines.extend(self._format_if_block(block))
        elif block.type == BlockType.WHILE:
            lines.extend(self._format_while_block(block))
        elif block.type == BlockType.FOR:
            lines.extend(self._format_for_block(block))
        elif block.type == BlockType.DO_WHILE:
            lines.extend(self._format_do_while_block(block))
        elif block.type == BlockType.REPEAT_UNTIL:
            lines.extend(self._format_repeat_until_block(block))
        elif block.type == BlockType.CHOOSE_CASE:
            lines.extend(self._format_choose_case_block(block))
        elif block.type == BlockType.TRY:
            lines.extend(self._format_try_block(block))
        else:
            lines.extend(self._format_basic_block(block))

        return lines

    def _format_header_comment(self, metadata: dict[str, Any]) -> list[str]:
        """Format header comment for verbose style."""
        lines = [
            "/*" + "=" * 70,
            f" * Object: {metadata.get('name', 'Unknown')}",
            f" * Type: {metadata.get('type', 'Unknown')}",
        ]

        if "version" in metadata:
            lines.append(f" * PowerBuilder Version: {metadata['version']}")

        if "created" in metadata:
            lines.append(f" * Created: {metadata['created']}")

        if "modified" in metadata:
            lines.append(f" * Modified: {metadata['modified']}")

        lines.append(" " + "=" * 70 + "*/")
        return lines

    def _format_window(
        self, blocks: list[ControlBlock], metadata: dict[str, Any]
    ) -> list[str]:
        """Format a window object."""
        lines = []
        name = metadata.get("name", "unknown_window")

        # Window declaration
        lines.append(self._format_keyword("window") + f" {name}")

        # Properties
        if "properties" in metadata:
            lines.extend(self._format_properties(metadata["properties"]))

        # Events and methods
        for block in blocks:
            if block.type == BlockType.EVENT:
                lines.extend(
                    self._add_blank_lines(self.options.blank_lines_between_methods)
                )
                lines.extend(self.format_block(block))

        lines.append(self._format_keyword("end window"))
        return lines

    def _format_function(
        self, blocks: list[ControlBlock], metadata: dict[str, Any]
    ) -> list[str]:
        """Format a function."""
        lines = []
        name = metadata.get("name", "unknown_function")
        return_type = metadata.get("return_type", "none")
        params = metadata.get("parameters", [])

        # Function signature
        signature = self._format_function_signature(name, return_type, params)
        lines.append(signature)

        self.indent_level += 1

        # Local variables
        if "local_variables" in metadata:
            lines.extend(self._format_local_variables(metadata["local_variables"]))
            if metadata["local_variables"]:
                lines.append("")

        # Function body
        for block in blocks:
            lines.extend(self.format_block(block))

        self.indent_level -= 1
        lines.append(self._format_keyword("end function"))
        return lines

    def _format_if_block(self, block: ControlBlock) -> list[str]:
        """Format an IF block."""
        lines = []
        condition = block.metadata.get("condition", "unknown_condition")

        # IF statement
        lines.append(
            self._indent(
                f"{self._format_keyword('if')} {condition} {self._format_keyword('then')}"
            )
        )

        # THEN branch
        self.indent_level += 1
        if hasattr(block, "then_block") and block.then_block:
            lines.extend(self.format_block(block.then_block))
        elif hasattr(block, "statements") and block.statements:
            for stmt in block.statements:
                lines.append(self._indent(stmt))

        # ELSE branch
        if hasattr(block, "else_block") and block.else_block:
            self.indent_level -= 1
            lines.append(self._indent(self._format_keyword("else")))
            self.indent_level += 1
            lines.extend(self.format_block(block.else_block))

        self.indent_level -= 1
        lines.append(self._indent(self._format_keyword("end if")))
        return lines

    def _format_while_block(self, block: ControlBlock) -> list[str]:
        """Format a WHILE loop."""
        lines = []
        condition = block.metadata.get("condition", "unknown_condition")

        lines.append(self._indent(f"{self._format_keyword('do while')} {condition}"))

        self.indent_level += 1
        if hasattr(block, "body") and block.body:
            lines.extend(self.format_block(block.body))
        elif hasattr(block, "statements") and block.statements:
            for stmt in block.statements:
                lines.append(self._indent(stmt))
        self.indent_level -= 1

        lines.append(self._indent(self._format_keyword("loop")))
        return lines

    def _format_for_block(self, block: ControlBlock) -> list[str]:
        """Format a FOR loop."""
        lines = []
        var = block.metadata.get("variable", "i")
        start = block.metadata.get("start", "1")
        end = block.metadata.get("end", "unknown")
        step = block.metadata.get("step", "1")

        # FOR statement
        for_stmt = f"{self._format_keyword('for')} {var} = {start} {self._format_keyword('to')} {end}"
        if step != "1":
            for_stmt += f" {self._format_keyword('step')} {step}"
        lines.append(self._indent(for_stmt))

        self.indent_level += 1
        if hasattr(block, "body") and block.body:
            lines.extend(self.format_block(block.body))
        elif hasattr(block, "statements") and block.statements:
            for stmt in block.statements:
                lines.append(self._indent(stmt))
        self.indent_level -= 1

        lines.append(self._indent(self._format_keyword("next")))
        return lines

    def _format_choose_case_block(self, block: ControlBlock) -> list[str]:
        """Format a CHOOSE CASE block."""
        lines = []
        expr = block.metadata.get("expression", "unknown_expression")

        lines.append(self._indent(f"{self._format_keyword('choose case')} {expr}"))

        self.indent_level += 1

        # Format cases
        if hasattr(block, "cases") and block.cases:
            for case in block.cases:
                if isinstance(case, dict):
                    value = case.get("value", "unknown")
                    lines.append(
                        self._indent(f"{self._format_keyword('case')} {value}")
                    )

                    if self.options.indent_case_statements:
                        self.indent_level += 1

                    if "body" in case:
                        lines.extend(self.format_block(case["body"]))

                    if self.options.indent_case_statements:
                        self.indent_level -= 1

        # Default case
        if hasattr(block, "default_case") and block.default_case:
            lines.append(self._indent(self._format_keyword("case else")))

            if self.options.indent_case_statements:
                self.indent_level += 1

            lines.extend(self.format_block(block.default_case))

            if self.options.indent_case_statements:
                self.indent_level -= 1

        self.indent_level -= 1
        lines.append(self._indent(self._format_keyword("end choose")))
        return lines

    def _format_basic_block(self, block: ControlBlock) -> list[str]:
        """Format a basic block with just statements."""
        lines = []

        if hasattr(block, "statements") and block.statements:
            for stmt in block.statements:
                # Skip labels - they'll be handled by the processor
                if (
                    isinstance(stmt, str)
                    and stmt.strip().startswith("L_")
                    and stmt.strip().endswith(":")
                ):
                    continue
                lines.append(self._indent(stmt))

        return lines

    def _format_function_signature(
        self, name: str, return_type: str, params: list[dict[str, Any]]
    ) -> str:
        """Format a function signature."""
        # Build parameter list
        param_strs = []
        for param in params:
            param_type = param.get("type", "any")
            param_name = param.get("name", "param")
            param_mode = param.get("mode", "")

            if param_mode:
                param_str = f"{param_mode} {param_type} {param_name}"
            else:
                param_str = f"{param_type} {param_name}"

            param_strs.append(param_str)

        # Build signature
        if return_type and return_type != "none":
            signature = f"{self._format_keyword('function')} {return_type} {name}("
        else:
            signature = f"{self._format_keyword('function')} {name}("

        if (
            self.options.wrap_long_lines
            and len(signature) + len(", ".join(param_strs))
            > self.options.max_line_length
        ):
            # Multi-line parameters
            if param_strs:
                signature += " &\n"
                for i, param in enumerate(param_strs):
                    signature += self._indent_str + self._indent_str + param
                    if i < len(param_strs) - 1:
                        signature += ", &\n"
                signature += " )"
            else:
                signature += ")"
        else:
            # Single line
            signature += ", ".join(param_strs) + ")"

        return signature

    def _format_local_variables(self, variables: list[dict[str, Any]]) -> list[str]:
        """Format local variable declarations."""
        lines = []

        if self.options.align_declarations:
            # Find longest type name for alignment
            max_type_len = max(
                (len(var.get("type", "")) for var in variables), default=0
            )

            for var in variables:
                var_type = var.get("type", "any")
                var_name = var.get("name", "var")
                var_init = var.get("initial_value", None)

                if var_init:
                    lines.append(
                        self._indent(
                            f"{var_type:<{max_type_len}} {var_name} = {var_init}"
                        )
                    )
                else:
                    lines.append(self._indent(f"{var_type:<{max_type_len}} {var_name}"))
        else:
            for var in variables:
                var_type = var.get("type", "any")
                var_name = var.get("name", "var")
                var_init = var.get("initial_value", None)

                if var_init:
                    lines.append(self._indent(f"{var_type} {var_name} = {var_init}"))
                else:
                    lines.append(self._indent(f"{var_type} {var_name}"))

        return lines

    def _format_keyword(self, keyword: str) -> str:
        """Format a keyword according to options."""
        if self.options.preserve_original_case:
            return keyword
        if self.options.uppercase_keywords:
            return keyword.upper()
        if self.options.lowercase_keywords:
            return keyword.lower()
        # Title case
        return keyword.title()

    def _indent(self, text: str) -> str:
        """Add indentation to a line."""
        if not text or text.isspace():
            return text
        return self._indent_str * self.indent_level + text

    def _add_blank_lines(self, count: int) -> list[str]:
        """Add blank lines."""
        return [""] * count

    def _add_operator_spacing(self, text: str) -> str:
        """Add spacing around operators."""
        operators = [
            "=",
            "+",
            "-",
            "*",
            "/",
            "^",
            "<>",
            "<=",
            ">=",
            "<",
            ">",
            "AND",
            "OR",
            "MOD",
        ]

        for op in operators:
            # Skip if already has spaces
            if f" {op} " in text:
                continue

            # Add spaces around operator
            # Be careful not to break strings or comments
            in_string = False
            in_comment = False
            result = []
            i = 0

            while i < len(text):
                if text[i] == '"' and not in_comment:
                    in_string = not in_string
                    result.append(text[i])
                elif text[i : i + 2] == "//" and not in_string:
                    in_comment = True
                    result.append(text[i])
                elif not in_string and not in_comment and text[i : i + len(op)] == op:
                    # Found operator outside of string/comment
                    # Check if it's not part of a larger operator
                    if (
                        op in ["<", ">", "="]
                        and i + 1 < len(text)
                        and text[i + 1] in ["=", ">"]
                    ):
                        result.append(text[i])
                    else:
                        # Add spaces around operator
                        if i > 0 and text[i - 1] != " ":
                            result.append(" ")
                        result.append(op)
                        if i + len(op) < len(text) and text[i + len(op)] != " ":
                            result.append(" ")
                        i += len(op) - 1
                else:
                    result.append(text[i])

                i += 1

            text = "".join(result)

        return text

    def _add_comma_spacing(self, text: str) -> str:
        """Add spacing after commas."""
        # Simple implementation - could be enhanced
        in_string = False
        result = []

        for i, char in enumerate(text):
            if char == '"':
                in_string = not in_string
            elif char == "," and not in_string:
                result.append(char)
                # Add space if next char is not already a space
                if i + 1 < len(text) and text[i + 1] != " ":
                    result.append(" ")
                continue

            result.append(char)

        return "".join(result)

    def _finalize_formatting(self, code: str) -> str:
        """Apply final formatting passes."""
        lines = code.split("\n")

        # Remove trailing whitespace
        lines = [line.rstrip() for line in lines]

        # Remove excessive blank lines
        if self.options.style != FormattingStyle.VERBOSE:
            result = []
            blank_count = 0

            for line in lines:
                if not line:
                    blank_count += 1
                    if blank_count <= 2:  # Max 2 consecutive blank lines
                        result.append(line)
                else:
                    blank_count = 0
                    result.append(line)

            lines = result

        # Ensure file ends with newline
        if lines and lines[-1]:
            lines.append("")

        return "\n".join(lines)

    def _format_generic(
        self, blocks: list[ControlBlock], metadata: dict[str, Any]
    ) -> list[str]:
        """Format a generic object type."""
        lines = []

        # Just format all blocks
        for i, block in enumerate(blocks):
            if i > 0:
                lines.extend(
                    self._add_blank_lines(self.options.blank_lines_between_methods)
                )
            lines.extend(self.format_block(block))

        return lines

    def _format_event(
        self, blocks: list[ControlBlock], metadata: dict[str, Any]
    ) -> list[str]:
        """Format an event."""
        lines = []
        name = metadata.get("name", "unknown_event")
        params = metadata.get("parameters", [])

        # Event signature
        signature = f"{self._format_keyword('event')} {name}("
        param_strs = [
            f"{p.get('type', 'any')} {p.get('name', 'param')}" for p in params
        ]
        signature += ", ".join(param_strs) + ")"
        lines.append(signature)

        self.indent_level += 1

        # Event body
        for block in blocks:
            lines.extend(self.format_block(block))

        self.indent_level -= 1
        lines.append(self._format_keyword("end event"))
        return lines

    def _format_userobject(
        self, blocks: list[ControlBlock], metadata: dict[str, Any]
    ) -> list[str]:
        """Format a user object."""
        lines = []
        name = metadata.get("name", "unknown_userobject")
        parent = metadata.get("parent")

        # User object declaration
        if parent:
            lines.append(
                f"{self._format_keyword('userobject')} {name} {self._format_keyword('from')} {parent}"
            )
        else:
            lines.append(f"{self._format_keyword('userobject')} {name}")

        # Properties
        if "properties" in metadata:
            lines.extend(self._format_properties(metadata["properties"]))

        # Methods and events
        for block in blocks:
            lines.extend(
                self._add_blank_lines(self.options.blank_lines_between_methods)
            )
            lines.extend(self.format_block(block))

        lines.append(self._format_keyword("end userobject"))
        return lines

    def _format_application(
        self, blocks: list[ControlBlock], metadata: dict[str, Any]
    ) -> list[str]:
        """Format an application object."""
        lines = []
        name = metadata.get("name", "unknown_application")

        lines.append(f"{self._format_keyword('application')} {name}")

        # Global variables
        if "global_variables" in metadata:
            lines.append(self._format_keyword("global variables"))
            self.indent_level += 1
            lines.extend(self._format_local_variables(metadata["global_variables"]))
            self.indent_level -= 1
            lines.append(self._format_keyword("end variables"))
            lines.append("")

        # Events
        for block in blocks:
            if block.type == BlockType.EVENT:
                lines.extend(
                    self._add_blank_lines(self.options.blank_lines_between_methods)
                )
                lines.extend(self.format_block(block))

        lines.append(self._format_keyword("end application"))
        return lines

    def _format_properties(self, properties: list[dict[str, Any]]) -> list[str]:
        """Format object properties."""
        lines = []

        for prop in properties:
            name = prop.get("name", "unknown_property")
            value = prop.get("value", "")
            prop_type = prop.get("type", "")

            if prop_type:
                lines.append(self._indent(f"{prop_type} {name} = {value}"))
            else:
                lines.append(self._indent(f"{name} = {value}"))

        return lines

    def _format_repeat_until_block(self, block: ControlBlock) -> list[str]:
        """Format a REPEAT UNTIL loop."""
        lines = []
        condition = block.metadata.get("condition", "unknown_condition")

        lines.append(self._indent(self._format_keyword("do")))

        self.indent_level += 1
        if hasattr(block, "body") and block.body:
            lines.extend(self.format_block(block.body))
        elif hasattr(block, "statements") and block.statements:
            for stmt in block.statements:
                lines.append(self._indent(stmt))
        self.indent_level -= 1

        lines.append(self._indent(f"{self._format_keyword('loop until')} {condition}"))
        return lines

    def _format_do_while_block(self, block: ControlBlock) -> list[str]:
        """Format a DO WHILE loop."""
        lines = []
        condition = block.metadata.get("condition", "unknown_condition")

        lines.append(self._indent(self._format_keyword("do")))

        self.indent_level += 1
        if hasattr(block, "body") and block.body:
            lines.extend(self.format_block(block.body))
        elif hasattr(block, "statements") and block.statements:
            for stmt in block.statements:
                lines.append(self._indent(stmt))
        self.indent_level -= 1

        lines.append(self._indent(f"{self._format_keyword('loop while')} {condition}"))
        return lines

    def _format_try_block(self, block: ControlBlock) -> list[str]:
        """Format a TRY block."""
        lines = []

        lines.append(self._indent(self._format_keyword("try")))

        self.indent_level += 1
        if hasattr(block, "try_body") and block.try_body:
            lines.extend(self.format_block(block.try_body))
        elif hasattr(block, "statements") and block.statements:
            for stmt in block.statements:
                lines.append(self._indent(stmt))
        self.indent_level -= 1

        # Format catch blocks
        if hasattr(block, "catch_blocks"):
            for catch in block.catch_blocks:
                exception_type = catch.get("type", "Exception")
                var_name = catch.get("variable", "ex")
                lines.append(
                    self._indent(
                        f"{self._format_keyword('catch')} ({exception_type} {var_name})"
                    )
                )

                self.indent_level += 1
                if "body" in catch:
                    lines.extend(self.format_block(catch["body"]))
                self.indent_level -= 1

        # Format finally block
        if hasattr(block, "finally_block") and block.finally_block:
            lines.append(self._indent(self._format_keyword("finally")))
            self.indent_level += 1
            lines.extend(self.format_block(block.finally_block))
            self.indent_level -= 1

        lines.append(self._indent(self._format_keyword("end try")))
        return lines
