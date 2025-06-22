#!/usr/bin/env python3
"""Add trailing commas for better git diffs."""

import ast
import sys
from pathlib import Path


def add_trailing_commas(source_code: str) -> str:
    """Add trailing commas to multiline collections."""
    try:
        # Parse the source code
        tree = ast.parse(source_code)
    except SyntaxError:
        # Skip files with syntax errors
        return source_code

    lines = source_code.split("\n")

    # Find multiline collections and add trailing commas
    class CommaVisitor(ast.NodeVisitor):
        def __init__(self):
            self.modifications = []

        def visit_List(self, node):
            self._check_multiline_collection(node, node.elts, "[", "]")
            self.generic_visit(node)

        def visit_Tuple(self, node):
            # Only add trailing commas to non-empty tuples
            if node.elts:
                self._check_multiline_collection(node, node.elts, "(", ")")
            self.generic_visit(node)

        def visit_Dict(self, node):
            # For dictionaries, check both keys and values
            if node.keys:
                items = []
                for i, (key, value) in enumerate(zip(node.keys, node.values)):
                    items.extend([key, value])
                self._check_multiline_collection(node, items, "{", "}")
            self.generic_visit(node)

        def visit_Set(self, node):
            self._check_multiline_collection(node, node.elts, "{", "}")
            self.generic_visit(node)

        def visit_Call(self, node):
            # Add trailing commas to function calls with multiple arguments
            all_args = node.args + node.keywords
            if len(all_args) > 1:
                self._check_multiline_collection(node, all_args, "(", ")")
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            # Add trailing commas to function parameters
            if len(node.args.args) > 1:
                self._check_multiline_function_def(node)
            self.generic_visit(node)

        def _check_multiline_collection(self, node, elements, open_char, close_char):
            """Check if a collection spans multiple lines and needs a trailing comma."""
            if not elements or not hasattr(node, "lineno"):
                return

            # Check if the collection spans multiple lines
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)

            if end_line > start_line:
                # Find the last element
                last_element = elements[-1]
                if hasattr(last_element, "end_lineno") and hasattr(last_element, "end_col_offset"):
                    last_line = last_element.end_lineno - 1  # Convert to 0-based
                    last_col = last_element.end_col_offset

                    if last_line < len(lines):
                        line = lines[last_line]
                        # Check if there's already a trailing comma
                        remaining = line[last_col:].strip()
                        if not remaining.startswith(","):
                            # Look for the closing bracket
                            close_line = last_line
                            found_close = False

                            # Search for closing bracket in current and subsequent lines
                            for check_line in range(last_line, min(len(lines), last_line + 3)):
                                if close_line < len(lines) and close_char in lines[check_line]:
                                    found_close = True
                                    break

                            if found_close:
                                # Add trailing comma
                                self.modifications.append((last_line, last_col, ","))

        def _check_multiline_function_def(self, node):
            """Check function definitions for trailing commas in parameters."""
            if not hasattr(node, "end_lineno") or node.end_lineno == node.lineno:
                return

            # This is more complex - for now skip function definitions
            # as they require more careful parsing
            pass

    visitor = CommaVisitor()
    visitor.visit(tree)

    # Apply modifications in reverse order to maintain line positions
    visitor.modifications.sort(reverse=True, key=lambda x: (x[0], x[1]))

    modified_lines = lines[:]
    for line_idx, col_idx, comma in visitor.modifications:
        if line_idx < len(modified_lines):
            line = modified_lines[line_idx]
            # Insert comma at the specified position
            new_line = line[:col_idx] + comma + line[col_idx:]
            modified_lines[line_idx] = new_line

    return "\n".join(modified_lines)


def process_file(file_path: Path) -> bool:
    """Process a single Python file to add trailing commas."""
    try:
        content = file_path.read_text(encoding="utf-8")

        # Skip if file has syntax errors
        try:
            ast.parse(content)
        except SyntaxError:
            return False

        updated_content = add_trailing_commas(content)

        if updated_content != content:
            # Verify the updated content is still valid
            try:
                ast.parse(updated_content)
                file_path.write_text(updated_content, encoding="utf-8")
                return True
            except SyntaxError:
                # Don't write if we broke the syntax
                return False

        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Add trailing commas to all Python files."""
    root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov", "tests", "reference", "scripts"}

    for py_file in root.rglob("*.py"):
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)

    print(f"Processing {len(python_files)} Python files...")

    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            print(f"✓ Added trailing commas: {file_path.relative_to(root)}")
            updated_count += 1

    print(f"\n✓ Added trailing commas to {updated_count} files")
    return updated_count


if __name__ == "__main__":
    main()
