#!/usr/bin/env python3
"""Fix quote consistency - use double quotes throughout."""

import ast
import re
import sys
from pathlib import Path


def fix_quotes_in_file(file_path: Path) -> bool:

    """Fix quotes in a single Python file to use double quotes consistently."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Parse the file to understand string literals vs other uses of quotes
        try:
            tree = ast.parse(content)
        except SyntaxError:
            print(f"⚠️  Syntax error in {file_path}, skipping quote fixes")
            return False

        # Get all string positions
        string_positions = []

        class StringFinder(ast.NodeVisitor):
            def visit_Constant(self, node):
                if isinstance(node.value, str) and hasattr(node, "lineno"):
                    # Record position
                    string_positions.append({
                        "line": node.lineno - 1,  # 0-based
                        "col": node.col_offset,
                        "end_col": node.end_col_offset if hasattr(node, "end_col_offset") else None,
                        "value": node.value,
                    })
                self.generic_visit(node)

        finder = StringFinder()
        finder.visit(tree)

        # Split into lines for processing
        lines = content.split("\n")

        # Process each line
        for i, line in enumerate(lines):
            # Skip lines that are comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Skip lines in docstrings (rough check)
            if '"""' in line or "'''" in line:
                continue

            # Find strings in this line
            line_strings = [s for s in string_positions if s["line"] == i]

            # Replace single quotes with double quotes for strings
            # This is a simplified approach - a full solution would need more complex parsing
            new_line = line

            # Handle f-strings
            new_line = re.sub(r"\bf'([^']*)'", r'f"\1"', new_line)
            new_line = re.sub(r'\bf"([^"]*)"', r'f"\1"', new_line)

            # Handle r-strings (raw strings)
            new_line = re.sub(r"\br'([^']*)'", r'r"\1"', new_line)
            new_line = re.sub(r'\br"([^"]*)"', r'r"\1"', new_line)

            # Handle regular strings (but avoid changing quotes inside strings)
            # This is tricky because we need to avoid changing quotes that are part of the string content

            # First, protect strings that contain the opposite quote
            protected = []

            # Find all string literals in the line
            # Match various string patterns
            string_patterns = [
                (r"'([^'\\]|\\.)*'", '"'),  # Single quotes to double
                (r'"([^"\\]|\\.)*"', '"'),  # Already double (no change)
                (r"'''(.*?)'''", '"""'),     # Triple single to triple double
                (r'"""(.*?)"""', '"""'),     # Already triple double
            ]

            # For simple single-quoted strings without embedded quotes
            # Convert 'text' to "text" if text doesn't contain "
            def replace_quotes(match):
                content = match.group(0)
                if content.startswith("'") and content.endswith("'") and '"' not in content[1:-1]:
                    # Simple case: no double quotes inside
                    return '"' + content[1:-1] + '"'
                return content

            # Apply replacements carefully
            # Skip if line contains dictionary key patterns like {'key': value}
            if not (re.search(r"{\s*'[^']+'\s*:", new_line) or re.search(r",\s*'[^']+'\s*:", new_line)):
                # Replace simple single-quoted strings
                new_line = re.sub(r"(?<![\\])('([^'\\]|\\.)*?')", replace_quotes, new_line)

            lines[i] = new_line

        # Rejoin lines
        new_content = "\n".join(lines)

        # Only write if changed
        if new_content != original_content:
            # Verify the file still parses correctly
            try:
                ast.parse(new_content)
                file_path.write_text(new_content, encoding="utf-8")
                return True
            except SyntaxError:
                print(f"✗ Quote conversion would break {file_path}, skipping")
                return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

    return False


def main():
    """Main function to fix quotes in all Python files."""
    root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov", "tests", "reference", "scripts"}

    for py_file in root.rglob("*.py"):
        # Skip excluded directories
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)

    print(f"Found {len(python_files)} Python files to check")

    updated_count = 0
    for file_path in python_files:
        if fix_quotes_in_file(file_path):
            print(f"✓ Updated: {file_path.relative_to(root)}")
            updated_count += 1

    print(f"\nCompleted! Updated {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
