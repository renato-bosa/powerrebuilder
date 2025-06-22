#!/usr/bin/env python3
"""Fix additional syntax errors in Python files."""

import re
import sys
from pathlib import Path


def fix_docstring_indentation(content: str) -> tuple[str, bool]:

    """Fix docstring indentation issues.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    lines = content.split("\n")
    fixed_lines = []
    in_class_or_func = False
    expected_indent = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if we're starting a function or method
        if re.match(r"^(\s*)(def|class)\s+\w+.*:\s*$", line):
            match = re.match(r"^(\s*)(def|class)\s+\w+.*:\s*$", line)
            expected_indent = len(match.group(1)) + 4
            in_class_or_func = True
            fixed_lines.append(line)
            i += 1
            continue

        # If we're in a function/class and hit a docstring
        if in_class_or_func and (stripped.startswith('"""') or stripped.startswith("'''")):
            # Make sure it has correct indentation
            if len(line) - len(line.lstrip()) != expected_indent:
                fixed_lines.append(" " * expected_indent + stripped)
            else:
                fixed_lines.append(line)
            in_class_or_func = False
            i += 1
            continue

        fixed_lines.append(line)
        i += 1

    result = "\n".join(fixed_lines)
    return result, result != content


def fix_inline_assignments(content: str) -> tuple[str, bool]:

    """Fix inline assignments after if/while/for statements.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Fix patterns like "if result: var1, var2 = result"
        match = re.match(r"^(\s*)(if|while|for)\s+([^:]+):\s*(\w+)\s*,\s*(\w+)\s*=\s*(.+)$", line)
        if match:
            indent, keyword, condition, var1, var2, rhs = match.groups()
            fixed_lines.append(f"{indent}{keyword} {condition}:")
            fixed_lines.append(f"{indent}    {var1}, {var2} = {rhs}")
            continue

        # Fix patterns like "while block_stack: block_type, start_line = block_stack.pop()"
        match = re.match(r"^(\s*)(while|if)\s+(\w+):\s*(\w+)\s*,\s*(\w+)\s*=\s*(.+)$", line)
        if match:
            indent, keyword, condition, var1, var2, rhs = match.groups()
            fixed_lines.append(f"{indent}{keyword} {condition}:")
            fixed_lines.append(f"{indent}    {var1}, {var2} = {rhs}")
            continue

        # Fix patterns in for loops: "for pattern, replacement in list: var, count = ..."
        match = re.match(r"^(\s*)(for)\s+(\w+)\s*,\s*(\w+)\s+in\s+([^:]+):\s*(.+)$", line)
        if match:
            indent, keyword, var1, var2, iterator, statement = match.groups()
            fixed_lines.append(f"{indent}{keyword} {var1}, {var2} in {iterator}:")
            fixed_lines.append(f"{indent}    {statement}")
            continue

        fixed_lines.append(line)

    result = "\n".join(fixed_lines)
    return result, result != content


def fix_try_except_blocks(content: str) -> tuple[str, bool]:

    """Fix try/except block syntax issues.

    Returns:
        Tuple of (updated_content, was_changed)
    """
    # Fix try blocks that have incorrect structure
    lines = content.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for patterns where except/finally appear without proper try structure
        if re.match(r"^(\s*)except\s+\w+.*:$", line) or re.match(r"^(\s*)finally\s*:$", line):
            # Check if previous non-empty line has a try
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1

            if j >= 0 and "try:" not in lines[j]:
                # This except/finally is orphaned, comment it out
                fixed_lines.append(f"# {line}  # FIXME: Orphaned except/finally")
                i += 1
                continue

        fixed_lines.append(line)
        i += 1

    result = "\n".join(fixed_lines)
    return result, result != content


def fix_method_definitions(content: str) -> tuple[str, bool]:

    """Fix method definition syntax issues.

    Returns:
        Tuple of (updated_content, was_changed)  
    """
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Fix method definitions that are missing colons
        if re.match(r"^(\s*)def\s+\w+\([^)]*\)\s*->\s*[^:]+$", line):
            fixed_lines.append(line + ":")
            continue

        # Fix async method definitions
        if re.match(r"^(\s*)async\s+def\s+\w+\([^)]*\)\s*->\s*[^:]+$", line):
            fixed_lines.append(line + ":")
            continue

        fixed_lines.append(line)

    result = "\n".join(fixed_lines)
    return result, result != content


def process_file(file_path: Path) -> bool:

    """Process a single Python file.

    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content

        # Apply all fixes
        content, _ = fix_docstring_indentation(content)
        content, _ = fix_inline_assignments(content) 
        content, _ = fix_try_except_blocks(content)
        content, _ = fix_method_definitions(content)

        if content != original:
            file_path.write_text(content, encoding="utf-8")
            print(f"✓ Fixed: {file_path.relative_to(Path.cwd())}")
            return True
        else:
            return False
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov"}

    for py_file in root.rglob("*.py"):
        # Skip excluded directories
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)

    print(f"Found {len(python_files)} Python files to check")

    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            updated_count += 1

    print(f"\nCompleted! Fixed {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
