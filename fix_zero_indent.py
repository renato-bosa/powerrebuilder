#!/usr/bin/env python3
"""Fix lines that have zero indentation when they should be indented.
This handles the specific case where lines after if/for/while/etc have no indentation.
"""

import re
import shutil
import sys
from pathlib import Path


def fix_zero_indent(file_path: Path) -> bool:
    """Fix lines with zero indentation that should be indented."""
    # Backup the file
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")
    shutil.copy2(file_path, backup_path)

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    fixed_lines = []
    changes_made = 0
    expected_indent_stack = [0]  # Stack to track expected indentation levels

    for _i, line in enumerate(lines):
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())

        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            continue

        # Skip comments
        if stripped.startswith("#"):
            fixed_lines.append(line)
            continue

        # Check if current line has zero indentation but should be indented
        if current_indent == 0 and expected_indent_stack[-1] > 0:
            # Check if this is a valid top-level statement
            if not re.match(r"^(class|def|import|from|@|if __name__|#)", stripped):
                # This line should be indented
                fixed_line = " " * expected_indent_stack[-1] + stripped + "\n"
                fixed_lines.append(fixed_line)
                changes_made += 1

                # Update current_indent for subsequent logic
                current_indent = expected_indent_stack[-1]
            else:
                # This is a valid top-level statement, reset indent stack
                expected_indent_stack = [0]
                fixed_lines.append(line)
        else:
            # Line has some indentation or is correctly at zero
            fixed_lines.append(line)

            # Adjust expected indent stack based on actual indentation
            while (
                len(expected_indent_stack) > 1
                and current_indent < expected_indent_stack[-1]
            ):
                expected_indent_stack.pop()

        # Check if this line starts a new block
        if stripped.endswith(":") and not stripped.startswith("#"):
            # This line starts a block, next lines should be indented
            if re.match(
                r"^(if|elif|else|for|while|with|try|except|finally|def|class|async def)",
                stripped,
            ):
                # Calculate expected indentation for the block
                if current_indent == 0 and re.match(
                    r"^(class|def|async def)", stripped
                ):
                    # Top-level class/function
                    expected_indent_stack.append(4)
                else:
                    # Nested block
                    expected_indent_stack.append(current_indent + 4)

    # Write the fixed content
    if changes_made > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        # Verify syntax
        try:
            with open(file_path, encoding="utf-8") as f:
                compile(f.read(), str(file_path), "exec")
            backup_path.unlink()  # Remove backup on success
            return True
        except SyntaxError:
            # Restore from backup
            shutil.copy2(backup_path, file_path)
            return False
    else:
        backup_path.unlink()
        return True


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        sys.exit(1)

    success = fix_zero_indent(file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
