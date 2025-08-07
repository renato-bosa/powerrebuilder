"""PowerBuilder method body to Dart/Python converter.

This module converts complete PowerBuilder method bodies to Dart or Python,
handling control flow, database operations, variable declarations, and more.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from src.generate.converters.data.db_formatter import DatabaseOperationFormatter
from src.generate.converters.utils.expressions import ExpressionConverter
from src.generate.converters.utils.types import TypeConverter

logger = logging.getLogger(__name__)


@dataclass
class ConvertedStatement:
    """Represents a converted statement."""

    dart_code: str
    python_code: str
    requires_async: bool = False
    imports_needed: list[str] = None

    def __post_init__(self) -> None:
        if self.imports_needed is None:
            self.imports_needed = []


class MethodBodyConverter:
    """Converts PowerBuilder method bodies to Dart or Python."""

    def __init__(self) -> None:
        """Initialize the method body converter."""
        self.expression_converter = ExpressionConverter()
        self.db_formatter = DatabaseOperationFormatter()
        self.type_converter = TypeConverter()

        # PowerBuilder control flow keywords
        self.control_keywords = {
            "if",
            "then",
            "else",
            "elseif",
            "end if",
            "for",
            "to",
            "step",
            "next",
            "do",
            "while",
            "loop",
            "until",
            "choose case",
            "case",
            "end choose",
            "try",
            "catch",
            "finally",
            "end try",
            "return",
            "exit",
            "continue",
        }

        # PowerBuilder to Dart/Python statement patterns
        self.statement_patterns = [
            # Variable declarations
            (
                r"^\s*(string|int|integer|long|decimal|boolean|datetime|date|time)\s+(\w+)(?:\s*=\s*(.+))?",
                self._convert_variable_declaration,
            ),
            # Array declarations
            (
                r"^\s*(\w+)\s+(\w+)\[\s*\](?:\s*=\s*(.+))?",
                self._convert_array_declaration,
            ),
            # Assignment statements
            (
                r"^\s*(\w+(?:\.\w+)*)\s*=\s*(.+)",
                self._convert_assignment,
            ),
            # MessageBox (before generic method calls)
            (r"^\s*messagebox\s*\((.*)\)", self._convert_messagebox),
            # Method calls
            (
                r"^\s*(\w+(?:\.\w+)*)\s*\((.*)\)",
                self._convert_method_call,
            ),
            # If statements
            (r"^\s*if\s+(.+)\s+then", self._convert_if_statement),
            # For loops
            (
                r"^\s*for\s+(\w+)\s*=\s*(.+)\s+to\s+(.+)(?:\s+step\s+(.+))?",
                self._convert_for_loop,
            ),
            # While loops
            (r"^\s*do\s+while\s+(.+)", self._convert_while_loop),
            # Return statements
            (r"^\s*return\s*(.*)", self._convert_return),
            # Database operations
            (
                r"^\s*(select|insert|update|delete|fetch|close|open)\s+",
                self._convert_database_operation,
            ),
            # Control property access
            (
                r"^\s*(\w+)\.(\w+)\s*=\s*(.+)",
                self._convert_property_assignment,
            ),
            # Control structure endings
            (
                r"^\s*(end\s+if|next|loop|end\s+try|end\s+choose)\s*$",
                self._convert_control_ending,
            ),
        ]

    def convert_method_body(
        self,
        pb_code: str,
        _method_name: str | None = None,
        _parameters: list[tuple[str, str]] | None = None,
        _return_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Convert PowerBuilder method body to Dart and Python.

        Args:
            pb_code: PowerBuilder code to convert
            method_name: Name of the method
            parameters: Method parameters
            return_type: Method return type
            context: Additional context (variables, controls, etc.)

        Returns:
            Dictionary with converted code and metadata
        """
        if not pb_code or not pb_code.strip():
            return {
                "dart": "// Empty method",
                "python": "pass",
                "requires_async": False,
                "imports": [],
            }

        lines = pb_code.strip().split("\n")
        dart_lines = []
        python_lines = []
        requires_async = False
        imports_needed = set()
        indent_level = 0

        for line in lines:
            line = line.rstrip()

            # Skip empty lines and comments
            if not line.strip():
                dart_lines.append("")
                python_lines.append("")
                continue

            if line.strip().startswith("//"):
                dart_lines.append(line)
                python_lines.append(line.replace("//", "#"))
                continue

            # Convert the statement
            result = self._convert_statement(line, context)

            if result:
                # Handle indentation
                dart_indent = "  " * indent_level
                python_indent = "    " * indent_level

                # Add converted code
                if result.dart_code:
                    dart_lines.append(dart_indent + result.dart_code)
                if result.python_code:
                    python_lines.append(python_indent + result.python_code)

                # Track async requirement
                if result.requires_async:
                    requires_async = True

                # Collect imports
                imports_needed.update(result.imports_needed)

                # Update indent level based on control flow
                indent_change = self._get_indent_change(line)
                if indent_change > 0:
                    indent_level += indent_change
                elif indent_change < 0:
                    # Reduce indent before the line for closing statements
                    if dart_lines and dart_lines[-1].strip():
                        dart_lines[-1] = dart_lines[-1][2:]  # Remove one indent
                    if python_lines and python_lines[-1].strip():
                        python_lines[-1] = python_lines[-1][4:]  # Remove one indent
                    indent_level += indent_change
            else:
                # Couldn't convert - add as comment
                dart_lines.append(f"// TODO: Convert - {line.strip()}")
                python_lines.append(f"# TODO: Convert - {line.strip()}")

        return {
            "dart": "\n".join(dart_lines),
            "python": "\n".join(python_lines),
            "requires_async": requires_async,
            "imports": list(imports_needed),
        }

    def _convert_statement(
        self, statement: str, context: dict[str, Any] | None = None
    ) -> ConvertedStatement | None:
        """Convert a single PowerBuilder statement."""
        statement = statement.strip()

        # Try each pattern
        for pattern, converter in self.statement_patterns:
            match = re.match(pattern, statement, re.IGNORECASE)
            if match:
                return converter(match, context)

        # Try expression conversion as fallback
        try:
            dart_expr = self.expression_converter.convert_expression(statement)
            python_expr = self._convert_expression_to_python(statement)
            return ConvertedStatement(
                dart_code=f"{dart_expr}",
                python_code=f"{python_expr}",
            )
        except Exception:
            return None

    def _convert_variable_declaration(
        self, match: re.Match[str], _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert variable declaration."""
        pb_type = match.group(1)
        var_name = match.group(2)
        initial_value = match.group(3)

        # Convert types
        dart_type = self.type_converter.convert_type(pb_type)
        python_type = self._pb_to_python_type(pb_type)

        # Convert initial value if present
        if initial_value:
            dart_value = self.expression_converter.convert_expression(
                initial_value.strip()
            )
            python_value = self._convert_expression_to_python(initial_value.strip())
        else:
            dart_value = self._get_dart_default(dart_type)
            python_value = self._get_python_default(python_type)

        return ConvertedStatement(
            dart_code=f"{dart_type} {var_name} = {dart_value};",
            python_code=f"{var_name}: {python_type} = {python_value}",
        )

    def _convert_array_declaration(
        self, match: re.Match[str], _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert array declaration."""
        pb_type = match.group(1)
        var_name = match.group(2)
        initial_value = match.group(3)

        # Convert types
        dart_type = self.type_converter.convert_type(pb_type)
        python_type = self._pb_to_python_type(pb_type)

        # Array initialization
        if initial_value:
            # Parse array literal
            dart_value = self._convert_array_literal(initial_value, dart_type)
            python_value = self._convert_array_literal(initial_value, python_type)
        else:
            dart_value = "[]"
            python_value = "[]"

        return ConvertedStatement(
            dart_code=f"List<{dart_type}> {var_name} = {dart_value};",
            python_code=f"{var_name}: list[{python_type}] = {python_value}",
            imports_needed=["typing"] if python_type else [],
        )

    def _convert_assignment(
        self, match: re.Match[str], context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert assignment statement."""
        lhs = match.group(1)
        rhs = match.group(2).strip()

        # Check if RHS is a control property access
        if "." in rhs and context and "controls" in context:
            parts = rhs.split(".", 1)
            control_name = parts[0]
            property_name = parts[1]

            if control_name in context.get("controls", {}):
                control = context["controls"][control_name]
                flutter_widget = control.get("flutter_widget", {})

                # Check if this control needs a controller
                if (
                    flutter_widget.get("requires_controller")
                    and property_name.lower() == "text"
                ):
                    dart_rhs = f"{control_name}Controller.text"
                else:
                    dart_rhs = f"{control_name}.{property_name}"

                python_rhs = self._convert_expression_to_python(rhs)

                return ConvertedStatement(
                    dart_code=f"{lhs} = {dart_rhs};",
                    python_code=f"{lhs} = {python_rhs}",
                )

        # Check if it's a control property assignment on LHS
        if "." in lhs and context and "controls" in context:
            parts = lhs.split(".", 1)
            control_name = parts[0]
            property_name = parts[1]

            if control_name in context.get("controls", {}):
                return self._convert_control_property_assignment(
                    control_name, property_name, rhs, context
                )

        # Regular assignment
        dart_rhs = self.expression_converter.convert_expression(rhs)
        python_rhs = self._convert_expression_to_python(rhs)

        return ConvertedStatement(
            dart_code=f"{lhs} = {dart_rhs};",
            python_code=f"{lhs} = {python_rhs}",
        )

    def _convert_method_call(
        self, match: re.Match[str], context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert method call."""
        method_path = match.group(1)
        args = match.group(2)

        # Check for special methods
        if "." in method_path:
            obj, method = method_path.rsplit(".", 1)
            if method.lower() in ["setfocus", "show", "hide", "close"]:
                return self._convert_ui_method(obj, method, args, context)

        # Convert arguments
        dart_args = self._convert_arguments(args, "dart")
        python_args = self._convert_arguments(args, "python")

        # Check if it's an async method
        requires_async = self._is_async_method(method_path, context)

        if requires_async:
            dart_code = f"await {method_path}({dart_args});"
        else:
            dart_code = f"{method_path}({dart_args});"

        return ConvertedStatement(
            dart_code=dart_code,
            python_code=f"{method_path}({python_args})",
            requires_async=requires_async,
        )

    def _convert_if_statement(
        self, match: re.Match[str], _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert if statement."""
        condition = match.group(1)

        dart_condition = self.expression_converter.convert_expression(condition)
        python_condition = self._convert_expression_to_python(condition)

        return ConvertedStatement(
            dart_code=f"if ({dart_condition}) {{",
            python_code=f"if {python_condition}:",
        )

    def _convert_for_loop(
        self, match: re.Match[str], _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert for loop."""
        var_name = match.group(1)
        start_expr = match.group(2).strip()
        end_expr = match.group(3).strip()
        step_expr = match.group(4)

        # Convert expressions
        dart_start = self.expression_converter.convert_expression(start_expr)
        dart_end = self.expression_converter.convert_expression(end_expr)

        python_start = self._convert_expression_to_python(start_expr)
        python_end = self._convert_expression_to_python(end_expr)

        if step_expr:
            step_expr = step_expr.strip()
            dart_step = self.expression_converter.convert_expression(step_expr)
            python_step = self._convert_expression_to_python(step_expr)

            # Dart doesn't have step in for loop, use while
            dart_code = f"for (int {var_name} = {dart_start}; {var_name} <= {dart_end}; {var_name} += {dart_step}) {{"
            python_code = f"for {var_name} in range({python_start}, {python_end} + 1, {python_step}):"
        else:
            dart_code = f"for (int {var_name} = {dart_start}; {var_name} <= {dart_end}; {var_name}++) {{"
            python_code = f"for {var_name} in range({python_start}, {python_end} + 1):"

        return ConvertedStatement(
            dart_code=dart_code,
            python_code=python_code,
        )

    def _convert_while_loop(
        self, match: re.Match[str], _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert while loop."""
        condition = match.group(1)

        dart_condition = self.expression_converter.convert_expression(condition)
        python_condition = self._convert_expression_to_python(condition)

        return ConvertedStatement(
            dart_code=f"while ({dart_condition}) {{",
            python_code=f"while {python_condition}:",
        )

    def _convert_return(
        self, match: re.Match[str], _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert return statement."""
        return_expr = match.group(1).strip()

        if return_expr:
            dart_expr = self.expression_converter.convert_expression(return_expr)
            python_expr = self._convert_expression_to_python(return_expr)

            return ConvertedStatement(
                dart_code=f"return {dart_expr};",
                python_code=f"return {python_expr}",
            )
        return ConvertedStatement(
            dart_code="return;",
            python_code="return",
        )

    def _convert_database_operation(
        self, match: re.Match[str], context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert database operation."""
        full_statement = match.group(0)

        # Use database operation formatter
        db_ops = self.db_formatter.format_database_operations([full_statement], context)

        if db_ops and db_ops[0]:
            # Extract Dart and Python versions
            # This is simplified - the actual formatter might return more complex structure
            dart_code = (
                db_ops[0]
                if self.db_formatter.target == "flutter"
                else self._generate_dart_db_op(full_statement)
            )
            python_code = (
                db_ops[0]
                if self.db_formatter.target == "python"
                else self._generate_python_db_op(full_statement)
            )

            return ConvertedStatement(
                dart_code=dart_code,
                python_code=python_code,
                requires_async=True,
                imports_needed=["dart:async"]
                if self.db_formatter.target == "flutter"
                else ["sqlalchemy"],
            )

        return ConvertedStatement(
            dart_code=f"// TODO: Database operation - {full_statement}",
            python_code=f"# TODO: Database operation - {full_statement}",
            requires_async=True,
        )

    def _convert_messagebox(
        self, match: re.Match[str], _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert MessageBox to platform equivalent."""
        args = match.group(1)

        # Parse arguments (simplified)
        arg_list = self._parse_arguments(args)

        if len(arg_list) >= 2:
            # Strip outer quotes more carefully
            title = arg_list[0].strip().strip("\"'")
            message = arg_list[1].strip().strip("\"'")

            dart_code = f"""showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('{title}'),
        content: Text('{message}'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );"""

            python_code = f'messagebox.showinfo("{title}", "{message}")'

            return ConvertedStatement(
                dart_code=dart_code,
                python_code=python_code,
                imports_needed=["flutter/material.dart", "tkinter.messagebox"],
            )

        return ConvertedStatement(
            dart_code=f"// TODO: MessageBox - {args}",
            python_code=f"# TODO: MessageBox - {args}",
        )

    def _convert_property_assignment(
        self, match: re.Match[str], context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert property assignment."""
        obj_name = match.group(1)
        prop_name = match.group(2)
        value = match.group(3).strip()

        return self._convert_control_property_assignment(
            obj_name, prop_name, value, context
        )

    def _convert_control_ending(
        self, match: re.Match[str], _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert control structure endings."""
        ending = match.group(1).lower()

        # Map PowerBuilder endings to Dart/Python
        dart_code = "}"  # Most control structures end with }
        python_code = ""  # Python doesn't need explicit endings

        # Special cases
        if ending in {"next", "loop"}:
            dart_code = "}"

        return ConvertedStatement(
            dart_code=dart_code,
            python_code=python_code,
        )

    def _convert_control_property_assignment(
        self,
        control_name: str,
        property_name: str,
        value: str,
        _context: dict[str, Any] | None = None,
    ) -> ConvertedStatement:
        """Convert control property assignment."""
        dart_value = self.expression_converter.convert_expression(value)
        python_value = self._convert_expression_to_python(value)

        prop_lower = property_name.lower()

        # Map common properties
        if prop_lower == "text":
            dart_code = f"{control_name}Controller.text = {dart_value};"
            python_code = f"self.{control_name}.config(text={python_value})"
        elif prop_lower == "enabled":
            # In Flutter, enabling/disabling is typically done through setState
            dart_code = f"setState(() => _{control_name}Enabled = {dart_value});"
            python_code = f'self.{control_name}.config(state="normal" if {python_value} else "disabled")'
        elif prop_lower == "visible":
            # In Flutter, visibility is controlled through setState
            dart_code = f"setState(() => _{control_name}Visible = {dart_value});"
            python_code = f"self.{control_name}.pack() if {python_value} else self.{control_name}.pack_forget()"
        else:
            dart_code = f"{control_name}.{property_name} = {dart_value};"
            python_code = f"self.{control_name}.{property_name} = {python_value}"

        return ConvertedStatement(
            dart_code=dart_code,
            python_code=python_code,
        )

    def _convert_ui_method(
        self, obj: str, method: str, args: str, _context: dict[str, Any] | None = None
    ) -> ConvertedStatement:
        """Convert UI-specific methods."""
        method_lower = method.lower()

        if method_lower == "setfocus":
            dart_code = f"{obj}FocusNode.requestFocus();"
            python_code = f"self.{obj}.focus_set()"
        elif method_lower == "show":
            # In Flutter, show is done by setting visibility to true
            dart_code = f"setState(() => _{obj}Visible = true);"
            python_code = f"self.{obj}.pack()"
        elif method_lower == "hide":
            # In Flutter, hide is done by setting visibility to false
            dart_code = f"setState(() => _{obj}Visible = false);"
            python_code = f"self.{obj}.pack_forget()"
        elif method_lower == "close":
            dart_code = "Navigator.pop(context);"
            python_code = "self.destroy()"
        else:
            dart_code = f"{obj}.{method}({self._convert_arguments(args, 'dart')});"
            python_code = (
                f"self.{obj}.{method}({self._convert_arguments(args, 'python')})"
            )

        return ConvertedStatement(
            dart_code=dart_code,
            python_code=python_code,
        )

    def _convert_expression_to_python(self, expr: str) -> str:
        """Convert PowerBuilder expression to Python."""
        # This is a simplified implementation
        # A full implementation would handle all PowerBuilder expressions

        # Handle boolean operators
        expr = expr.replace(" and ", " and ")
        expr = expr.replace(" or ", " or ")
        expr = expr.replace(" not ", " not ")
        expr = expr.replace("<>", "!=")

        # Handle null
        expr = re.sub(r"\bnull\b", "None", expr, flags=re.IGNORECASE)

        # Handle true/false
        expr = re.sub(r"\btrue\b", "True", expr, flags=re.IGNORECASE)
        return re.sub(r"\bfalse\b", "False", expr, flags=re.IGNORECASE)

    def _convert_arguments(self, args: str, target: str) -> str:
        """Convert function arguments."""
        if not args or not args.strip():
            return ""

        arg_list = self._parse_arguments(args)

        if target == "dart":
            converted = [
                self.expression_converter.convert_expression(arg.strip())
                for arg in arg_list
            ]
        else:
            converted = [
                self._convert_expression_to_python(arg.strip()) for arg in arg_list
            ]

        return ", ".join(converted)

    def _parse_arguments(self, args: str) -> list[str]:
        """Parse comma-separated arguments handling nested parentheses."""
        result = []
        current = ""
        paren_level = 0
        in_string = False
        string_char = None

        for char in args:
            if char in "\"'":
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
            elif not in_string:
                if char == "(":
                    paren_level += 1
                elif char == ")":
                    paren_level -= 1
                elif char == "," and paren_level == 0:
                    result.append(current)
                    current = ""
                    continue

            current += char

        if current:
            result.append(current)

        return result

    def _convert_array_literal(self, literal: str, _element_type: str) -> str:
        """Convert array literal syntax."""
        # Handle PowerBuilder array syntax like {1, 2, 3}
        if literal.startswith("{") and literal.endswith("}"):
            return "[" + literal[1:-1] + "]"
        return literal

    def _get_indent_change(self, line: str) -> int:
        """Determine indentation change for control flow."""
        line_lower = line.lower().strip()

        # Opening statements
        if any(
            line_lower.startswith(kw)
            for kw in ["if ", "for ", "do ", "while ", "try", "choose case"]
        ):
            if not line_lower.endswith("then"):
                return 0
            return 1

        # Closing statements
        if any(
            line_lower.startswith(kw)
            for kw in ["end if", "next", "loop", "end try", "end choose"]
        ):
            return -1

        # Middle statements
        if any(
            line_lower.startswith(kw)
            for kw in ["else", "elseif", "catch", "finally", "case"]
        ):
            return 0

        return 0

    def _pb_to_python_type(self, pb_type: str) -> str:
        """Convert PowerBuilder type to Python type annotation."""
        type_map = {
            "string": "str",
            "integer": "int",
            "int": "int",
            "long": "int",
            "decimal": "float",
            "real": "float",
            "double": "float",
            "boolean": "bool",
            "datetime": "datetime",
            "date": "date",
            "time": "time",
            "char": "str",
            "blob": "bytes",
        }
        return type_map.get(pb_type.lower(), "Any")

    def _get_dart_default(self, dart_type: str) -> str:
        """Get default value for Dart type."""
        defaults = {
            "int": "0",
            "double": "0.0",
            "String": "''",
            "bool": "false",
            "DateTime": "DateTime.now()",
            "List": "[]",
            "Map": "{}",
        }
        return defaults.get(dart_type, "null")

    def _get_python_default(self, python_type: str) -> str:
        """Get default value for Python type."""
        defaults = {
            "int": "0",
            "float": "0.0",
            "str": '""',
            "bool": "False",
            "datetime": "datetime.now()",
            "date": "date.today()",
            "time": "time()",
            "list": "[]",
            "dict": "{}",
            "bytes": 'b""',
        }
        return defaults.get(python_type, "None")

    def _is_async_method(
        self, method_name: str, _context: dict[str, Any] | None = None
    ) -> bool:
        """Check if method requires async."""
        # Methods that typically require async
        async_patterns = [
            "fetch",
            "load",
            "save",
            "get",
            "post",
            "put",
            "delete",
            "query",
            "execute",
            "commit",
            "rollback",
            "connect",
        ]

        method_lower = method_name.lower()
        return any(pattern in method_lower for pattern in async_patterns)

    def _generate_dart_db_op(self, statement: str) -> str:
        """Generate Dart database operation (simplified)."""
        statement_lower = statement.lower().strip()

        # Handle different SQL operations
        if statement_lower.startswith("insert"):
            return f'''// Insert operation
    await database.execute(
      """
      {statement}
      """
    );'''
        if statement_lower.startswith("update"):
            return f'''// Update operation
    final rowsAffected = await database.execute(
      """
      {statement}
      """
    );'''
        if statement_lower.startswith("delete"):
            return f'''// Delete operation
    final rowsDeleted = await database.execute(
      """
      {statement}
      """
    );'''
        if statement_lower.startswith("select"):
            return f'''// Query operation
    final results = await database.query(
      """
      {statement}
      """
    );'''
        if statement_lower == "commit":
            return "// Commit transaction\nawait database.commit();"
        if statement_lower == "rollback":
            return "// Rollback transaction\nawait database.rollback();"
        return f'''// Database operation
    final result = await database.execute(
      """
      {statement}
      """
    );'''

    def _generate_python_db_op(self, statement: str) -> str:
        """Generate Python database operation (simplified)."""
        statement_lower = statement.lower().strip()

        # Handle different SQL operations
        if statement_lower.startswith("insert"):
            return f'''# Insert operation
    session.execute(
        """
        {statement}
        """
    )
    session.commit()'''
        if statement_lower.startswith("update"):
            return f'''# Update operation
    rows_affected = session.execute(
        """
        {statement}
        """
    ).rowcount
    session.commit()'''
        if statement_lower.startswith("delete"):
            return f'''# Delete operation
    rows_deleted = session.execute(
        """
        {statement}
        """
    ).rowcount
    session.commit()'''
        if statement_lower.startswith("select"):
            return f'''# Query operation
    results = session.execute(
        """
        {statement}
        """
    ).fetchall()'''
        if statement_lower == "commit":
            return "# Commit transaction\nsession.commit()"
        if statement_lower == "rollback":
            return "# Rollback transaction\nsession.rollback()"
        return f'''# Database operation
    result = session.execute(
        """
        {statement}
        """
    )'''
