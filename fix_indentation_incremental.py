#!/usr/bin/env python3
"""Incrementally fix indentation issues by applying fixes one at a time
and checking syntax after each fix.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def check_syntax(file_path: Path) -> tuple[bool, str]:
    """Check if file has valid syntax."""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(file_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, ""
    return False, result.stderr


def fix_indentation_incremental(file_path: Path) -> bool:
    """Fix indentation issues incrementally."""
    # Backup the file
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")
    shutil.copy2(file_path, backup_path)

    total_fixes = 0
    max_iterations = 20  # Prevent infinite loops

    for _iteration in range(max_iterations):
        # Read current content
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Find and fix one issue at a time
        fix_applied = False

        for i in range(len(lines) - 1):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Check if this line ends with : (block starter)
            if stripped.endswith(":") and not stripped.startswith("#"):
                current_indent = len(line) - len(line.lstrip())

                # Look at the next non-empty line
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.strip()

                    if not next_stripped or next_stripped.startswith("#"):
                        j += 1
                        continue

                    next_indent = len(next_line) - len(next_line.lstrip())

                    # Check if next line needs indenting
                    if next_indent <= current_indent:
                        # Skip if it's another block starter
                        if next_stripped.endswith(":"):
                            break

                        # Apply fix
                        fixed_line = " " * (current_indent + 4) + next_stripped + "\n"
                        lines[j] = fixed_line

                        # Write the fix
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.writelines(lines)

                        total_fixes += 1
                        fix_applied = True
                        break
                    # Line already indented correctly
                    break

                if fix_applied:
                    break

        if not fix_applied:
            break

        # Check syntax after each fix
        valid, error = check_syntax(file_path)
        if not valid and "expected an indented block" not in error:
            break

    # Final syntax check
    valid, error = check_syntax(file_path)
    if valid:
        backup_path.unlink()
        return True

    # Keep partial fixes by default in non-interactive mode

    return False


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        sys.exit(1)

    success = fix_indentation_incremental(file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
