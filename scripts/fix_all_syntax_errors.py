#!/usr/bin/env python3
"""Comprehensive script to fix all syntax errors in Python files."""

import re
import sys
from pathlib import Path


def fix_orphaned_except_blocks(content: str) -> tuple[str, bool]:
    """Fix orphaned except blocks marked with FIXME comment.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    lines = content.split('\n')
    fixed_lines = []
    changed = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for commented except blocks with FIXME
        if '# FIXME: Orphaned except/finally' in line and 'except' in line:
            # Extract the except statement
            match = re.search(r'#\s*(except[^:]*:)', line)
            if match:
                # Find the indent level
                indent_match = re.match(r'^(\s*)', line)
                indent = indent_match.group(1) if indent_match else ''
                
                # Look backwards for the matching try block
                j = i - 1
                while j >= 0:
                    if lines[j].strip().startswith('try:'):
                        # Found a try block, uncomment the except
                        fixed_lines.append(indent + match.group(1))
                        changed = True
                        i += 1
                        break
                    j -= 1
                else:
                    # No try found, keep the line as is
                    fixed_lines.append(line)
                    i += 1
            else:
                fixed_lines.append(line)
                i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines), changed


def fix_missing_except_blocks(content: str) -> tuple[str, bool]:
    """Add missing except blocks after try blocks.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    lines = content.split('\n')
    fixed_lines = []
    changed = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a try block
        if line.strip() == 'try:':
            # Add the try line
            fixed_lines.append(line)
            i += 1
            
            # Get the indentation level
            indent_match = re.match(r'^(\s*)try:', line)
            try_indent = indent_match.group(1) if indent_match else ''
            
            # Look for the next except/finally or unindented line
            found_handler = False
            j = i
            while j < len(lines):
                next_line = lines[j]
                
                # Check if we found except or finally at the right indentation
                if (next_line.strip().startswith('except ') or 
                    next_line.strip().startswith('except:') or
                    next_line.strip().startswith('finally:')):
                    next_indent = len(next_line) - len(next_line.lstrip())
                    expected_indent = len(try_indent)
                    if next_indent == expected_indent:
                        found_handler = True
                        break
                
                # Check if we've left the try block (unindented line)
                if next_line.strip() and not next_line.startswith(try_indent + '    '):
                    break
                    
                j += 1
            
            # If no handler found, add a generic except block
            if not found_handler and j > i:
                # First add all the lines in the try block
                for k in range(i, j):
                    if k < len(lines):
                        fixed_lines.append(lines[k])
                
                # Add the missing except block
                fixed_lines.append(try_indent + 'except Exception as e:')
                fixed_lines.append(try_indent + '    pass  # TODO: Handle exception')
                changed = True
                i = j
                continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines), changed


def fix_try_syntax_patterns(content: str) -> tuple[str, bool]:
    """Fix various try/except syntax patterns.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content
    
    # Fix patterns where try: appears on a line by itself when it shouldn't
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Skip if it's a proper try block
        if line.strip() == 'try:' and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Check if next line is properly indented
            if next_line.strip() and len(next_line) - len(next_line.lstrip()) > len(line) - len(line.lstrip()):
                fixed_lines.append(line)
                continue
        
        # Fix orphaned try: statements
        if line.strip() == 'try:' and i > 0:
            # Check if this is an orphaned try (no proper code block following)
            if i + 1 >= len(lines) or not lines[i + 1].strip():
                # Skip this orphaned try
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), '\n'.join(fixed_lines) != original


def fix_indentation_errors(content: str) -> tuple[str, bool]:
    """Fix indentation errors in try/except blocks.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    lines = content.split('\n')
    fixed_lines = []
    changed = False
    
    for i, line in enumerate(lines):
        # Fix lines that have "except Exception as e:" with wrong indentation
        if 'except Exception as e:' in line and i > 0:
            # Find the matching try block
            j = i - 1
            while j >= 0:
                if 'try:' in lines[j]:
                    try_indent = len(lines[j]) - len(lines[j].lstrip())
                    current_indent = len(line) - len(line.lstrip())
                    
                    # If except has different indentation than try, fix it
                    if current_indent != try_indent:
                        fixed_lines.append(' ' * try_indent + line.strip())
                        changed = True
                        continue
                    break
                j -= 1
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), changed


def process_file(file_path: Path) -> bool:
    """Process a single Python file.
    
    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Apply all fixes
        content, _ = fix_orphaned_except_blocks(content)
        content, _ = fix_missing_except_blocks(content)
        content, _ = fix_try_syntax_patterns(content)
        content, _ = fix_indentation_errors(content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            print(f"✓ Fixed: {file_path.relative_to(Path.cwd())}")
            return True
        
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