#!/usr/bin/env python3
"""Fix field annotation patterns in dataclasses."""

import re
import sys
from pathlib import Path


def fix_field_annotations(content: str) -> tuple[str, bool]:
    
    


    """Fix field annotation patterns.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content
    
    # Fix field patterns: "fieldname: Type | None = field(...)" to "fieldname: Type | None = field(...)"
    content = re.sub(
        r'(\w+):\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*None\s*=\s*field\(',
        r'\1: \2 | None = field(',
        content
    )
    
    # Fix simple field patterns: "fieldname: Type | None = None" to "fieldname: Type | None = None"
    content = re.sub(
        r'(\w+):\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*None\s*=\s*None',
        r'\1: \2 | None = None',
        content
    )
    
    # Fix patterns without assignment: "fieldname: Type, None" to "fieldname: Type | None"
    content = re.sub(
        r'(\w+):\s*(\w+(?:\[[\w\[\], |]+\])?)\s*,\s*None\s*$',
        r'\1: \2 | None',
        content,
        flags=re.MULTILINE
    )
    
    return content, content != original


def process_file(file_path: Path) -> bool:
    
    


    """Process a single Python file.
    
    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        updated_content, was_changed = fix_field_annotations(content)
        
        if was_changed:
            file_path.write_text(updated_content, encoding='utf-8')
            print(f"✓ Fixed: {file_path}")
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
    python_files = list(root.rglob("*.py"))
    
    # Exclude virtual environment and other directories
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.eggs'}
    python_files = [
        f for f in python_files 
        if not any(part in exclude_dirs for part in f.parts)
    ]
    
    print(f"Found {len(python_files)} Python files to check")
    
    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            updated_count += 1
    
    print(f"\nCompleted! Fixed {updated_count} files.")
    
    return 0 if updated_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())