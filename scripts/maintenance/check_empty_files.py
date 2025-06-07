#!/usr/bin/env python3
"""Check for empty or nearly empty files in the project."""

import os
from pathlib import Path


def check_empty_files(root_dir: Path):
    """Find empty or nearly empty Python files."""
    empty_files = []
    small_files = []
    
    for path in root_dir.rglob("*.py"):
        # Skip hidden directories and __pycache__
        if any(part.startswith('.') for part in path.parts) or '__pycache__' in str(path):
            continue
            
        try:
            size = path.stat().st_size
            
            if size == 0:
                empty_files.append(path)
            elif size < 50:  # Less than 50 bytes is essentially empty
                with open(path, 'r') as f:
                    content = f.read().strip()
                    # Check if it's just imports or docstring
                    if not content or content == '""""""' or content.startswith('from __future__'):
                        small_files.append((path, size, content[:50]))
        except Exception as e:
            print(f"Error checking {path}: {e}")
    
    return empty_files, small_files


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent.parent
    
    empty_files, small_files = check_empty_files(project_root)
    
    if empty_files:
        print(f"Found {len(empty_files)} empty files:")
        for f in sorted(empty_files):
            relative_path = f.relative_to(project_root)
            print(f"  - {relative_path}")
    
    if small_files:
        print(f"\nFound {len(small_files)} nearly empty files (< 50 bytes):")
        for f, size, preview in sorted(small_files):
            relative_path = f.relative_to(project_root)
            print(f"  - {relative_path} ({size} bytes): {preview!r}")
    
    if not empty_files and not small_files:
        print("No empty or nearly empty files found!")
    
    # Check specifically for empty __init__.py files
    empty_inits = [f for f in empty_files if f.name == "__init__.py"]
    if empty_inits:
        print(f"\nEmpty __init__.py files ({len(empty_inits)}):")
        for f in sorted(empty_inits):
            relative_path = f.relative_to(project_root)
            print(f"  - {relative_path}")


if __name__ == "__main__":
    main()