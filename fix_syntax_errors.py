#!/usr/bin/env python3
"""Fix syntax errors caused by duplicate inline statements."""

from pathlib import Path


def fix_duplicate_inline_statements(content: str) -> str:
    """Fix duplicate inline statements that cause syntax errors."""
    lines = content.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if next line exists and contains the same statement pattern
        if i + 2 < len(lines):
            current_stripped = line.strip()
            next_line = lines[i + 1].strip()
            third_line = lines[i + 2].strip()

            # Pattern 1: Empty line followed by duplicate with inline code
            if (
                next_line == ""
                and third_line.startswith(current_stripped)
                and len(third_line) > len(current_stripped)
                and third_line[len(current_stripped) :].strip().startswith(":")
            ):
                # Skip the empty line and the duplicate
                fixed_lines.append(line)
                i += 3
                continue

            # Pattern 2: Direct duplicate with inline code
            if (
                next_line.startswith(current_stripped)
                and len(next_line) > len(current_stripped)
                and next_line[len(current_stripped) :].strip().startswith(":")
            ):
                # Skip the duplicate
                fixed_lines.append(line)
                i += 2
                continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def process_file(filepath: Path) -> bool:
    """Process a single file and return True if modified."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        original = content
        fixed = fix_duplicate_inline_statements(content)

        if fixed != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed)
            return True
        return False
    except Exception:
        return False


def main() -> None:
    """Fix syntax errors in all Python files."""
    src_dir = Path("src")
    modified_count = 0

    for py_file in src_dir.rglob("*.py"):
        if process_file(py_file):
            modified_count += 1


if __name__ == "__main__":
    main()
