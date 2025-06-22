#!/usr/bin/env python3
"""Fix remaining type annotation issues."""

import re
import sys
from pathlib import Path


def fix_remaining_type_issues(content: str) -> tuple[str, bool]:
    
    


    """Fix remaining type annotation issues.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content
    
    # Fix patterns like "Type1 | Type2, Type3" in return types
    # These should be "Type1 | Type2 | Type3"
    content = re.sub(
        r'(->.*?)(\w+\s*\|\s*\w+)\s*,\s*(\w+)\s*:',
        r'\1\2 | \3:',
        content
    )
    
    # Fix patterns where assignment with | was incorrectly used
    # e.g., "a, b = func()" should be "a, b = func()"
    content = re.sub(
        r'(\w+)\s*\|\s*(\w+)\s*=\s*',
        r'\1, \2 = ',
        content
    )
    
    # Fix tuple in return type: "tuple[str | None, int]" to "tuple[str | None, int]"  
    content = re.sub(
        r'tuple\[([^,\]]+)\s*\|\s*(\w+)\]',
        r'tuple[\1, \2]',
        content
    )
    
    return content, content != original


def process_file(file_path: Path) -> bool:
    
    


    """Process a single Python file.
    
    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        updated_content, was_changed = fix_remaining_type_issues(content)
        
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