#!/usr/bin/env python3
"""Fix improperly converted Union types with more than 2 elements."""

import re
import sys
from pathlib import Path


def fix_union_conversions(content: str) -> tuple[str, bool]:








    """Fix Union conversions that weren't properly handled.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content

    # Fix patterns like "Type1 | Type2 | Type3" -> "Type1 | Type2 | Type3"
    # This handles the case where Union[A, B, C] was converted to A | B | C
    pattern = re.compile(r"(\w+)\s*\|\s*(\w+)\s*,\s*(\w+)")

    def fix_match(match):


        return f"{match.group(1)} | {match.group(2)} | {match.group(3)}"

    content = pattern.sub(fix_match, content)

    # Also handle patterns with more elements
    # e.g., "Type1 | Type2 | Type3 | Type4" -> "Type1 | Type2 | Type3 | Type4"
    max_iterations = 10
    for _ in range(max_iterations):
        new_content = re.sub(
            r"((?:\w+\s*\|\s*)+\w+)\s*,\s*(\w+)",
            r"\1 | \2",
            content,
        )
        if new_content == content:
            break
        content = new_content

    return content, content != original


def process_file(file_path: Path) -> bool:








    """Process a single Python file.

    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        updated_content, was_changed = fix_union_conversions(content)

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
