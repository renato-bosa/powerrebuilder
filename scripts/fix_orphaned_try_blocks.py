#!/usr/bin/env python3
"""Fix orphaned try/except blocks in Python files."""

import sys
from pathlib import Path


def fix_orphaned_try_blocks(content: str) -> tuple[str, bool]:

    """Fix orphaned try/except blocks.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    lines = content.split("\n")
    fixed_lines = []
    changed = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for commented out except blocks with FIXME
        if "# FIXME: Orphaned except/finally" in line and line.strip().startswith("#"):
            # Find the previous try block by looking backwards
            j = i - 1
            while j >= 0:
                if lines[j].strip().startswith("try:"):
                    # Found the try block, uncomment the except
                    uncommented = line.replace("#", "", 1).strip()
                    # Ensure proper indentation - match the try block
                    try_indent = len(lines[j]) - len(lines[j].lstrip())
                    fixed_lines.append(" " * try_indent + uncommented)
                    changed = True
                    i += 1
                    break
                j -= 1
            else:
                # No try block found, keep commented
                fixed_lines.append(line)
                i += 1
        else:
            fixed_lines.append(line)
            i += 1

    return "\n".join(fixed_lines), changed


def add_missing_try_blocks(content: str) -> tuple[str, bool]:

    """Add missing try blocks where needed.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    lines = content.split("\n")
    fixed_lines = []
    changed = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if we have code that should be in a try block
        # Look for patterns that typically need try blocks
        if i > 0 and not lines[i-1].strip().startswith("try:"):
            # Check if next line has except without preceding try
            if i + 1 < len(lines) and (lines[i+1].strip().startswith("except ") or 
                                       lines[i+1].strip() == "except:"):
                # Add try block
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(" " * indent + "try:")
                fixed_lines.append(" " * (indent + 4) + line.strip())
                changed = True
                i += 1
                continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines), changed


def process_file(file_path: Path) -> bool:

    """Process a single Python file.

    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content

        # Apply fixes
        content, changed1 = fix_orphaned_try_blocks(content)
        content, changed2 = add_missing_try_blocks(content)

        if changed1 or changed2:
            file_path.write_text(content, encoding="utf-8")
            print(f"✓ Fixed: {file_path.relative_to(Path.cwd())}")
            return True
        else:
            return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process Python files with orphaned try blocks."""
    root = Path(__file__).parent.parent

    # Only process files that were modified and have the FIXME comment
    files_to_check = []

    # Specific files that were modified
    specific_files = [
        "scripts/fix_remaining_syntax_errors.py",
        "scripts/fix_final_type_issues.py", 
        "scripts/fix_more_syntax_errors.py",
        "generate/template_schemas.py",
        "decompile/decompile_coordinator.py",
        "model/utils/type_checker.py",
    ]

    for file_path in specific_files:
        full_path = root / file_path
        if full_path.exists():
            files_to_check.append(full_path)

    print(f"Checking {len(files_to_check)} files for orphaned try blocks")

    updated_count = 0
    for file_path in files_to_check:
        if process_file(file_path):
            updated_count += 1

    print(f"\nCompleted! Fixed {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
