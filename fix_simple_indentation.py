#!/usr/bin/env python3
"""Simple indentation fixer that focuses on the most common issue:
Lines after colons that aren't indented.
"""

import re
import shutil
import sys
from pathlib import Path


def fix_simple_indentation(file_path: Path) -> bool:
    """Fix simple indentation issues where lines after colons aren't indented."""
    # Backup the file
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")
    shutil.copy2(file_path, backup_path)

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    fixed_lines = []
    changes_made = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this line ends with a colon (indicates a block start)
        if stripped and stripped.endswith(":") and not stripped.startswith("#"):
            # Add the line with colon
            fixed_lines.append(line)
            i += 1

            # Calculate expected indentation for the block
            current_indent = len(line) - len(line.lstrip())
            expected_indent = current_indent + 4

            # Process subsequent lines that should be in this block
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()

                # Skip empty lines
                if not next_stripped:
                    fixed_lines.append(next_line)
                    i += 1
                    continue

                # Skip comments at the same level
                if next_stripped.startswith("#"):
                    fixed_lines.append(next_line)
                    i += 1
                    continue

                next_indent = len(next_line) - len(next_line.lstrip())

                # Check if this line should be indented
                if next_indent <= current_indent:
                    # Check if this is a new block (ends with :) at same or lower level
                    if next_stripped.endswith(":") and not next_stripped.startswith(
                        "#"
                    ):
                        # This is a new block at same/lower level, stop fixing
                        break

                    # Check for keywords that indicate end of block
                    if re.match(
                        r"^(class|def|if|elif|else|try|except|finally|with|for|while)\s",
                        next_stripped,
                    ):
                        # This starts a new construct at same/lower level
                        break

                    # This line needs to be indented
                    fixed_line = " " * expected_indent + next_stripped
                    fixed_lines.append(fixed_line)
                    changes_made += 1
                    i += 1
                else:
                    # Line is already indented, block continues normally
                    fixed_lines.append(next_line)
                    i += 1

                    # If this line is indented more than expected, use it as the new expected
                    expected_indent = max(expected_indent, next_indent)
        else:
            # Not a block starter, just add the line
            fixed_lines.append(line)
            i += 1

    # Write the fixed content
    if changes_made > 0:
        fixed_content = "\n".join(fixed_lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        # Verify syntax
        try:
            compile(fixed_content, str(file_path), "exec")
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

    success = fix_simple_indentation(file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
