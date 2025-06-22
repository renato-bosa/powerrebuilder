#!/usr/bin/env python3
"""Fix remaining indentation errors in specific files."""

import ast
import re
from pathlib import Path


def fix_indentation_patterns(content: str) -> str:
    """Fix common indentation patterns in the content."""
    lines = content.split("\n")
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for mismatched try/except blocks
        if re.match(r"^(\s*)try:", line):
            indent_level = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1

            # Find all except blocks and ensure they match the try indentation
            while i < len(lines):
                next_line = lines[i]

                # Check for except blocks
                if re.match(r"^(\s*)except\s+", next_line):
                    except_indent = len(next_line) - len(next_line.lstrip())

                    # If except is not aligned with try, fix it
                    if except_indent != indent_level:
                        code_part = next_line.lstrip()
                        fixed_line = " " * indent_level + code_part
                        fixed_lines.append(fixed_line)
                    else:
                        fixed_lines.append(next_line)
                elif re.match(r"^(\s*)(else:|finally:)", next_line):
                    # Handle else/finally clauses
                    clause_indent = len(next_line) - len(next_line.lstrip())
                    if clause_indent != indent_level:
                        code_part = next_line.lstrip()
                        fixed_line = " " * indent_level + code_part
                        fixed_lines.append(fixed_line)
                    else:
                        fixed_lines.append(next_line)
                elif next_line.strip() == "" or next_line.startswith(" " * (indent_level + 4)):
                    # Empty line or properly indented content inside try/except
                    fixed_lines.append(next_line)
                else:
                    # End of try/except block
                    break
                i += 1
            continue

        # Fix overly indented logger statements
        if re.match(r"^(\s{20,})(logger\.(debug|info|warning|error|exception))", line):
            # Reduce to reasonable indentation
            code_part = line.lstrip()
            # Use 12 spaces (3 levels of indentation)
            fixed_line = "            " + code_part
            fixed_lines.append(fixed_line)
            i += 1
            continue

        # Fix other excessive indentation
        if len(line) - len(line.lstrip()) > 32 and line.strip():
            # Reduce excessive indentation
            code_part = line.lstrip()
            # Determine reasonable indentation level (max 16 spaces)
            new_indent = min(16, (len(line) - len(line.lstrip())) // 2)
            fixed_line = " " * new_indent + code_part
            fixed_lines.append(fixed_line)
            i += 1
            continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_file(file_path: Path) -> bool:
    """Fix indentation in a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Apply fixes
        fixed_content = fix_indentation_patterns(content)

        # Test if the fix works
        if fixed_content != original_content:
            try:
                ast.parse(fixed_content)
                file_path.write_text(fixed_content, encoding="utf-8")
                return True
            except SyntaxError:
                # Fix didn't work, try a simpler approach
                return try_simple_fixes(file_path, content)

        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def try_simple_fixes(file_path: Path, content: str) -> bool:
    """Try simpler fixes for stubborn files."""
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Skip FIXME comments that were left from previous fixes
        if "# FIXME:" in line:
            continue

        # For any line with excessive indentation, just normalize it
        if len(line) - len(line.lstrip()) > 20:
            code_part = line.lstrip()
            # Use moderate indentation
            fixed_line = "        " + code_part  # 8 spaces
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    fixed_content = "\n".join(fixed_lines)

    try:
        ast.parse(fixed_content)
        file_path.write_text(fixed_content, encoding="utf-8")
        return True
    except SyntaxError:
        return False


def main():
    """Fix remaining files with syntax errors."""
    root = Path(__file__).parent.parent

    # Problem files identified earlier
    problem_files = [
        "parse/sql_parser.py",
        "common/pipeline_coordinator.py",
        "common/pipeline.py",
        "common/progress.py",
        "benchmarks/benchmark_end_to_end.py",
        "model/ui.py",
        "generate/generate_coordinator.py",
        "generate/template_validator.py",
        "extract/pbd/structures/header.py",
        "extract/pbd/structures/data_block.py",
        "extract/pbd/io/scanner.py",
        "extract/pbd/io/file_operations.py",
        "extract/pbd/utils/binary_utils.py",
        "extract/pbd/extraction/library.py",
        "generate/converters/datawindow_enhancements.py",
        "generate/converters/datawindow_converter.py",
        "model/optimization/sql_optimizer.py",
        "model/utils/type_checker.py",
        "decompile/core/post_processor.py",
    ]

    fixed_count = 0
    for file_rel_path in problem_files:
        file_path = root / file_rel_path
        if file_path.exists():
            try:
                # Test current syntax
                with open(file_path, "r", encoding="utf-8") as f:
                    ast.parse(f.read())
                print(f"✓ {file_rel_path} - already valid")
            except SyntaxError as e:
                print(f"Fixing {file_rel_path}: {e}")
                if fix_file(file_path):
                    print(f"✓ Fixed: {file_rel_path}")
                    fixed_count += 1
                else:
                    print(f"✗ Could not fix: {file_rel_path}")

    print(f"\nFixed {fixed_count} files")
    return fixed_count


if __name__ == "__main__":
    main()
