#!/usr/bin/env python3
"""Remove whitespace from blank lines."""

import sys
from pathlib import Path


def remove_blank_line_whitespace(content: str) -> str:
    """Remove whitespace from lines that contain only whitespace."""
    lines = content.split("\n")
    cleaned_lines = []

    for line in lines:
        # If the line contains only whitespace, make it completely empty
        if line.strip() == "":
            cleaned_lines.append("")
        else:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def process_file(file_path: Path) -> bool:
    """Process a single file to remove blank line whitespace."""
    try:
        content = file_path.read_text(encoding="utf-8")
        cleaned_content = remove_blank_line_whitespace(content)

        if cleaned_content != content:
            file_path.write_text(cleaned_content, encoding="utf-8")
            return True

        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def find_files_with_blank_line_whitespace(root: Path) -> list[Path]:
    """Find files that have whitespace on blank lines."""
    files_with_issues = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov"}

    for py_file in root.rglob("*.py"):
        if any(part in exclude_dirs for part in py_file.parts):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Check if any lines have whitespace but no visible content
            has_blank_line_whitespace = any(
                line != line.strip() and line.strip() == ""
                for line in lines
            )

            if has_blank_line_whitespace:
                files_with_issues.append(py_file)

        except Exception:
            continue

    return files_with_issues


def main():
    """Remove whitespace from blank lines in all Python files."""
    root = Path(__file__).parent.parent

    # First, find files that actually have the issue
    print("Scanning for files with whitespace on blank lines...")
    files_with_issues = find_files_with_blank_line_whitespace(root)

    if not files_with_issues:
        print("✓ No files found with whitespace on blank lines")
        return 0

    print(f"Found {len(files_with_issues)} files with whitespace on blank lines")

    updated_count = 0
    for file_path in files_with_issues:
        if process_file(file_path):
            print(f"✓ Cleaned: {file_path.relative_to(root)}")
            updated_count += 1

    print(f"\n✓ Cleaned whitespace from blank lines in {updated_count} files")
    return updated_count


if __name__ == "__main__":
    main()
