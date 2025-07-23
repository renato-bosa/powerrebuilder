#!/usr/bin/env python3
"""Fix indentation errors in Python files."""

import ast
import re
from pathlib import Path
from typing import List, Tuple

def check_syntax(filepath: Path) -> Tuple[bool, str, int]:
    """Check if file has syntax errors, return (is_valid, error_msg, line_number)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, "", 0
    except SyntaxError as e:
        return False, str(e.msg), e.lineno or 0

def fix_file_indentation(filepath: Path) -> bool:
    """Fix indentation errors in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return False
            
        fixed_lines = []
        i = 0
        class_or_def_level = 0
        current_indent = 0
        in_class = False
        in_function = False
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                fixed_lines.append(line)
                i += 1
                continue
            
            # Handle class definitions
            if re.match(r'^class\s+\w+', stripped):
                in_class = True
                class_or_def_level = current_indent
                fixed_lines.append(' ' * current_indent + stripped + '\n')
                current_indent += 4
                i += 1
                continue
                
            # Handle function/method definitions
            if re.match(r'^def\s+\w+', stripped):
                in_function = True
                if not in_class:
                    class_or_def_level = current_indent
                fixed_lines.append(' ' * current_indent + stripped + '\n')
                current_indent += 4
                i += 1
                continue
            
            # Handle docstrings after class/function
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if i > 0 and (re.match(r'^\s*(class|def)\s+', lines[i-1].strip())):
                    # This is a docstring right after class/def
                    fixed_lines.append(' ' * current_indent + stripped + '\n')
                else:
                    # Regular docstring
                    fixed_lines.append(' ' * current_indent + stripped + '\n')
                i += 1
                continue
                
            # Handle decorators
            if stripped.startswith('@'):
                fixed_lines.append(' ' * max(0, current_indent - 4) + stripped + '\n')
                i += 1
                continue
                
            # Handle dedent keywords
            if stripped in ('pass', 'return', 'break', 'continue') or stripped.startswith('return '):
                fixed_lines.append(' ' * current_indent + stripped + '\n')
                if in_function and current_indent > class_or_def_level:
                    current_indent = class_or_def_level
                    in_function = False
                i += 1
                continue
                
            # Handle control flow keywords that increase indent
            if any(stripped.startswith(kw + ' ') or stripped.startswith(kw + ':') 
                   for kw in ('if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with')):
                fixed_lines.append(' ' * current_indent + stripped + '\n')
                if stripped.endswith(':'):
                    current_indent += 4
                i += 1
                continue
                
            # Handle lines that should dedent
            if stripped.startswith(('elif', 'else:', 'except', 'finally')):
                if current_indent >= 4:
                    current_indent -= 4
                fixed_lines.append(' ' * current_indent + stripped + '\n')
                if stripped.endswith(':'):
                    current_indent += 4
                i += 1
                continue
            
            # Default: use current indentation
            fixed_lines.append(' ' * current_indent + stripped + '\n')
            
            # If line ends with ':', increase indent for next line
            if stripped.endswith(':') and not stripped.startswith('#'):
                current_indent += 4
                
            i += 1
        
        # Write fixed content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
            
        # Check if we fixed it
        is_valid, _, _ = check_syntax(filepath)
        return is_valid
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Fix indentation errors in all Python files with syntax errors."""
    src_dir = Path('src')
    
    # Find all files with syntax errors
    files_to_fix = []
    
    print("Finding files with indentation errors...")
    for py_file in src_dir.rglob('*.py'):
        is_valid, error_msg, line_no = check_syntax(py_file)
        if not is_valid and 'indent' in error_msg:
            files_to_fix.append((py_file, error_msg, line_no))
            print(f"  {py_file}: Line {line_no} - {error_msg}")
    
    print(f"\nFound {len(files_to_fix)} files with indentation errors")
    
    # Try to fix them
    print("\nAttempting fixes...")
    fixed_count = 0
    
    for filepath, _, _ in files_to_fix:
        if fix_file_indentation(filepath):
            fixed_count += 1
            print(f"  Fixed: {filepath}")
        else:
            print(f"  Failed: {filepath}")
    
    print(f"\nFixed {fixed_count} files")
    
    # Report remaining errors
    remaining_errors = 0
    for filepath, _, _ in files_to_fix:
        is_valid, error_msg, line_no = check_syntax(filepath)
        if not is_valid:
            remaining_errors += 1
            print(f"  Still has error: {filepath} - Line {line_no}: {error_msg}")
    
    print(f"\n{remaining_errors} files still have errors")

if __name__ == "__main__":
    main()