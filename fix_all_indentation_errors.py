#!/usr/bin/env python3
"""Fix all indentation errors in Python files."""

import os


def fix_indentation_after_colon(content):
    """Fix indentation errors after if/for/while/def/class statements."""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        fixed_lines.append(line)

        # Check if this line ends with : and has control flow keywords
        if line.strip() and line.strip().endswith(":"):
            # Look ahead to see if next line needs indenting
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                current_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip())

                # If next line has same or less indentation and is not empty, it needs fixing
                if next_line.strip() and next_indent <= current_indent:
                    # Check if it's a control flow statement
                    if any(
                        line.strip().startswith(kw)
                        for kw in [
                            "if ",
                            "elif ",
                            "else:",
                            "for ",
                            "while ",
                            "def ",
                            "class ",
                            "try:",
                            "except",
                            "finally:",
                            "with ",
                        ]
                    ):
                        # Fix the indentation of the next line
                        lines[i + 1] = " " * (current_indent + 4) + next_line.lstrip()

    return "\n".join(fixed_lines)


def main() -> None:
    """Fix indentation in all files with errors."""
    files_to_fix = [
        "src/model/types/base.py",
        "src/model/coordinator.py",
        "src/model/factory.py",
    ]

    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            continue

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            fixed_content = fix_indentation_after_colon(content)

            if fixed_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
            else:
                pass

        except Exception:
            pass


if __name__ == "__main__":
    main()
