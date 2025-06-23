#!/usr/bin/env python3
"""Fix remaining syntax errors in Python files."""

import re
import sys
from pathlib import Path


def fix_remaining_syntax_errors(content: str) -> tuple[str, bool]:

    """Fix remaining syntax errors.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content

    # Fix sorted() with pipe syntax issue
    # Pattern: "sorted(..., key=lambda x: x[1], reverse=True)" -> ", reverse=True)"
    content = re.sub(
        r"sorted\(([^)]+)\)\s*\|\s*reverse\s*=\s*True",
        r"sorted(\1, reverse=True)",
        content,
    )

    # Also fix variations with space before =
    content = re.sub(
        r"sorted\(([^)]+)\)\s*\|\s*reverse\s*=\s*True",
        r"sorted(\1, reverse=True)",
        content,
    )

    # Fix inline def patterns where FIXED_PART_LEN= appears 
    # Pattern: "def func() -> Type: FIXED_PART_LEN= 24"
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Handle def with inline assignment like FIXED_PART_LEN
        if re.match(r"^def\s+\w+\([^)]*\)\s*->\s*[^:]+:\s*\w+\s*=\s*\d+", line):
            # Split into two lines
            match = re.match(r"^(def\s+\w+\([^)]*\)\s*->\s*[^:]+:)\s*(\w+\s*=\s*\d+.*)$", line)
            if match:
                fixed_lines.append(match.group(1))
                fixed_lines.append("    " + match.group(2))
                continue

        # Fix patterns where a while loop has tuple unpacking with pipe
        # "while condition: var | val = expr" -> "while condition: var, val = expr"
        if re.match(r"^(\s*)(while\s+[^:]+:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$", line):
            match = re.match(r"^(\s*)(while\s+[^:]+:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$", line)
            indent, while_part, var1, var2, rhs = match.groups()
            fixed_lines.append(f"{indent}{while_part}{var1}, {var2} = {rhs}")
            continue

        # Fix if statements with incorrect pipe unpacking 
        # "if result: var | val = result" -> "if result: var, val = result"
        if "if" in line and "|" in line and "=" in line and ":" in line:
            # More specific pattern to avoid false positives
            match = re.match(r"^(\s*)(if\s+[^:]+:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*([^|].*)$", line)
            if match:
                indent, if_part, var1, var2, rhs = match.groups()
                fixed_lines.append(f"{indent}{if_part}{var1}, {var2} = {rhs}")
                continue

        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # Fix sorted with incorrect pipe in key parameter
    # Pattern: sorted(..., key=lambda x: x[1], reverse=True)
    content = re.sub(
        r"key=lambda\s+(\w+):\s*(\w+)\[(\d+)\]\s*\|\s*reverse\s*=\s*True",
        r"key=lambda \1: \2[\3], reverse=True",
        content,
    )

    # Fix try blocks with statements on the same line (more specific)
    # Pattern: "try: var, val = func()" needs to be split
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Handle try: with assignment on same line
        if line.strip().startswith("try:") and len(line.strip()) > 4 and not line.strip()[4:].strip().startswith("#"):
            indent = len(line) - len(line.lstrip())
            try_part = line[:line.index("try:") + 4]
            statement = line[line.index("try:") + 4:].strip()
            fixed_lines.append(try_part)
            fixed_lines.append(" " * (indent + 4) + statement)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines), "\n".join(fixed_lines) != original


def process_file(file_path: Path) -> bool:

    """Process a single Python file.

    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        updated_content, was_changed = fix_remaining_syntax_errors(content)

        if was_changed:
            file_path.write_text(updated_content, encoding="utf-8")
            print(f"✓ Fixed: {file_path.relative_to(Path.cwd())}")
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
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov"}

    for py_file in root.rglob("*.py"):
        # Skip excluded directories
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)

    print(f"Found {len(python_files)} Python files to check")

    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            updated_count += 1

    print(f"\nCompleted! Fixed {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
