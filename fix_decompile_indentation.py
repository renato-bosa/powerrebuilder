#!/usr/bin/env python3
"""Fix common indentation issues in decompile module files."""

import re
import sys
from pathlib import Path


def fix_file_indentation(filepath: Path) -> bool:
    """Fix common indentation issues in a Python file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    lines = content.split('\n')
    fixed_lines = []
    in_function = False
    in_class = False
    function_indent = 0
    class_indent = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track context
        if stripped.startswith('class '):
            in_class = True
            class_indent = len(line) - len(line.lstrip())
            in_function = False
            fixed_lines.append(line)
            continue
            
        if re.match(r'^def\s+', stripped):
            in_function = True
            function_indent = len(line) - len(line.lstrip())
            # Ensure proper indentation for methods in classes
            if in_class and function_indent < class_indent + 4:
                line = ' ' * (class_indent + 4) + stripped
            fixed_lines.append(line)
            continue
        
        # Fix excessive indentation (more than 40 spaces is almost always wrong)
        if line and len(line) - len(line.lstrip()) > 40:
            # Determine proper indentation based on context
            if in_function:
                # Code inside a function should be indented 4 spaces from the function
                new_indent = function_indent + 4
            elif in_class:
                # Code inside a class but not in a function
                new_indent = class_indent + 4
            else:
                # Top-level code
                new_indent = 0
            
            # Special handling for certain patterns
            if stripped.startswith(('"""', "'''")):
                # Docstrings
                line = ' ' * new_indent + stripped
            elif stripped.startswith(('#', '//')):
                # Comments
                line = ' ' * new_indent + stripped
            else:
                # Regular code
                line = ' ' * new_indent + stripped
        
        # Fix misaligned if/elif/else
        if stripped.startswith(('if ', 'elif ', 'else:', 'else ')):
            # These should align with each other
            if i > 0 and fixed_lines[i-1].strip():
                prev_indent = len(fixed_lines[i-1]) - len(fixed_lines[i-1].lstrip())
                current_indent = len(line) - len(line.lstrip())
                
                # If severely misaligned, fix it
                if abs(current_indent - prev_indent) > 20:
                    if in_function:
                        line = ' ' * (function_indent + 4) + stripped
                    elif in_class:
                        line = ' ' * (class_indent + 4) + stripped
        
        # Fix misaligned except clauses
        if stripped.startswith('except'):
            # Find the matching try
            for j in range(i-1, max(0, i-20), -1):
                if fixed_lines[j].strip().startswith('try:'):
                    try_indent = len(fixed_lines[j]) - len(fixed_lines[j].lstrip())
                    line = ' ' * try_indent + stripped
                    break
        
        fixed_lines.append(line)
    
    # Write back the fixed content
    fixed_content = '\n'.join(fixed_lines)
    
    try:
        with open(filepath, 'w') as f:
            f.write(fixed_content)
        print(f"Fixed indentation in {filepath}")
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False


def main():
    """Fix indentation in problematic decompile files."""
    files_to_fix = [
        'src/decompile/pcode/detector.py',
        'src/decompile/reconstruction/expression.py',
    ]
    
    for file_path in files_to_fix:
        path = Path(file_path)
        if path.exists():
            print(f"\nProcessing {file_path}...")
            if fix_file_indentation(path):
                # Try to compile to check if we fixed it
                import py_compile
                try:
                    py_compile.compile(str(path), doraise=True)
                    print(f"✓ {file_path} now compiles successfully!")
                except py_compile.PyCompileError as e:
                    print(f"✗ {file_path} still has syntax errors: {e}")
        else:
            print(f"File not found: {file_path}")


if __name__ == "__main__":
    main()