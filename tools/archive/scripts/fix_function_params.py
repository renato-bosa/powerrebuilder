#!/usr/bin/env python3
"""Fix function parameter typing issues from Union conversion."""

import re
import sys
from pathlib import Path


def fix_function_params(content: str) -> tuple[str, bool]:








    """Fix function parameter type annotations that were incorrectly converted.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content

    # Fix patterns where parameter names got mixed into type unions
    # e.g., "param1: Type1 | Type2, param2: Type3" -> "param1: Type1 | Type2 | param2: Type3"
    pattern = re.compile(
        r"(\w+):\s*([^,=\n]+?)\s*\|\s*(\w+):\s*([^,=\n]+)",
        re.MULTILINE,
    )

    def fix_param_match(match):


        param1 = match.group(1)
        type1 = match.group(2).strip()
        param2 = match.group(3)
        type2 = match.group(4).strip()
        return f"{param1}: {type1}, {param2}: {type2}"

    content = pattern.sub(fix_param_match, content)

    # Also fix patterns with default values
    # e.g., "param1: Type1 | Type2, param2: Type3= default"
    pattern_with_default = re.compile(
        r"(\w+):\s*([^,=\n]+?)\s*\|\s*(\w+):\s*([^,=\n]+?)\s*=\s*([^,\n]+)",
        re.MULTILINE,
    )

    def fix_param_default_match(match):


        param1 = match.group(1)
        type1 = match.group(2).strip()
        param2 = match.group(3)
        type2 = match.group(4).strip()
        default = match.group(5).strip()
        return f"{param1}: {type1}, {param2}: {type2} = {default}"

    content = pattern_with_default.sub(fix_param_default_match, content)

    return content, content != original


def process_file(file_path: Path) -> bool:








    """Process a single Python file.

    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        updated_content, was_changed = fix_function_params(content)

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
