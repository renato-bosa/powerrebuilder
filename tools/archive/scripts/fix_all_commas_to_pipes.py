#!/usr/bin/env python3
"""Fix all comma-separated type unions to use pipe syntax."""

import re
import sys
from pathlib import Path


def fix_comma_to_pipe(content: str) -> tuple[str, bool]:





    """Fix comma-separated type unions to use pipe syntax.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content

    # Fix patterns like "name: Type1, Type2 = value" to "name: Type1 | Type2 = value"
    # This pattern needs to be more careful to avoid breaking function parameters
    lines = content.split("\n")
    updated_lines = []

    for line in lines:
        # Skip function definitions and parameter lists
        if "def " in line or line.strip().startswith("(") or line.strip().startswith(")"):
            updated_lines.append(line)
            continue

        # Look for type annotations with commas that should be pipes
        # Pattern: variable: Type1, Type2 = value
        match = re.match(r"^(\s*)(\w+):\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*(\w+(?:\[[\w\[\], |]+\])?)\s*=\s*(.*)$", line)
        if match:
            indent, var_name, type1, type2, value = match.groups()
            # Convert to pipe syntax
            updated_line = f"{indent}{var_name}: {type1} | {type2} = {value}"
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    content = "\n".join(updated_lines)

    # Also fix simpler patterns with re.sub for safety
    # Fix: "variable: Type, None" (at end of line) to "variable: Type | None"
    content = re.sub(
        r"^(\s*)(\w+):\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*None\s*$",
        r"\1\2: \3 | None",
        content,
        flags=re.MULTILINE,
    )

    return content, content != original


def process_file(file_path: Path) -> bool:





    """Process a single Python file.

    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        updated_content, was_changed = fix_comma_to_pipe(content)

        if was_changed:
            file_path.write_text(updated_content, encoding="utf-8")
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
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs"}
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
