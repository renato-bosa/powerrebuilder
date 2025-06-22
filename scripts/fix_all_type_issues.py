#!/usr/bin/env python3
"""Fix all remaining type annotation issues from Union conversion."""

import re
import sys
from pathlib import Path


def fix_all_type_issues(content: str) -> tuple[str, bool]:








    """Fix all type annotation issues.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content

    # Fix return type annotations with comma instead of pipe
    # e.g., "-> Type1 | Type2: " should be "-> Type1, Type2: "
    content = re.sub(
        r"->\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*(\w+)\s*:",
        r"-> \1 | \2:",
        content,
    )

    # Fix type annotations in variable declarations
    # e.g., "var: Type1, Type2 = " should be "var: Type1, Type2 = "
    content = re.sub(
        r":\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*(\w+)\s*=",
        r": \1 | \2 =",
        content,
    )

    # Fix type annotations followed by docstring
    # e.g., '-> Type1 | Type2: """docstring' should be '-> Type1, Type2: \n    """docstring'
    content = re.sub(
        r'->\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*(\w+)\s*:\s*"""',
        r'-> \1 | \2:\n    """',
        content,
    )

    # Fix function parameter annotations where comma is missing
    # e.g., "param: Type1, param2: Type2" should be "param: Type1, param2: Type2"
    content = re.sub(
        r"(\w+):\s*([^,=\n()]+?)\s*\|\s+(\w+):\s*([^,=\n()]+)",
        r"\1: \2, \3: \4",
        content,
    )

    # Fix edge case where there's a newline after the comma in return type
    # e.g., "-> Type1,\n    Type2: " should be "-> Type1, Type2: "
    content = re.sub(
        r"->\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*\n\s*(\w+)\s*:",
        r"-> \1 | \2:",
        content,
    )

    return content, content != original


def process_file(file_path: Path) -> bool:








    """Process a single Python file.

    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        updated_content, was_changed = fix_all_type_issues(content)

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
