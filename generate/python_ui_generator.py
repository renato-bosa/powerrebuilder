"""Python UI code generator for PowerBuilder windows.

Generates Python Tkinter code from PowerBuilder window definitions.
"""

import logging
from typing import Any

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET
from generate.base_generator import CodeGenerator
from generate.layout_converter import LayoutConverter, LayoutStrategy

logger = logging.getLogger(__name__)


class PythonTypeConverter:
    """Convert PowerBuilder types to Python types."""

    def __init__(self) -> None:


        self.type_map = {
            # Basic types
            "integer": "int", "long": "int", "decimal": "float", "real": "float", "double": "float", "boolean": "bool", "string": "str", "char": "str", "date": "datetime.date", "time": "datetime.time", "datetime": "datetime.datetime", "blob": "bytes", # PowerBuilder specific
            "any": "Any", "powerobject": "object", "datawindow": "DataWindowWidget", "transaction": "Transaction", # Arrays
            "integer[]": "list[int]", "string[]": "list[str]", "decimal[]": "list[float]", }

    def convert_type(self, pb_type: str) -> str:




        """Convert PowerBuilder type to Python type."""
        if not pb_type:
            return "Any"

        pb_type_lower = pb_type.lower().strip()

        # Check direct mapping
        if pb_type_lower in self.type_map:
            return self.type_map[pb_type_lower]

        # Handle arrays
        if pb_type_lower.endswith("[]"):
            base_type = pb_type_lower[:-2]
            python_base = self.convert_type(base_type)
            return f"list[{python_base}]"

        # Default to object
        return "object"


