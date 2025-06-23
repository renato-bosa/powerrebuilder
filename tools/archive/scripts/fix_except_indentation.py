#!/usr/bin/env python3
"""Fix indentation of except blocks to match their try blocks."""

import sys
from pathlib import Path


def fix_except_indentation(file_path: Path) -> bool:

    """Fix indentation of except blocks in a single file.

    Returns:
        True if file was modified, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        fixed_lines = []
        changed = False

        # Track try block indentations
        try_stack = []  # Stack of (line_num, indent_level) for try blocks

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Track try blocks
            if stripped == "try:":
                indent = len(line) - len(line.lstrip())
                try_stack.append((i, indent))
                fixed_lines.append(line)
                continue

            # Fix except blocks with wrong indentation
            if (stripped.startswith("except ") or stripped == "except:" or 
                stripped.startswith("finally:")):

                current_indent = len(line) - len(line.lstrip())

                # Find the most recent try block
                expected_indent = None
                for j in range(len(try_stack) - 1, -1, -1):
                    try_line, try_indent = try_stack[j]
                    # The except should have the same indentation as its try
                    if current_indent >= try_indent:
                        expected_indent = try_indent
                        # Remove processed try blocks from stack
                        try_stack = try_stack[:j]
                        break

                if expected_indent is not None and current_indent != expected_indent:
                    # Fix the indentation
                    fixed_lines.append(" " * expected_indent + stripped)
                    changed = True
                else:
                    fixed_lines.append(line)
            else:
                # Check if we've left a try block (unindented past it)
                if try_stack and line.strip():
                    current_indent = len(line) - len(line.lstrip())
                    # Remove try blocks we've exited
                    try_stack = [(ln, ind) for ln, ind in try_stack if ind < current_indent]

                fixed_lines.append(line)

        if changed:
            file_path.write_text("\n".join(fixed_lines), encoding="utf-8")
            print(f"✓ Fixed indentation: {file_path.relative_to(Path.cwd())}")
            return True

        return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix except block indentation."""
    root = Path(__file__).parent.parent

    # Find Python files
    print("Searching for files with indentation issues...")

    files_to_check = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov"}

    for py_file in root.rglob("*.py"):
        # Skip excluded directories
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        files_to_check.append(py_file)

    print(f"Checking {len(files_to_check)} files")

    updated_count = 0
    for file_path in files_to_check:
        if fix_except_indentation(file_path):
            updated_count += 1

    print(f"\nCompleted! Fixed {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
