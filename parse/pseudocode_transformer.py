"""Transform pseudocode AST to Python code."""

import logging
import subprocess
from pathlib import Path
from typing import Any

from lark import Transformer, v_args

logger = logging.getLogger(__name__)


@v_args(inline=True)
class PseudocodeToPython(Transformer):
    """Transform pseudocode AST to Python code."""

    def __init__(self) -> None:
        """Initialize transformer with type mapping and state."""
        super().__init__()
        self.indent_level = 0
        self.declared_variables: dict[str, str] = {}
        self.type_map = {
            "INTEGER": "int",
            "REAL": "float",
            "STRING": "str",
            "BOOLEAN": "bool",
            "CHAR": "str",
            "FILE": "TextIO",
            "ERROR": "Exception",
        }
        self.current_function: str | None = None
        self.error_handlers: dict[str, list[str]] = {}

    def indent(self) -> str:
        """Get current indentation string."""
        return "    " * self.indent_level

    def format_code(self, code: str) -> str:
        """Format Python code using Ruff."""
        try:
            # Write code to temporary file
            temp_file = Path("temp_code.py")
            temp_file.write_text(code)

            # Format with Ruff
            subprocess.run(["ruff", "format", "temp_code.py"], check=True)

            # Read formatted code
            formatted = temp_file.read_text()

            # Clean up
            temp_file.unlink()

            return formatted
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to format code with Ruff: %s", str(e))
            return code
        except OSError as e:
            logger.warning("File operation error during code formatting: %s", str(e))
            return code
        except Exception as e:
            logger.exception("Unexpected error during code formatting: %s", str(e))
            return code

    def transform(self, tree: Any) -> list[str]:
        """Transform AST to Python code with formatting."""
        lines = super().transform(tree)
        if isinstance(lines, list):
            code = "\n".join(lines)
            return self.format_code(code).splitlines()
        return lines

    def start(self, *stmts) -> list[str]:
        """Transform start rule."""
        return [line for stmt in stmts for line in stmt if line]

    # Declarations
    def declaration(self, name: str, type_spec: str, *init) -> list[str]:
        """Transform variable declaration."""
        if name not in self.declared_variables:
            self.declared_variables[name] = type_spec
            if type_spec.startswith("ARRAY"):
                return self._handle_array_declaration(name, type_spec)
            py_type = self.type_map.get(type_spec, "Any")
            if init:
                return [f"{name}: {py_type} = {init[0]}"]
            return [f"{name}: {py_type} = {self._default_value(type_spec)}"]
        return []

    def _handle_array_declaration(self, name: str, type_spec: str) -> list[str]:
        """Handle array declaration."""
        array_parts = type_spec.split("OF", 1)
        size = array_parts[0].replace("ARRAY[", "").replace("]", "").strip()
        elem_type = array_parts[1].strip()

        if elem_type.startswith("ARRAY"):
            inner_decl = self._handle_array_declaration(name, elem_type)[0]
            inner_init = inner_decl.split(" = ", 1)[1]
            return [f"{name} = [{inner_init} for _ in range({size})]"]

        default = self._default_value(elem_type)
        return [f"{name} = [{default} for _ in range({size})]"]

    def _default_value(self, type_spec: str) -> str:
        """Get default value for type."""
        defaults = {
            "INTEGER": "0",
            "REAL": "0.0",
            "STRING": '""',
            "BOOLEAN": "False",
            "CHAR": '""',
        }
        return defaults.get(type_spec, "None")

    # Control flow
    def if_stmt(self, cond, then_block, *rest) -> list[str]:
        """Transform if statement."""
        lines = [f"if {cond}:"]
        self.indent_level += 1
        lines.extend(f"{self.indent()}{line}" for line in then_block)
        self.indent_level -= 1
        if rest:
            else_block = rest[0]
            lines.append("else:")
            self.indent_level += 1
            lines.extend(f"{self.indent()}{line}" for line in else_block)
            self.indent_level -= 1
        return lines

    def while_stmt(self, cond, body) -> list[str]:
        """Transform while statement."""
        lines = [f"while {cond}:"]
        self.indent_level += 1
        lines.extend(f"{self.indent()}{line}" for line in body)
        self.indent_level -= 1
        return lines

    def for_stmt(self, var, start, end, *rest) -> list[str]:
        """Transform for statement."""
        step = rest[0] if rest and not isinstance(rest[0], list) else "1"
        body = rest[-1] if isinstance(rest[-1], list) else []
        lines = [f"for {var} in range({start}, {end} + 1, {step}):"]
        self.indent_level += 1
        lines.extend(f"{self.indent()}{line}" for line in body)
        self.indent_level -= 1
        return lines

    def foreach_stmt(self, var, collection, body) -> list[str]:
        """Transform foreach statement."""
        lines = [f"for {var} in {collection}:"]
        self.indent_level += 1
        lines.extend(f"{self.indent()}{line}" for line in body)
        self.indent_level -= 1
        return lines

    def repeat_stmt(self, body, cond) -> list[str]:
        """Transform repeat-until statement."""
        lines = ["while True:"]
        self.indent_level += 1
        lines.extend(f"{self.indent()}{line}" for line in body)
        lines.append(f"{self.indent()}if {cond}:")
        lines.append(f"{self.indent()}    break")
        self.indent_level -= 1
        return lines

    def case_stmt(self, expr, *items) -> list[str]:
        """Transform case statement."""
        lines = [f"match {expr}:"]
        self.indent_level += 1
        for item in items:
            if isinstance(item, tuple):  # Case branch
                value, stmts = item
                lines.append(f"{self.indent()}case {value}:")
                self.indent_level += 1
                lines.extend(f"{self.indent()}{line}" for line in stmts)
                self.indent_level -= 1
            else:  # Else block
                lines.append(f"{self.indent()}case _:")
                self.indent_level += 1
                lines.extend(f"{self.indent()}{line}" for line in item)
                self.indent_level -= 1
        self.indent_level -= 1
        return lines

    # Functions and procedures
    def function_def(self, name, params, return_type, *body) -> list[str]:
        """Transform function definition."""
        self.current_function = str(name)
        param_list = []
        throws = []
        body = []

        # Process parameters and body
        for item in body:
            if isinstance(item, tuple) and item[0] == "THROWS":
                throws = item[1:]
            else:
                body.extend(item if isinstance(item, list) else [item])

        # Build parameter list
        for param_name, param_type, *direction in params or []:
            py_type = self.type_map.get(str(param_type), "Any")
            direction = direction[0] if direction else None
            if direction == "OUT":
                param_list.append(
                    f"{param_name}: List[{py_type}]",
                )  # Use list for out parameters
            else:
                param_list.append(f"{param_name}: {py_type}")

        # Build function header
        py_return_type = self.type_map.get(str(return_type), "Any")
        lines = [f"def {name}({', '.join(param_list)}) -> {py_return_type}:"]

        # Add docstring with throws information
        if throws:
            self.indent_level += 1
            lines.append(f'{self.indent()}"""')
            lines.append(f"{self.indent()}Args:")
            for param_name, param_type, *direction in params or []:
                direction = direction[0] if direction else "IN"
                lines.append(
                    f"{self.indent()}    {param_name}: Parameter direction: {direction}",
                )
            if throws:
                lines.append(f"{self.indent()}")
                lines.append(f"{self.indent()}Raises:")
                for error in throws:
                    lines.append(f"{self.indent()}    {error}: If an error occurs")
            lines.append(f'{self.indent()}"""')
            self.indent_level -= 1

        # Add function body
        self.indent_level += 1
        lines.extend(f"{self.indent()}{line}" for line in body)
        self.indent_level -= 1

        self.current_function = None
        return lines

    def procedure_def(self, name, params, *body) -> list[str]:
        """Transform procedure definition."""
        return self.function_def(name, params, "None", *body)

    # Basic statements
    def assignment(self, var, _, expr) -> list[str]:
        """Transform assignment statement."""
        if isinstance(var, tuple):  # Array assignment
            array, index = var
            return [f"{array}[{index}] = {expr}"]
        return [f"{var} = {expr}"]

    def input_stmt(self, var) -> list[str]:
        """Transform input statement with type casting."""
        var_type = self.declared_variables.get(str(var))
        if var_type in self.type_map:
            cast = self.type_map[var_type]
            return [f"{var} = {cast}(input('Enter {var}: '))"]
        return [f"{var} = input('Enter {var}: ')"]

    def output_stmt(self, value_list) -> list[str]:
        """Transform output statement with string interpolation."""
        values = []
        needs_f = False
        for value in value_list:
            if isinstance(value, str) and value.startswith('"'):
                values.append(value.strip('"'))
            else:
                needs_f = True
                values.append(f"{{{value}}}")

        if len(values) == 1 and not needs_f:
            return [f'print("{values[0]}")']
        return [f'print(f"{"".join(values)}")']

    def return_stmt(self, *args) -> list[str]:
        """Transform return statement."""
        return [f"return {args[0]}" if args else "return"]

    # File operations
    def file_open(self, *args) -> list[str]:
        """Transform file open statement."""
        file_var, mode_spec, *sharing = args
        mode = str(mode_spec).lower()
        mode_map = {
            "read": "r",
            "write": "w",
            "append": "a",
            "random": "r+",
        }
        mode_str = mode_map.get(mode, "r")
        if sharing:
            sharing_mode = str(sharing[0]).lower()
            if sharing_mode == "exclusive":
                return [
                    f"{file_var} = open({file_var}_path, '{mode_str}', opener=lambda p, f: os.open(p, f | os.O_EXCL))",
                ]
            if sharing_mode == "readonly":
                return [f"{file_var} = open({file_var}_path, 'r')"]
        return [f"{file_var} = open({file_var}_path, '{mode_str}')"]

    def file_read(self, *args) -> list[str]:
        """Transform file read statement."""
        file_var, into_var, *size = args
        if size:
            return [f"{into_var} = {file_var}.read({size[0]})"]
        return [f"{into_var} = {file_var}.read()"]

    def file_write(self, *args) -> list[str]:
        """Transform file write statement."""
        file_var, expr, *append = args
        if append:
            return [
                f"{file_var}.seek(0, 2)",  # Seek to end
                f"{file_var}.write(str({expr}))",
            ]
        return [f"{file_var}.write(str({expr}))"]

    def file_close(self, file_var) -> list[str]:
        """Transform file close statement."""
        return [f"{file_var}.close()"]

    def file_seek(self, file_var, pos) -> list[str]:
        """Transform file seek statement."""
        return [f"{file_var}.seek({pos})"]

    def file_status(self, file_var, into_var) -> list[str]:
        """Transform file status statement."""
        return [
            f"{into_var} = {{'exists': os.path.exists({file_var}_path),",
            f"           'size': os.path.getsize({file_var}_path),",
            f"           'mode': os.stat({file_var}_path).st_mode}}",
        ]

    def file_access(self, var, op) -> str:
        """Transform file access expression."""
        op = str(op).lower()
        if op == "read":
            return f"{var}.read()"
        if op == "write":
            return f"{var}.write"
        if op == "seek":
            return f"{var}.seek"
        # status
        return f"os.stat({var}_path)"

    # Expressions
    def or_expr(self, *args) -> str:
        """Transform OR expression."""
        return f"({' or '.join(str(arg) for arg in args)})"

    def and_expr(self, *args) -> str:
        """Transform AND expression."""
        return f"({' and '.join(str(arg) for arg in args)})"

    def not_expr(self, expr) -> str:
        """Transform NOT expression."""
        return f"(not {expr})"

    def comparison(self, left, op, right) -> str:
        """Transform comparison expression."""
        op_map = {
            "=": "==",
            "<>": "!=",
            "LIKE": "like",
        }
        op = op_map.get(op, op)
        return f"{left} {op} {right}"

    def arith_expr(self, *args) -> str:
        """Transform arithmetic expression."""
        if len(args) == 1:
            return str(args[0])
        result = []
        for i in range(0, len(args), 2):
            result.append(str(args[i]))
            if i + 1 < len(args):
                result.append(str(args[i + 1]))
        return "".join(result)

    # Built-in functions
    def builtin_func(self, func, *args) -> str:
        """Transform built-in function calls."""
        func_name = str(func).lower()
        args_str = ", ".join(str(arg) for arg in args)

        if func_name == "length":
            return f"len({args_str})"
        if func_name in {"lcase", "ucase"}:
            method = "lower" if func_name == "lcase" else "upper"
            return f"str({args[0]}).{method}()"
        if func_name == "substring":
            if len(args) == 2:
                return f"str({args[0]})[{args[1]}:]"
            return f"str({args[0]})[{args[1]}:{args[1]} + {args[2]}]"
        if func_name == "round":
            if len(args) == 1:
                return f"round({args[0]})"
            return f"round({args[0]}, {args[1]})"
        if func_name == "random":
            if not args:
                return "random.random()"
            return f"random.randint(1, {args[0]})"
        if func_name == "div":
            return f"({args[0]} // {args[1]})"
        if func_name == "mod":
            return f"({args[0]} % {args[1]})"
        if func_name == "eof":
            return f"{args[0]}.tell() >= os.path.getsize({args[0]}_path)"
        if func_name == "filesize":
            return f"os.path.getsize({args[0]}_path)"
        if func_name == "filetype":
            return f"os.path.splitext({args[0]}_path)[1]"
        if func_name == "filemode":
            return f"os.stat({args[0]}_path).st_mode"

        return f"{func_name}({args_str})"

    # Terminals
    def int_literal(self, token) -> str:
        """Transform integer literal."""
        return str(token)

    def float_literal(self, token) -> str:
        """Transform float literal."""
        return str(token)

    def string_literal(self, token) -> str:
        """Transform string literal."""
        return str(token)

    def char_literal(self, token) -> str:
        """Transform char literal."""
        return str(token)

    def true_literal(self, _) -> str:
        """Transform true literal."""
        return "True"

    def false_literal(self, _) -> str:
        """Transform false literal."""
        return "False"

    def null_literal(self, _) -> str:
        """Transform null literal."""
        return "None"

    def var(self, token) -> str:
        """Transform variable reference."""
        return str(token)

    def array_access(self, array, index) -> str:
        """Transform array access."""
        return f"{array}[{index}]"

    def cast_expr(self, type_spec, expr) -> str:
        """Transform type cast expression."""
        py_type = self.type_map.get(str(type_spec), "Any")
        return f"{py_type}({expr})"

    # Error handling
    def try_stmt(self, *items) -> list[str]:
        """Transform try statement."""
        lines = ["try:"]
        self.indent_level += 1

        # Process try block
        try_block = []
        catch_blocks = []
        finally_block = None

        for item in items:
            if isinstance(item, tuple) and item[0] == "CATCH":
                catch_blocks.append(item)
            elif isinstance(item, tuple) and item[0] == "FINALLY":
                finally_block = item[1]
            else:
                try_block.extend(item if isinstance(item, list) else [item])

        # Add try block
        lines.extend(f"{self.indent()}{line}" for line in try_block)
        self.indent_level -= 1

        # Add catch blocks
        for catch in catch_blocks:
            _, var, type_spec, stmts = catch
            py_type = self.type_map.get(str(type_spec), "Exception")
            lines.append(f"except {py_type} as {var}:")
            self.indent_level += 1
            lines.extend(f"{self.indent()}{line}" for line in stmts)
            self.indent_level -= 1

        # Add finally block
        if finally_block:
            lines.append("finally:")
            self.indent_level += 1
            lines.extend(f"{self.indent()}{line}" for line in finally_block)
            self.indent_level -= 1

        return lines

    def raise_stmt(self, expr) -> list[str]:
        """Transform raise statement."""
        return [f"raise {expr}"]

    def handle_stmt(self, error_type, *stmts) -> list[str]:
        """Transform handle statement."""
        if self.current_function:
            self.error_handlers.setdefault(self.current_function, []).append(
                str(error_type),
            )
        return [f"# Error handler for {error_type}", *list(stmts)]
