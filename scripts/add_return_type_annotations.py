#!/usr/bin/env python3
"""Add return type annotations based on method patterns and return statements."""

import ast
import re
import sys
from pathlib import Path


class ReturnTypeInferrer(ast.NodeVisitor):
    """Infer return types from method bodies."""

    def __init__(self):
        self.returns = []
        self.has_yield = False

    def visit_Return(self, node: ast.Return) -> None:
        """Visit return statement."""
        if node.value is None:
            self.returns.append("None")
        else:
            # Try to infer type from return value
            return_type = self._infer_type(node.value)
            if return_type:
                self.returns.append(return_type)
        self.generic_visit(node)

    def visit_Yield(self, node: ast.Yield) -> None:
        """Visit yield statement."""
        self.has_yield = True
        self.generic_visit(node)

    def _infer_type(self, node: ast.AST) -> str | None:
        """Infer type from AST node."""
        if isinstance(node, ast.Constant):
            value = node.value
            if value is None:
                return "None"
            elif isinstance(value, bool):
                return "bool"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "float"
            elif isinstance(value, str):
                return "str"
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Name):
            # Common variable names that hint at type
            if node.id in ["True", "False"]:
                return "bool"
            elif node.id == "None":
                return "None"
        elif isinstance(node, ast.Call):
            # Check common constructors/functions
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in ["list", "dict", "set", "tuple", "str", "int", "float", "bool"]:
                    return func_name
                elif func_name == "len":
                    return "int"
                elif func_name in ["Path"]:
                    return "Path"
        elif isinstance(node, ast.Attribute):
            # self.something suggests object return
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                return "Any"  # Conservative
        elif isinstance(node, ast.BoolOp):
            return "bool"
        elif isinstance(node, ast.Compare):
            return "bool"
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return "bool"

        return None

    def get_return_type(self) -> str | None:
        """Get inferred return type."""
        if self.has_yield:
            # Generator
            if self.returns:
                # Try to find common type
                unique_types = set(self.returns) - {"None"}
                if len(unique_types) == 1:
                    return f"Generator[{list(unique_types)[0]}, None, None]"
            return "Generator"

        if not self.returns:
            return None

        # Remove None and check remaining types
        non_none_returns = [r for r in self.returns if r != "None"]

        if not non_none_returns:
            return "None"

        # Check if all returns are the same type
        unique_types = set(non_none_returns)
        if len(unique_types) == 1:
            return_type = list(unique_types)[0]
            # Check if some returns are None
            if "None" in self.returns:
                return f"{return_type} | None"
            return return_type

        # Multiple return types - be conservative
        return None


def add_return_types(content: str) -> tuple[str, bool]:

    """Add return type annotations where they can be inferred."""
    try:
        tree = ast.parse(content)
    except:
        return content, False

    lines = content.split("\n")
    modified = False

    # Track functions to update
    updates = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip if already has return annotation
            if node.returns is not None:
                continue

            # Skip __init__ as we already handled those
            if node.name == "__init__":
                continue

            # Try to infer return type
            inferrer = ReturnTypeInferrer()
            for stmt in node.body:
                inferrer.visit(stmt)

            return_type = inferrer.get_return_type()

            # Also check method name patterns
            if not return_type:
                return_type = infer_from_method_name(node.name)

            if return_type:
                # Find the line with the function definition
                func_line = node.lineno - 1  # ast uses 1-based indexing
                if func_line < len(lines):
                    line = lines[func_line]
                    # Check if it's a simple one-line def
                    if line.strip().endswith(":"):
                        # Add return type before the colon
                        new_line = line.rstrip(":") + f" -> {return_type}:"
                        updates.append((func_line, new_line))

    # Apply updates
    for line_num, new_line in updates:
        lines[line_num] = new_line
        modified = True

    return "\n".join(lines), modified


def infer_from_method_name(method_name: str) -> str | None:

    """Infer return type from method name patterns."""
    method_lower = method_name.lower()

    # Boolean methods
    if any(method_lower.startswith(prefix) for prefix in ["is_", "has_", "can_", "should_", "will_", "was_", "are_"]):
        return "bool"
    if any(method_lower.endswith(suffix) for suffix in ["_exists", "_valid", "_enabled", "_visible"]):
        return "bool"

    # String methods
    if any(pattern in method_lower for pattern in ["to_string", "get_name", "get_text", "format_"]):
        return "str"
    if method_lower.endswith("_str") or method_lower.endswith("_string"):
        return "str"

    # Number methods
    if any(pattern in method_lower for pattern in ["count_", "get_size", "get_length", "calculate_"]):
        return "int"
    if method_lower.endswith("_count") or method_lower.endswith("_size"):
        return "int"

    # Collection methods
    if any(method_lower.startswith(prefix) for prefix in ["get_all_", "find_all_", "list_"]):
        return "list"
    if method_lower.endswith("_list") or method_lower.endswith("s"):  # plural often indicates list
        return "list"

    # Path methods
    if "path" in method_lower or "file" in method_lower or "dir" in method_lower:
        if any(verb in method_lower for verb in ["get_", "find_", "resolve_"]):
            return "Path"

    # Dict methods
    if any(pattern in method_lower for pattern in ["to_dict", "as_dict", "get_properties"]):
        return "dict"

    return None


def process_file(file_path: Path) -> bool:

    """Process a single Python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        updated_content, was_changed = add_return_types(content)

        if was_changed:
            file_path.write_text(updated_content, encoding="utf-8")
            print(f"✓ Updated: {file_path.relative_to(Path.cwd())}")
            return True
        else:
            return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov", "tests"}

    for py_file in root.rglob("*.py"):
        # Skip excluded directories and test files
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        if "test_" in py_file.name or "_test.py" in py_file.name:
            continue
        python_files.append(py_file)

    print(f"Found {len(python_files)} Python files to check")

    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            updated_count += 1

    print(f"\nCompleted! Updated {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
