#!/usr/bin/env python3
"""Update old typing imports to modern Python 3.10+ syntax."""

import re
import sys
from pathlib import Path


def update_typing_imports(content: str) -> tuple[str, bool]:



    
    


    """Update typing imports to modern syntax.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content
    
    # First update the import statement
    # Pattern to find typing imports that include Union, Dict, List, etc.
    import_pattern = re.compile(
        r'from typing import ([^]+)(?:;|$)', 
        re.MULTILINE
    )
    
    def update_imports(match) -> None:
        
    
        imports = match.group(1)
        # Remove the old-style type imports
        new_imports = []
        for imp in imports.split(','):
            imp = imp.strip()
            if imp not in ['Dict', 'List', 'Set', 'Tuple', 'Union', 'Optional', 'FrozenSet', 'Deque']:
                new_imports.append(imp)
        
        if new_imports:
            return f"from typing import {', '.join(new_imports)}"
        else:
            # If no imports left, return empty string (will be cleaned up later)
            return ""
    
    content = import_pattern.sub(update_imports, content)
    
    # Clean up empty typing imports
    content = re.sub(r'from typing import\s*\n', '', content)
    
    # Update type annotations
    # X | Y -> X | Y
    content = re.sub(r'Union\[([^, \]]+), \s*([^\]]+)\]', r'\1 | \2', content)
    
    # X | None -> X | None  
    content = re.sub(r'Optional\[([^\]]+)\]', r'\1 | None', content)
    
    # dict[X, Y] -> dict[X, Y]
    content = re.sub(r'\bDict\[', 'dict[', content)
    
    # list[X] -> list[X]
    content = re.sub(r'\bList\[', 'list[', content)
    
    # set[X] -> set[X]
    content = re.sub(r'\bSet\[', 'set[', content)
    
    # tuple[X, Y] -> tuple[X, Y]
    content = re.sub(r'\bTuple\[', 'tuple[', content)
    
    # frozenset[X] -> frozenset[X]
    content = re.sub(r'\bFrozenSet\[', 'frozenset[', content)
    
    # deque[X] -> deque[X] (from collections)
    content = re.sub(r'\bDeque\[', 'deque[', content)
    
    # Handle nested Union types recursively
    max_iterations = 10
    for _ in range(max_iterations):
        new_content = re.sub(r'Union\[([^, \]]+), \s*([^\]]+)\]', r'\1 | \2', content)
        if new_content == content:
            break
        content = new_content
    
    # Also need to add collections imports if we converted Deque
    if 'deque[' in content and 'from collections' not in content:
        # Find the right place to add the import (after __future__ imports)
        lines = content.split('\n')
        import_added = False
        for i, line in enumerate(lines):
            if line.startswith('from __future__'):
                continue
            elif line.startswith('import') or line.startswith('from'):
                # Add before first non-__future__ import
                lines.insert(i, 'from collections import deque')
                import_added = True
                break
        if not import_added and lines:
            # Add after module docstring if present
            for i, line in enumerate(lines):
                if i > 0 and (line.startswith('import') or line.startswith('from') or not line.strip()):
                    lines.insert(i, 'from collections import deque')
                    break
        content = '\n'.join(lines)
    
    return content, content != original


def process_file(file_path: Path) -> bool:



    
    


    """Process a single Python file.
    
    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        updated_content, was_changed = update_typing_imports(content)
        
        if was_changed:
            file_path.write_text(updated_content, encoding='utf-8')
            print(f"✓ Updated: {file_path}")
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
    
    print(f"\nCompleted! Updated {updated_count} files.")
    
    return 0 if updated_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())