#!/usr/bin/env python3
"""Fix indentation errors in Python files."""

import subprocess
import sys
from pathlib import Path


def check_syntax(file_path):
    """Check if a Python file has syntax errors."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(file_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)


def fix_file_with_autopep8(file_path):
    """Try to fix a file using autopep8."""
    try:
        # First check if autopep8 is available
        subprocess.run(["autopep8", "--version"], capture_output=True, check=True)

        # Run autopep8 with aggressive fixing
        result = subprocess.run(
            ["autopep8", "--in-place", "--aggressive", "--aggressive", str(file_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False


def find_python_files_with_errors():
    """Find all Python files with syntax errors."""
    error_files = []

    # Priority directories based on the report
    priority_paths = [
        "src/extract/factory.py",
        "src/decompile/pcode/decoder.py",
        "src/decompile/core/formatter.py",
        "src/parse/preprocessor/preprocessor.py",
        "src/model/services/ast_processor.py",
        "src/decompile/visualization/",
        "src/model/analysis/security.py",
    ]

    # Check priority files first
    for path_str in priority_paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".py":
            success, error = check_syntax(path)
            if not success:
                error_files.append((path, error))
        elif path.is_dir():
            # Check all Python files in directory
            for py_file in path.rglob("*.py"):
                success, error = check_syntax(py_file)
                if not success:
                    error_files.append((py_file, error))

    # Also check all other Python files in src/
    src_path = Path("src")
    if src_path.exists():
        for py_file in src_path.rglob("*.py"):
            if not any(str(py_file) == str(ef[0]) for ef in error_files):
                success, error = check_syntax(py_file)
                if not success:
                    error_files.append((py_file, error))

    return error_files


def main() -> None:
    """Main function."""
    error_files = find_python_files_with_errors()

    if not error_files:
        return

    for file_path, error in error_files[:10]:  # Show first 10
        if "IndentationError" in error:
            pass
        elif "SyntaxError" in error:
            # Extract line number if available
            if "line" in error:
                pass

    if len(error_files) > 10:
        pass

    # Try to fix with autopep8
    fixed_count = 0

    for file_path, _ in error_files:
        if fix_file_with_autopep8(file_path):
            # Check if it's actually fixed
            success, _ = check_syntax(file_path)
            if success:
                fixed_count += 1
            else:
                pass
        else:
            pass

    # Re-check for remaining errors
    remaining_errors = []
    for file_path, _ in error_files:
        success, error = check_syntax(file_path)
        if not success:
            remaining_errors.append((file_path, error))

    if remaining_errors:
        for file_path, error in remaining_errors[:5]:
            # Show specific error
            lines = error.strip().split("\n")
            for line in lines:
                if "line" in line:
                    break


if __name__ == "__main__":
    main()
