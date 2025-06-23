#!/usr/bin/env python3
"""Script to fix G004/G201 logging format issues by converting f-strings to % formatting."""

import re
import sys
from pathlib import Path


def fix_logging_fstring(line: str) -> str:








    """Convert f-string logging to % formatting."""
    # Pattern to match logger.method(f"...") calls
    logging_pattern = r'((?:logger|logging|self\.logger|log)\.\w+\()(f"[^"]*"|\bf\'[^\']*\')'

    def replace_fstring(match) -> str:


        prefix = match.group(1)
        fstring = match.group(2)

        # Remove the f prefix
        string_content = fstring[2:-1]  # Remove f" and "

        # Find all {expr} patterns
        expr_pattern = r"\{([^}]+)\}"
        expressions = []

        def collect_expr(m) -> str:


            expressions.append(m.group(1))
            return "%s"

        # Replace {expr} with %s and collect expressions
        new_string = re.sub(expr_pattern, collect_expr, string_content)

        if expressions:
            # Build the new logging call
            return f'{prefix}"{new_string}", {", ".join(expressions)}'
        else:
            return f'{prefix}"{new_string}"'

    return re.sub(logging_pattern, replace_fstring, line)


def process_file(file_path: Path) -> tuple[int, list[str]]:








    """Process a single file and return number of changes and new content."""
    changes = 0
    new_lines = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, []

    for line in lines:
        new_line = fix_logging_fstring(line)
        if new_line != line:
            changes += 1
        new_lines.append(new_line)

    return changes, new_lines


def main() -> None:







    """Main function to process files."""
    if len(sys.argv) < 2:
        print("Usage: python fix_logging_format.py <file_or_directory>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.rglob("*.py"))
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)

    total_changes = 0
    files_changed = 0

    for file_path in files:
        changes, new_content = process_file(file_path)

        if changes > 0:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_content)
                print(f"Fixed {changes} issues in {file_path}")
                total_changes += changes
                files_changed += 1
            except Exception as e:
                print(f"Error writing {file_path}: {e}")

    print(f"\nTotal: Fixed {total_changes} issues in {files_changed} files")


if __name__ == "__main__":
    main()
