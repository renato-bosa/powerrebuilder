#!/usr/bin/env python3
"""Fix try statement syntax errors."""

import re
import sys
from pathlib import Path


def fix_try_syntax(content: str) -> tuple[str, bool]:
    


    """Fix try statement syntax errors.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content
    
    # Fix patterns like "try: statement" on one line
    # This should be:
    # try:
    #     statement
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Check for try: with a statement on the same line
        match = re.match(r'^(\s*)(try:\s*)(.+)$', line)
        if match and not match.group(3).strip().startswith('#'):
            indent = match.group(1)
            try_part = match.group(2).rstrip()
            statement = match.group(3)
            # Split into two lines with proper indentation
            fixed_lines.append(f"{indent}{try_part}")
            fixed_lines.append(f"{indent}    {statement}")
        # Check for "if condition: var, val = something" that was incorrectly changed to pipe
        elif re.match(r'^(\s*)(if\s+[^:]+:\s*)(\w+),\s*(\w+)\s*=\s*(.*)$', line):
            # This is correct, keep as is
            fixed_lines.append(line)
        # Check for "for ... in ...: var, val = something"  
        elif re.match(r'^(\s*)(for\s+.+in.+:\s*)(\w+),\s*(\w+)\s*=\s*(.*)$', line):
            # This is correct, keep as is
            fixed_lines.append(line)
        # Check for "while condition: var, val = something"
        elif re.match(r'^(\s*)(while\s+[^:]+:\s*)(\w+),\s*(\w+)\s*=\s*(.*)$', line):
            # This is correct, keep as is
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Fix inline function definitions that need proper formatting
    # Pattern: def func(): statement (where statement is not pass/return)
    def fix_inline_func(match):
        
        indent = match.group(1) or ""
        func_def = match.group(2)
        statement = match.group(3)
        
        # Some inline definitions are intentional (like FIXED_PART_LEN= 24)
        if '=' in func_def and not '->' in func_def:
            # This is likely a variable assignment after function def
            return f"{indent}{func_def} {statement}"
        
        # Allow simple statements
        if statement.strip() in ['pass', '...', 'return', 'return None']:
            return match.group(0)
        
        # Split complex statements
        return f"{indent}{func_def}\n{indent}    {statement}"
    
    content = re.sub(
        r'^(\s*)(def\s+\w+\s*\([^)]*\)(?:\s*->\s*[^:]+)?:\s*)(.+)$',
        fix_inline_func,
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
        updated_content, was_changed = fix_try_syntax(content)
        
        if was_changed:
            file_path.write_text(updated_content, encoding='utf-8')
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
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.eggs', 'htmlcov'}
    
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