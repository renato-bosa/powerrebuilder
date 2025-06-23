#!/usr/bin/env python3
"""Remove unused imports from all Python files in the project."""

import subprocess
import sys
from pathlib import Path


def remove_unused_imports() -> None:




    """Remove unused imports from all Python files."""
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

    # First, let's check if autoflake is installed
    try:
        subprocess.run(["autoflake", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("autoflake not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "autoflake"], check=True)

    # Run autoflake on each file
    updated_count = 0
    for py_file in python_files:
        # Run autoflake to check if file needs changes
        result = subprocess.run(
            ["autoflake", "--remove-all-unused-imports", "--check", str(py_file)],
            capture_output=True,
        )

        # If autoflake returns non-zero, the file has unused imports
        if result.returncode != 0:
            # Apply the fix
            subprocess.run(
                ["autoflake", "--remove-all-unused-imports", "--in-place", str(py_file)],
                capture_output=True,
            )
            print(f"✓ Fixed: {py_file.relative_to(root)}")
            updated_count += 1

    print(f"\nCompleted! Fixed {updated_count} files.")
    return updated_count


if __name__ == "__main__":
    updated = remove_unused_imports()
    sys.exit(0 if updated > 0 else 1)
