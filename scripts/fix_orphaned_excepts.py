#!/usr/bin/env python3
"""Fix orphaned except blocks marked with FIXME comments."""

import re
import sys
from pathlib import Path


def fix_orphaned_excepts(file_path: Path) -> bool:

    """Fix orphaned except blocks in a single file.

    Returns:
        True if file was modified, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        fixed_lines = []
        changed = False

        for i, line in enumerate(lines):
            # Check if this line has the FIXME comment
            if "# FIXME: Orphaned except/finally" in line:
                # Extract the except statement
                # Look for patterns like "#                 except exceptions as e:  # FIXME: Orphaned except/finally"
                match = re.match(r"^#(\s*)(except\s+[^:]+:|except:|finally:)", line)
                if match:
                    indent = match.group(1)
                    statement = match.group(2)

                    # Replace the commented line with uncommented version
                    fixed_lines.append(indent + statement)
                    changed = True
                else:
                    # If we can't parse it, keep the original line
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        if changed:
            file_path.write_text("\n".join(fixed_lines), encoding="utf-8")
            print(f"✓ Fixed: {file_path.relative_to(Path.cwd())}")
            return True

        return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix orphaned except blocks."""
    root = Path(__file__).parent.parent

    # Find files with the FIXME pattern
    print("Searching for files with orphaned except blocks...")

    files_to_fix = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov"}

    for py_file in root.rglob("*.py"):
        # Skip excluded directories
        if any(part in exclude_dirs for part in py_file.parts):
            continue

        # Check if file contains the pattern
        try:
            content = py_file.read_text(encoding="utf-8")
            if "# FIXME: Orphaned except/finally" in content:
                files_to_fix.append(py_file)
        except Exception:
            continue

    print(f"Found {len(files_to_fix)} files to fix")

    updated_count = 0
    for file_path in files_to_fix:
        if fix_orphaned_excepts(file_path):
            updated_count += 1

    print(f"\nCompleted! Fixed {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
