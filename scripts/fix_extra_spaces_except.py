#!/usr/bin/env python3
"""Fix extra spaces before except statements."""

import re
import sys
from pathlib import Path


def fix_extra_spaces_except(file_path: Path) -> bool:

    """Fix extra spaces before except statements in a single file.

    Returns:
        True if file was modified, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        fixed_lines = []
        changed = False

        for i, line in enumerate(lines):
            # Check if line has except with extra leading space
            if re.match(r"^\s+except\s", line):
                # Count the current indentation
                current_indent = len(line) - len(line.lstrip())

                # Look for the corresponding try block
                expected_indent = None
                for j in range(i - 1, -1, -1):
                    if lines[j].strip().startswith("try:"):
                        try_indent = len(lines[j]) - len(lines[j].lstrip())
                        expected_indent = try_indent
                        break
                    # Also check for another except at the right level
                    elif lines[j].strip().startswith("except ") or lines[j].strip() == "except:":
                        prev_except_indent = len(lines[j]) - len(lines[j].lstrip())
                        # If this except has proper indentation, use it
                        if prev_except_indent % 4 == 0:  # Assuming 4-space indentation
                            expected_indent = prev_except_indent
                            break

                if expected_indent is not None and current_indent > expected_indent and (current_indent - expected_indent) == 1:
                    # Remove the extra space
                    fixed_line = line[1:]  # Remove one leading space
                    fixed_lines.append(fixed_line)
                    changed = True
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        if changed:
            file_path.write_text("\n".join(fixed_lines), encoding="utf-8")
            print(f"✓ Fixed extra spaces: {file_path.relative_to(Path.cwd())}")
            return True

        return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix extra spaces before except."""
    root = Path(__file__).parent.parent

    # Find Python files
    print("Searching for files with extra spaces before except...")

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
        if fix_extra_spaces_except(file_path):
            updated_count += 1

    print(f"\nCompleted! Fixed {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
