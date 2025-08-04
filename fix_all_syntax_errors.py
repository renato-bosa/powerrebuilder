#!/usr/bin/env python3
"""Fix all syntax errors in Python files."""

import ast
from pathlib import Path


def check_syntax(filepath: Path) -> tuple[bool, str]:
    """Check if file has syntax errors."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


def fix_duplicate_statements(content: str) -> str:
    """Fix duplicate inline statements."""
    lines = content.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check patterns for duplicate lines
        if i + 2 < len(lines):
            current_stripped = line.strip()
            next_line = lines[i + 1].strip()
            third_line = lines[i + 2].strip()

            # Pattern: statement followed by empty line and duplicate with inline code
            if (
                next_line == ""
                and third_line.startswith(current_stripped)
                and ":" in third_line[len(current_stripped) :]
            ):
                fixed_lines.append(line)
                i += 3
                continue

        # Check for immediate duplicate
        if i + 1 < len(lines):
            current_stripped = line.strip()
            next_line = lines[i + 1].strip()

            if (
                next_line.startswith(current_stripped)
                and ":" in next_line[len(current_stripped) :]
            ):
                fixed_lines.append(line)
                i += 2
                continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_indentation_after_statement(content: str) -> str:
    """Fix missing indentation after control statements."""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        fixed_lines.append(line)

        # Check if this line ends with : and next line has wrong indentation
        stripped = line.strip()
        if (
            stripped
            and stripped.endswith(":")
            and not stripped.startswith("#")
            and not stripped.startswith('"""')
            and not stripped.startswith("'''")
        ):
            # Check if next line exists and has content
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_stripped = next_line.strip()

                # If next line is not empty and not properly indented
                if next_stripped and not next_line.startswith(
                    " " * (len(line) - len(line.lstrip()) + 4)
                ):
                    # Skip - this might be a duplicate line issue
                    pass

    return "\n".join(fixed_lines)


def fix_unclosed_strings(content: str) -> str:
    """Fix unclosed triple-quoted strings."""
    # Count triple quotes
    triple_single = content.count("'''")
    triple_double = content.count('"""')

    # If odd number, add closing quotes at the end
    if triple_single % 2 == 1:
        content += "\n'''"
    if triple_double % 2 == 1:
        content += '\n"""'

    return content


def fix_unexpected_indent(content: str) -> str:
    """Fix unexpected indentation."""
    lines = content.split("\n")
    fixed_lines = []
    expected_indent = 0

    for i, line in enumerate(lines):
        if not line.strip():
            fixed_lines.append(line)
            continue

        current_indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        # Adjust expected indentation based on previous line
        if i > 0:
            prev_line = lines[i - 1].strip()
            if prev_line.endswith(":"):
                expected_indent = len(lines[i - 1]) - len(lines[i - 1].lstrip()) + 4
            elif prev_line in (
                "pass",
                "continue",
                "break",
                "return",
            ) or prev_line.startswith("return "):
                # Dedent after these statements
                expected_indent = max(0, expected_indent - 4)

        # Fix obvious indentation errors
        if current_indent > expected_indent + 8:  # Too much indent
            fixed_line = " " * expected_indent + stripped
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

        # Update expected indent for next line
        if stripped.endswith(":"):
            expected_indent = current_indent + 4
        elif not stripped.endswith(":") and current_indent < expected_indent:
            expected_indent = current_indent

    return "\n".join(fixed_lines)


def process_file(filepath: Path) -> bool:
    """Process a file to fix syntax errors."""
    try:
        # Check if file has syntax errors
        has_syntax_error, error_msg = check_syntax(filepath)
        if has_syntax_error:
            return False

        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        original = content

        # Apply fixes
        content = fix_duplicate_statements(content)
        content = fix_unclosed_strings(content)
        content = fix_indentation_after_statement(content)
        content = fix_unexpected_indent(content)

        # Only write if changed
        if content != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            # Verify fix worked
            has_syntax_error, _ = check_syntax(filepath)
            if not has_syntax_error:
                return True
            # Revert if we made it worse
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(original)

        return False

    except Exception:
        return False


def main() -> None:
    """Fix syntax errors in all Python files."""
    src_dir = Path("src")

    # First, get all files with syntax errors
    files_with_errors = []

    for py_file in src_dir.rglob("*.py"):
        has_error, error_msg = check_syntax(py_file)
        if not has_error:
            files_with_errors.append((py_file, error_msg))

    # Try to fix them
    fixed_count = 0

    for filepath, _ in files_with_errors:
        if process_file(filepath):
            fixed_count += 1

    # Report remaining errors
    remaining_errors = []
    for filepath, _ in files_with_errors:
        has_error, error_msg = check_syntax(filepath)
        if not has_error:
            remaining_errors.append((filepath, error_msg))

    if remaining_errors:
        for filepath, error_msg in remaining_errors:
            pass


if __name__ == "__main__":
    main()
