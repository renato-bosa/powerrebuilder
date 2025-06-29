#!/usr/bin/env python3
"""Script to update file paths from old structure to new data/ structure."""

import re
from pathlib import Path

# Define path replacements
PATH_REPLACEMENTS = {
    'data/input/pbd_files': 'data/input/pbd_files',
    'data/test_data/fixtures': 'data/test_data/fixtures',
    'data/output/current/extracted': 'data/output/current/extracted',
    'data/output/current/decompiled': 'data/output/current/decompiled',
    'data/output/current/model': 'data/output/current/model',
    'data/output/current/parsed': 'data/output/current/parsed',
    'data/output/current/logs': 'data/output/current/logs',
}

def update_file(file_path: Path) -> bool:
    """Update paths in a single file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply replacements
        for old_path, new_path in PATH_REPLACEMENTS.items():
            # Match the path in various contexts
            patterns = [
                f'"{old_path}"',
                f"'{old_path}'",
                f'{old_path}/',
                f'Path("{old_path}")',
                f"Path('{old_path}')",
            ]
            
            replacements = [
                f'"{new_path}"',
                f"'{new_path}'",
                f'{new_path}/',
                f'Path("{new_path}")',
                f"Path('{new_path}')",
            ]
            
            for pattern, replacement in zip(patterns, replacements):
                content = content.replace(pattern, replacement)
        
        # Write back if changed
        if content != original_content:
            file_path.write_text(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Update all Python files with old paths."""
    root = Path(".")
    updated_files = []
    
    # Find all Python files
    for py_file in root.rglob("*.py"):
        if "data/" in str(py_file):
            continue  # Skip files already in data directory
            
        if update_file(py_file):
            updated_files.append(py_file)
    
    # Report results
    if updated_files:
        print(f"Updated {len(updated_files)} files:")
        for f in updated_files:
            print(f"  - {f}")
    else:
        print("No files needed updating.")
    
    print("\nRemember to:")
    print("1. Update any configuration files (JSON, YAML, etc.)")
    print("2. Update documentation")
    print("3. Test the changes")

if __name__ == "__main__":
    main()