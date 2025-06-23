#!/usr/bin/env python3
"""Fix docstrings that ended up on the same line as function definitions."""

import re
import sys
from pathlib import Path


def fix_docstring_indent(content: str) -> tuple[str, bool]:








    """Fix docstrings on same line as function definition.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content

    # Fix patterns where docstring is on same line as function definition
    # e.g., 'def func() -> Type:
    # """docstring"""' 
    # should be 'def func() -> Type:\n    """docstring"""'
    pattern = re.compile(
        r'(\s*def\s+\w+\([^)]*\)\s*->\s*[^:]+):\s*"""',
        re.MULTILINE
    )

    def fix_docstring(match):


        # Get the function definition part
        func_def = match.group(1)
        # Calculate indentation for docstring (4 spaces more than function)
        indent_match = re.match(r'^(\s*)', func_def)
        base_indent = indent_match.group(1) if indent_match else ''
        docstring_indent = base_indent + '    '
        return f'{func_def}:\n{docstring_indent}"""'

    content = pattern.sub(fix_docstring, content)

    # Also fix method definitions without return type
    pattern_no_return = re.compile(
        r'(\s*def\s+\w+\([^)]*\)):\s*"""',
        re.MULTILINE
    )

    def fix_docstring_no_return(match):


        func_def = match.group(1)
        indent_match = re.match(r'^(\s*)', func_def)
        base_indent = indent_match.group(1) if indent_match else ''
        docstring_indent = base_indent + '    '
        return f'{func_def}:\n{docstring_indent}"""'

    content = pattern_no_return.sub(fix_docstring_no_return, content)

    return content, content != original


def process_file(file_path: Path) -> bool:








    """Process a single Python file.

    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        updated_content, was_changed = fix_docstring_indent(content)

        if was_changed:
            file_path.write_text(updated_content, encoding='utf-8')
            print(f"✓ Fixed: {file_path}")
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
    python_files = list(root.rglob("*.py"))

    # Exclude virtual environment and other directories
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.eggs'}
    python_files = [
        f for f in python_files 
        if not any(part in exclude_dirs for part in f.parts)
    ]

    print(f"Found {len(python_files)} Python files to check")

    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            updated_count += 1

    print(f"\nCompleted! Fixed {updated_count} files.")

    return 0 if updated_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())