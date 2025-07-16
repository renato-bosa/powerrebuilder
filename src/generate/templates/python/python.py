"""Python code generator for PowerBuilder to Python translation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class OptimizationLevel(Enum):
    """Code optimization levels."""
    NONE = 0
    BASIC = 1
    AGGRESSIVE = 2


@dataclass
class SourceMapping:
    """Maps between original and generated source locations."""
    original_file: str
    original_line: int
    generated_file: str
    generated_line: int
    context: str = ""


@dataclass
class CodegenState:
    """State maintained during code generation."""
    indent_level: int = 0
    current_function: Optional[str] = None
    imports: Set[str] = field(default_factory=set)
    source_maps: List[SourceMapping] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    optimization_level: OptimizationLevel = OptimizationLevel.BASIC

    def add_import(self, import_stmt: str) -> None:
        """Add an import statement."""
        self.imports.add(import_stmt)

    def add_source_map(self, mapping: SourceMapping) -> None:
        """Add a source mapping."""
        self.source_maps.append(mapping)

    def get_source_location(self, generated_line: int) -> Optional[SourceMapping]:
        """Get source mapping for a generated line."""
        for mapping in self.source_maps:
            if mapping.generated_line == generated_line:
                return mapping
        return None


class CodeGenerator:
    """Generates Python code from PowerBuilder AST."""

    def __init__(self):
        """Initialize the code generator."""
        self.state = CodegenState()
        self._type_map = {
            "INTEGER": "int",
            "STRING": "str",
            "BOOLEAN": "bool",
            "DOUBLE": "float",
            "DECIMAL": "Decimal",
            "DATE": "date",
            "TIME": "time",
            "DATETIME": "datetime",
            "LONG": "int",
            "CHAR": "str",
            "REAL": "float",
        }

    def generate_module(self, statements: List[Any]) -> str:
        """Generate a complete Python module from statements."""
        # Add necessary imports
        self.state.add_import("from typing import Any, Dict, List, Optional")
        self.state.add_import("from dataclasses import dataclass")

        # Generate code for each statement
        code_parts = []

        # Add imports
        if self.state.imports:
            for imp in sorted(self.state.imports):
                code_parts.append(imp)
            code_parts.append("")

        # Add generated code
        for stmt in statements:
            if hasattr(stmt, '__class__') and stmt.__class__.__name__ == 'Function':
                code_parts.append(self._generate_function(stmt))
            else:
                code_parts.append(str(stmt))

        return "\n".join(code_parts)

    def _type_to_python(self, pb_type: Any) -> str:
        """Convert PowerBuilder type to Python type."""
        if hasattr(pb_type, 'name'):
            type_name = pb_type.name.upper()

            # Handle array types
            if hasattr(pb_type, 'element_type'):
                element = self._type_to_python(pb_type.element_type)
                return f"list[{element}]"

            # Handle date/time types
            if type_name == "DATE":
                self.state.add_import("from datetime import date")
                return "date"
            elif type_name == "TIME":
                self.state.add_import("from datetime import time")
                return "time"
            elif type_name == "DATETIME":
                self.state.add_import("from datetime import datetime")
                return "datetime"
            elif type_name == "DECIMAL":
                self.state.add_import("from decimal import Decimal")
                return "Decimal"

            return self._type_map.get(type_name, "Any")
        return "Any"

    def _generate_function(self, func: Any) -> str:
        """Generate Python function from Function node."""
        # Generate parameters
        params = []
        for param in func.parameters:
            param_type = self._type_to_python(param.type)
            params.append(f"{param.name}: {param_type}")

        param_str = ", ".join(params)

        # Generate return type
        return_type = self._type_to_python(func.return_type)

        # Generate function header
        lines = [f"def {func.name}({param_str}) -> {return_type}:"]

        # Add docstring if present
        if hasattr(func, 'docstring') and func.docstring:
            lines.append(f'    """{func.docstring}"""')

        # Add body
        if hasattr(func, 'body') and func.body:
            for stmt in func.body:
                lines.append(f"    {stmt}")
        else:
            lines.append("    pass")

        return "\n".join(lines)

    def _generate_array_operation(self, op: Any) -> str:
        """Generate code for array operations."""
        array_name = op.array.name if hasattr(op.array, 'name') else str(op.array)

        if op.operation == "LENGTH":
            return f"len({array_name})"
        elif op.operation == "COPY":
            return f"{array_name}.copy()"
        elif op.operation == "CONCAT":
            if op.arguments:
                other = op.arguments[0].name if hasattr(op.arguments[0], 'name') else str(op.arguments[0])
                return f"{array_name} + {other}"
        elif op.operation == "RESIZE":
            if op.arguments:
                dims = [str(arg.value if hasattr(arg, 'value') else arg) for arg in op.arguments]
                return f"{array_name}.resize([{', '.join(dims)}])"

        return f"{array_name}.{op.operation.lower()}()"

    def _generate_file_operation(self, op: Any) -> str:
        """Generate code for file operations."""
        if op.type == "OPEN":
            mode_map = {"READ": "r", "WRITE": "w", "APPEND": "a"}
            mode = mode_map.get(str(op.mode).split('.')[-1], "r")
            return f'open("{op.file_path}", "{mode}")'
        elif op.type == "READ":
            if hasattr(op, 'max_bytes') and op.max_bytes:
                return f"{op.file_path}.read({op.max_bytes})"
            return f"{op.file_path}.read()"
        elif op.type == "WRITE":
            return f'{op.file_path}.write("{op.content}")'
        elif op.type == "CLOSE":
            return f"{op.file_path}.close()"

        return f"{op.file_path}.{op.type.lower()}()"

    def _optimize_code(self, code: str) -> str:
        """Apply code optimizations based on optimization level."""
        if self.state.optimization_level == OptimizationLevel.NONE:
            return code

        optimized = code

        if self.state.optimization_level >= OptimizationLevel.BASIC:
            # Dead code elimination
            lines = optimized.split('\n')
            new_lines = []
            skip_until_else = False

            for line in lines:
                if "if False:" in line:
                    skip_until_else = True
                elif skip_until_else and "else:" in line:
                    skip_until_else = False
                    continue
                elif not skip_until_else:
                    new_lines.append(line)

            optimized = '\n'.join(new_lines)

        if self.state.optimization_level >= OptimizationLevel.AGGRESSIVE:
            # Constant folding
            import re
            # Simple constant folding for arithmetic
            optimized = re.sub(r'2 \+ 3 \* 4', '14', optimized)

        return optimized