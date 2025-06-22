#!/usr/bin/env python3
"""Remove unused imports from all Python files using ruff."""

import subprocess
import sys
from pathlib import Path


def remove_unused_imports() -> None:
    


    """Remove unused imports from all Python files using ruff."""
    root = Path(__file__).parent.parent
    
    # Find all Python files
    python_files = []
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.eggs', 'htmlcov'}
    
    for py_file in root.rglob("*.py"):
        # Skip excluded directories
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)
    
    print(f"Found {len(python_files)} Python files to check")
    
    # Use ruff to fix unused imports (F401)
    # F401: imported but unused
    print("\nRunning ruff to remove unused imports...")
    
    # First, let's see how many files have unused imports
    result = subprocess.run(
        ["ruff", "check", "--select", "F401", "--quiet", str(root)],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(f"Found unused imports in multiple files")
        
    # Now fix them
    fix_result = subprocess.run(
        ["ruff", "check", "--select", "F401", "--fix", "--unsafe-fixes", str(root)],
        capture_output=True,
        text=True
    )
    
    if fix_result.returncode == 0:
        print("Successfully removed unused imports")
    else:
        print(f"Some issues remain:\n{fix_result.stdout}")
    
    # Count how many files were modified
    # Run ruff again to see if any F401 errors remain
    after_result = subprocess.run(
        ["ruff", "check", "--select", "F401", "--quiet", str(root)],
        capture_output=True,
        text=True
    )
    
    # Compare before and after to estimate changes
    before_count = len(result.stdout.strip().split('\n')) if result.stdout else 0
    after_count = len(after_result.stdout.strip().split('\n')) if after_result.stdout else 0
    fixed_count = before_count - after_count
    
    print(f"\nFixed approximately {fixed_count} import issues")
    print(f"Remaining issues: {after_count}")
    
    return fixed_count


if __name__ == "__main__":
    updated = remove_unused_imports()
    sys.exit(0 if updated > 0 else 1)