class PythonExpressionConverter:
    """Convert PowerBuilder expressions to Python."""

    def __init__(self, type_converter: PythonTypeConverter) -> None:


        self.type_converter = type_converter

        # PowerBuilder to Python operator mappings
        self.operator_map = {
            "=": "==", "<>": "!=", "and": "and", "or": "or", "not": "not", "mod": "%", "^": "**", # Power operator
        }

        # PowerBuilder to Python function mappings
        self.function_map = {
            # String functions
            "len": "len", "trim": ".strip()", "ltrim": ".lstrip()", "rtrim": ".rstrip()", "upper": ".upper()", "lower": ".lower()", "mid": self._convert_mid, # Custom handler
            "pos": ".find", "replace": ".replace", "string": "str", # Numeric functions
            "abs": "abs", "ceiling": "math.ceil", "int": "int", "round": "round", "truncate": "math.trunc", "integer": "int", "double": "float", "decimal": "float", # Date/Time functions
            "today": "datetime.date.today()", "now": "datetime.datetime.now()", # Type checking
            "isnull": "is None", "isvalid": "is not None", "setnull": "= None", # MessageBox
            "messagebox": "messagebox.showinfo", }

    def convert_expression(self, pb_expr: str) -> str:




        """Convert PowerBuilder expression to Python."""
        if not pb_expr:
            return ""

        import re

        result = pb_expr

        # Convert NULL handling
        result = re.sub(r"IsNull\s*\(\s*([^)]+)\s*\)", r"(\1 is None)", result, flags=re.IGNORECASE)
        result = re.sub(r"IsValid\s*\(\s*([^)]+)\s*\)", r"(\1 is not None)", result, flags=re.IGNORECASE)
        result = re.sub(r"SetNull\s*\(\s*([^)]+)\s*\)", r"\1 = None", result, flags=re.IGNORECASE)

        # Convert operators
        for pb_op, py_op in self.operator_map.items():
            if pb_op.isalpha():
                # Word operators need word boundaries
                pattern = rf"\b{pb_op}\b"
                result = re.sub(pattern, py_op, result, flags=re.IGNORECASE)
            else:
                # Symbol operators need careful replacement
                if pb_op == "=":
                    # Only convert = to == when it's a comparison, not assignment
                    # This should be handled in the statement converter instead
                    continue
                elif pb_op == "^":
                    # Power operator
                    result = re.sub(r"\^", "**", result)
                else:
                    # Other operators
                    result = result.replace(f" {pb_op} ", f" {py_op} ")

        # Convert function calls
        for pb_func, py_func in self.function_map.items():
            if callable(py_func):
                # Custom handler
                result = py_func(result)
            elif py_func.startswith("."):
                # Method call - e.g., trim(x) -> x.strip()
                pattern = rf"\b{pb_func}\s*\(([^)]*)\)"
                result = re.sub(pattern, rf"\1{py_func}", result, flags=re.IGNORECASE)
            else:
                # Function replacement
                pattern = rf"\b{pb_func}\s*\("
                result = re.sub(pattern, f"{py_func}(", result, flags=re.IGNORECASE)

        # Convert comparison operators in conditions
        # Only convert = to == when not in assignment context
        import re
        # In conditions (after IF, WHILE, etc.), convert = to ==
        result = re.sub(r"(\bif\s+.*)\s=\s", r"\1 == ", result, flags=re.IGNORECASE)
        result = re.sub(r"(\bwhile\s+.*)\s=\s", r"\1 == ", result, flags=re.IGNORECASE)
        result = re.sub(r"(\belif\s+.*)\s=\s", r"\1 == ", result, flags=re.IGNORECASE)

        # Convert control structures
        result = self._convert_control_structures(result)

        # Convert property access
        result = self._convert_property_access(result)

        return result

    def _convert_mid(self, expr: str) -> str:




        """Convert MID function to Python slice."""
        import re
        pattern = r"mid\s*\(\s*([^, ]+), \s*([^, ]+), \s*([^)]+)\s*\)"

        def replace_mid(match):


            string_var = match.group(1).strip()
            start = match.group(2).strip()
            length = match.group(3).strip()
            # PowerBuilder uses 1-based indexing
            return f"{string_var}[{start}-1:({start}-1)+{length}]"

        return re.sub(pattern, replace_mid, expr, flags=re.IGNORECASE)

    def _convert_control_structures(self, expr: str) -> str:




        """Convert PowerBuilder control structures to Python."""
        import re

        # IF...THEN...END IF
        expr = re.sub(r"\bIF\b", "if", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bTHEN\b", ":", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bEND\s+IF\b", "", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bELSEIF\b", "elif", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bELSE\b(?!:)", "else:", expr, flags=re.IGNORECASE)

        # FOR...TO...NEXT
        expr = re.sub(r"\bFOR\s+(\w+)\s*=\s*(\d+)\s+TO\s+(\d+)\b", r"for \1 in range(\2, \3 + 1):", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bNEXT\b", "", expr, flags=re.IGNORECASE)

        # DO WHILE...LOOP
        expr = re.sub(r"\bDO\s+WHILE\b", "while", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bLOOP\b", "", expr, flags=re.IGNORECASE)

        # CHOOSE CASE...END CHOOSE
        expr = re.sub(r"\bCHOOSE\s+CASE\s+(.+)\b", r"match \1:", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bCASE\s+(.+)\b", r"case \1:", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bCASE\s+ELSE\b", "case _:", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bEND\s+CHOOSE\b", "", expr, flags=re.IGNORECASE)

        return expr

    def _convert_property_access(self, expr: str) -> str:




        """Convert PowerBuilder property access patterns."""
        import re

        # Convert this. to self.
        expr = re.sub(r"\bthis\.", "self.", expr, flags=re.IGNORECASE)

        # Convert parent. to self.parent.
        expr = re.sub(r"\bparent\.", "self.parent.", expr, flags=re.IGNORECASE)

        # Convert PowerBuilder constants
        expr = re.sub(r"\bTRUE\b", "True", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bFALSE\b", "False", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bNULL\b", "None", expr, flags=re.IGNORECASE)

        # Convert control property access
        # control.text -> self._controls['control'].get() or .config(text=...)
        control_props = {
            ".text": ".get()", ".enabled": "['state'] != 'disabled'", ".visible": ".winfo_viewable()", ".checked": ".var.get()", }

        for pb_prop, py_prop in control_props.items():
            expr = expr.replace(pb_prop, py_prop)

        return expr


class PythonUIGenerator(CodeGenerator):
    """Generate Python Tkinter UI code from PowerBuilder windows."""

    def __init__(self, template_dir: str, output_dir: str, validate_templates: bool = True) -> None:


        """Initialize Python UI generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
            validate_templates: Whether to validate templates
        """
        super().__init__(template_dir, output_dir, validate_templates)
        self.type_converter = PythonTypeConverter()
        self.expression_converter = PythonExpressionConverter(self.type_converter)
        self.layout_converter = LayoutConverter(LayoutStrategy.ABSOLUTE)

    def generate_window(self, window_model: dict) -> None:




        """Generate Python Tkinter window from model.

        Args:
            window_model: Window model from converters
        """
        # Transform to Python-specific model
        python_window = self._transform_window_model(window_model)

        # Render template
        content = self.render_template("tkinter_window.py.jinja2", {"window": python_window})

        # Write file
        window_name = window_model.get("name", "unknown")
        self.write_file(f"windows/{window_name.lower()}.py", content)

    def _transform_window_model(self, window_model: dict) -> dict:




        """Transform generic window model to Python-specific model."""
        python_window = {
            "name": self._to_python_class_name(window_model.get("name", "UnknownWindow")), "title": window_model.get("title", ""), "width": 800, # Default size
            "height": 600, "variables": [], "controls": [], "methods": [], "menus": [], "has_menu": False, "has_datawindow": False, "control_events": [], "open_event": None, "close_event": None, }

        # Convert variables
        for var in window_model.get("variables", []):
            python_window["variables"].append({
                "name": var.get("name", ""), "python_type": self.type_converter.convert_type(var.get("type", "any")), "initial_value": self._convert_initial_value(var.get("initial_value")), })

        # Convert controls
        for control in window_model.get("controls", []):
            python_control = self._transform_control(control)
            python_window["controls"].append(python_control)

            if python_control["type"] == "datawindow":
                python_window["has_datawindow"] = True

        # Convert events
        for event in window_model.get("events", []):
            event_name = event.get("name", "")
            if event_name == "open":
                python_window["open_event"] = self._convert_event_body(event.get("body", []))
            elif event_name == "close":
                python_window["close_event"] = self._convert_event_body(event.get("body", []))
            else:
                # Control event
                control_name, event_type = self._parse_control_event(event_name)
                if control_name:
                    python_window["control_events"].append({
                        "control": control_name, "event_name": event_type, "event_type": event_type, })

                    # Add event handler to control
                    for control in python_window["controls"]:
                        if control["name"] == control_name:
                            control[f"{event_type}_event"] = self._convert_event_body(event.get("body", []))

        # Convert methods
        for method in window_model.get("methods", []):
            python_window["methods"].append({
                "name": method.get("name", ""), "params": self._convert_parameters(method.get("parameters", [])), "body": self._convert_method_body(method.get("body", [])), "description": f"PowerBuilder method: {method.get("name", "")}", })

        # Set window to use absolute positioning if controls have position data
        if python_window["controls"] and "position" in window_model.get("controls", [{}])[0]:
            for control in python_window["controls"]:
                control["use_absolute_position"] = True

        return python_window

    def _transform_control(self, control: dict) -> dict:




        """Transform PowerBuilder control to Python Tkinter control."""
        pb_type = control.get("type", "").lower()
        flutter_widget = control.get("flutter_widget", {})
        position = control.get("position", {})
        size = control.get("size", {})

        python_control = {
            "name": control.get("name", ""), "type": pb_type, "text": flutter_widget.get("flutter_properties", {}).get("text", ""), "enabled": flutter_widget.get("flutter_properties", {}).get("enabled", True), "x": position.get("x", 0), "y": position.get("y", 0), "width": size.get("width"), "height": size.get("height"), }

        # Type-specific properties
        if pb_type == "checkbox":
            python_control["checked"] = flutter_widget.get("flutter_properties", {}).get("checked", False)
        elif pb_type in ["dropdownlistbox", "listbox"]:
            python_control["items"] = flutter_widget.get("flutter_properties", {}).get("items", [])
            if pb_type == "listbox":
                python_control["multiselect"] = flutter_widget.get("flutter_properties", {}).get("multiselect", False)
        elif pb_type == "datawindow":
            python_control["dataobject"] = flutter_widget.get("flutter_properties", {}).get("dataobject", "")

        return python_control

    def _convert_event_body(self, body: list[str]) -> str:




        """Convert event body from PowerScript to Python."""
        if not body:
            return "pass"

        python_lines = []
        indent_level = 0

        for statement in body:
            # Skip empty lines and comments
            stripped = statement.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # Handle indentation for control structures
            if any(stripped.upper().startswith(end) for end in ["END IF", "NEXT", "LOOP", "END CHOOSE"]):
                indent_level = max(0, indent_level - 1)

            # Convert the statement
            converted = self._convert_statement(stripped)

            if converted and converted.strip():  # Only add non-empty statements
                # Add proper indentation
                python_lines.append("    " * indent_level + converted)

            # Increase indentation after control structure starts
            if converted and converted.endswith(":"):
                indent_level += 1

        return "\n".join(python_lines) if python_lines else "pass"

    def _convert_statement(self, statement: str) -> str:




        """Convert a single PowerBuilder statement to Python."""
        import re

        # Skip comment lines
        if statement.strip().startswith("//"):
            return f"# {statement.strip()[2:].strip()}"

        # Handle RETURN statements
        if statement.upper().startswith("RETURN"):
            match = re.match(r"RETURN\s*(.*)", statement, re.IGNORECASE)
            if match and match.group(1):
                value = self.expression_converter.convert_expression(match.group(1))
                return f"return {value}"
            else:
                return "return"

        # Handle assignments
        if "=" in statement and not any(op in statement for op in ["==", "!=", "<=", ">=", "<>"]):
            parts = statement.split("=", 1)
            if len(parts) == 2:
                lhs = parts[0].strip()
                rhs = parts[1].strip()

                # Convert right-hand side first
                rhs_converted = self.expression_converter.convert_expression(rhs)

                # Handle control property assignments specially
                if "." in lhs:
                    lhs_parts = lhs.split(".", 1)
                    obj = lhs_parts[0].strip()
                    prop = lhs_parts[1].strip()

                    # Convert PowerBuilder constants
                    if rhs_converted.upper() in ["TRUE", "FALSE"]:
                        rhs_converted = rhs_converted.capitalize()

                    if prop.lower() == "text":
                        return f"self.set_text('{obj}', {rhs_converted})"
                    elif prop.lower() == "enabled":
                        return f"self._controls['{obj}'].config(state='normal' if {rhs_converted} else 'disabled')"
                    elif prop.lower() == "checked":
                        return f"self._controls['{obj}'].var.set({rhs_converted})"
                    else:
                        # Generic property
                        return f"self.{self._to_camel_case(obj)}.{prop} = {rhs_converted}"
                else:
                    # Variable assignment
                    lhs_converted = self._convert_lhs(lhs)
                    return f"{lhs_converted} = {rhs_converted}"

        # Handle variable declarations (ignore them for Python)
        if any(statement.upper().startswith(t) for t in ["STRING ", "INTEGER ", "BOOLEAN ", "DECIMAL ", "LONG "]):
            # Extract variable name if needed for type hints
            parts = statement.split()
            if len(parts) >= 2:
                var_name = parts[1]
                return f"# {statement}  # Variable declaration handled in __init__"
            return ""

        # Handle IF statements
        if statement.upper().startswith("IF "):
            match = re.match(r"IF\s+(.+?)\s+THEN", statement, re.IGNORECASE)
            if match:
                condition = match.group(1)
                # Convert the condition separately to avoid double conversion
                converted_condition = self._convert_condition(condition)
                return f"if {converted_condition}:"

        # Handle ELSEIF
        if statement.upper().startswith("ELSEIF "):
            match = re.match(r"ELSEIF\s+(.+?)\s+THEN", statement, re.IGNORECASE)
            if match:
                condition = match.group(1)
                converted_condition = self._convert_condition(condition)
                return f"elif {converted_condition}:"

        # Handle ELSE
        if statement.upper() == "ELSE":
            return "else:"

        # Handle FOR loops
        match = re.match(r"FOR\s+(\w+)\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+STEP\s+(.+?))?$", statement, re.IGNORECASE)
        if match:
            var = match.group(1)
            start = self.expression_converter.convert_expression(match.group(2))
            end = self.expression_converter.convert_expression(match.group(3))
            step = match.group(4)

            if step:
                step_val = self.expression_converter.convert_expression(step)
                return f"for {var} in range({start}, {end} + 1, {step_val}):"
            else:
                return f"for {var} in range({start}, {end} + 1):"

        # Handle WHILE loops
        match = re.match(r"(?:DO\s+)?WHILE\s+(.+)", statement, re.IGNORECASE)
        if match:
            condition = self.expression_converter.convert_expression(match.group(1))
            return f"while {condition}:"

        # Handle MessageBox
        if statement.upper().startswith("MESSAGEBOX"):
            return self._convert_messagebox(statement)

        # Handle Close
        if statement.upper().startswith("CLOSE("):
            match = re.match(r"CLOSE\s*\(\s*(.+?)\s*\)", statement, re.IGNORECASE)
            if match:
                window = match.group(1).strip()
                if window.upper() == "THIS":
                    return "self.destroy()"
                else:
                    return f"# Close window: {window}"

        # Handle SetFocus
        if "SetFocus" in statement:
            match = re.search(r"(\w+)\.SetFocus\s*\(\s*\)", statement, re.IGNORECASE)
            if match:
                control = match.group(1)
                control_ref = self._get_control_reference(control)
                return f"{control_ref}.focus_set()"

        # Handle method/function calls
        if "(" in statement and ")" in statement:
            # Convert the expression
            converted = self.expression_converter.convert_expression(statement)
            return converted

        # Handle control structure endings (return empty to adjust indentation)
        if statement.upper() in ["END IF", "NEXT", "LOOP", "END CHOOSE"]:
            return ""

        # Default: try expression converter
        try:
            converted = self.expression_converter.convert_expression(statement)
            return converted
        except Exception as e:
            return f"# TODO: {statement}"

    def _convert_lhs(self, lhs: str) -> str:




        """Convert left-hand side of assignment."""
        # Handle control property assignments
        if "." in lhs:
            parts = lhs.split(".", 1)
            obj = parts[0].strip()
            prop = parts[1].strip()

            # Check if it's a control
            if prop.lower() == "text":
                control_ref = self._get_control_reference(obj)
                return f"self.set_text('{obj}', value)"  # Will need to fix the value part
            elif prop.lower() == "enabled":
                control_ref = self._get_control_reference(obj)
                return f"{control_ref}.config(state='normal' if value else 'disabled')"
            else:
                # Generic property
                return f"self.{self._to_camel_case(obj)}.{prop}"
        else:
            # Variable assignment
            if lhs.lower() in ["this", "self"]:
                return "self"
            else:
                # Check if it's an instance variable
                return f"self.{self._to_camel_case(lhs)}"

    def _get_control_reference(self, control_name: str) -> str:




        """Get the Python reference for a control."""
        return f"self._controls['{control_name}']"

    def _convert_messagebox(self, statement: str) -> str:




        """Convert MessageBox to Python."""
        import re

        # Try to parse MessageBox parameters
        match = re.search(r'MessageBox\s*\(\s*["\']([^"\']+)["\']\s*, \s*["\']([^"\']+)["\']\s*\)', statement, re.IGNORECASE)
        if match:
            title = match.group(1)
            message = match.group(2)
            return f'messagebox.showinfo("{title}", "{message}")'

        # Single parameter version
        match = re.search(r'MessageBox\s*\(\s*["\']([^"\']+)["\']\s*\)', statement, re.IGNORECASE)
        if match:
            message = match.group(1)
            return f'messagebox.showinfo("Information", "{message}")'

        # Variable parameters
        match = re.search(r"MessageBox\s*\(\s*(.+?)\s*, \s*(.+?)\s*\)", statement, re.IGNORECASE)
        if match:
            title = self.expression_converter.convert_expression(match.group(1).strip())
            message = self.expression_converter.convert_expression(match.group(2).strip())
            return f"messagebox.showinfo({title}, {message})"

        return "# " + statement

    def _to_camel_case(self, name: str) -> str:




        """Convert snake_case to camelCase."""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    def _convert_condition(self, condition: str) -> str:




        """Convert a PowerBuilder condition to Python."""
        # First convert the expression
        converted = self.expression_converter.convert_expression(condition)

        # Fix common issues
        converted = converted.replace("self.if", "").strip()
        converted = converted.replace(" :", "").strip()

        # Handle control property access in conditions
        import re
        # Replace control.text with proper access
        converted = re.sub(r"(\w+)\.get\(\)", lambda m: f"self._controls['{m.group(1)}'].get()", converted)

        # Fix standalone trim that wasn't converted
        converted = re.sub(r"\btrim\s*\(", ".strip(", converted, flags=re.IGNORECASE)

        # Fix isnull that might still be there
        converted = re.sub(r"\bisnull\s*\(([^)]+)\)", r"(\1 is None)", converted, flags=re.IGNORECASE)

        # Fix OR/AND that might remain
        converted = re.sub(r"\bor\b", "or", converted, flags=re.IGNORECASE)
        converted = re.sub(r"\band\b", "and", converted, flags=re.IGNORECASE)

        # Fix comparison operators
        converted = re.sub(r"\s=\s", " == ", converted)

        return converted

    def _convert_method_body(self, body: list[str]) -> str:




        """Convert method body from PowerScript to Python."""
        return self._convert_event_body(body)

    def _convert_parameters(self, params: list[dict]) -> str:




        """Convert method parameters to Python signature."""
        if not params:
            return ""

        param_list = []
        for param in params:
            name = param.get("name", "")
            pb_type = param.get("type", "any")
            python_type = self.type_converter.convert_type(pb_type)

            # Python 3 type hints
            param_list.append(f"{name}: {python_type}")

        return ", ".join(param_list)

    def _convert_initial_value(self, value: Any) -> str:




        """Convert initial value to Python literal."""
        if value is None:
            return "None"
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "True" if value else "False"
        else:
            return str(value)

    def _to_python_class_name(self, name: str) -> str:




        """Convert PowerBuilder name to Python class name."""
        # Remove common prefixes
        name = name.lstrip("w_").lstrip("uo_")

        # Convert to PascalCase
        parts = name.split("_")
        return "".join(part.capitalize() for part in parts)

    def _parse_control_event(self, event_name: str) -> tuple:




        """Parse control.event notation."""
        if "." in event_name:
            parts = event_name.split(".", 1)
            return parts[0], parts[1]
        return None, event_name
