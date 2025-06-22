#!/usr/bin/env python3
"""Fix syntax errors in Python files."""

import re
import sys
from pathlib import Path


def fix_syntax_errors(content: str) -> tuple[str, bool]:
    
    


    """Fix various syntax errors in Python code.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content
    
    # Fix parameter syntax errors like "param: Type | None = None"
    # This should be "param: Type | None = None"
    content = re.sub(
        r'(\w+):\s*([^,=\n]+),\s*None\s*=\s*None',
        r'\1: \2 | None = None',
        content
    )
    
    # Fix assignment syntax errors like "var, val = result" that should be unpacking
    # Don't fix actual type annotations
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Check for patterns like "if result: var, val = result"
        # This got incorrectly changed to "if result: var | val = result"
        match = re.match(r'^(\s*)(if\s+[^:]+:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$', line)
        if match:
            indent, condition, var1, var2, rhs = match.groups()
            fixed_line = f"{indent}{condition}{var1}, {var2} = {rhs}"
            fixed_lines.append(fixed_line)
        # Check for patterns like "try: var | val = func()"
        elif re.match(r'^(\s*)(try:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$', line):
            match = re.match(r'^(\s*)(try:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$', line)
            indent, try_part, var1, var2, rhs = match.groups()
            fixed_line = f"{indent}{try_part}{var1}, {var2} = {rhs}"
            fixed_lines.append(fixed_line)
        # Check for "while condition: var | val = func()" 
        elif re.match(r'^(\s*)(while\s+[^:]+:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$', line):
            match = re.match(r'^(\s*)(while\s+[^:]+:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$', line)
            indent, while_part, var1, var2, rhs = match.groups()
            fixed_line = f"{indent}{while_part}{var1}, {var2} = {rhs}"
            fixed_lines.append(fixed_line)
        # Check for patterns like "for ... in ...: var, val = item"
        elif re.match(r'^(\s*)(for\s+.+:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$', line):
            match = re.match(r'^(\s*)(for\s+.+:\s*)(\w+)\s*\|\s*(\w+)\s*=\s*(.*)$', line)
            indent, for_part, var1, var2, rhs = match.groups()
            fixed_line = f"{indent}{for_part}{var1}, {var2} = {rhs}"
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Fix inline function definitions without proper newlines
    # Pattern: "def func(...): statement" on one line (except for simple returns/pass)
    def fix_inline_defs(match) -> list:
        
        full_match = match.group(0)
        def_part = match.group(1)
        statement = match.group(2)
        
        # Allow simple returns and pass statements
        if statement.strip() in ['pass', 'return', 'return None'] or statement.strip().startswith('return '):
            return full_match
        
        # For complex statements, add proper newline and indent
        return f"{def_part}\n    {statement}"
    
    content = re.sub(
        r'^(def\s+\w+\s*\([^)]*\)\s*->\s*[^:]+:\s*)(.+)$',
        fix_inline_defs,
        content,
        flags=re.MULTILINE
    )
    
    # Fix sorted() with wrong pipe syntax
    # "sorted(..., key=lambda x: x[1] , reverse=True)" should be ", reverse=True)"
    content = re.sub(
        r'sorted\(([^)]+)\s*\|\s*reverse\s*=\s*True\)',
        r'sorted(\1, reverse=True)',
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
        updated_content, was_changed = fix_syntax_errors(content)
        
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