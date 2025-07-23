#!/usr/bin/env python3
"""
Fix the specific case where for loop bodies have wrong indentation.
"""

import sys
from pathlib import Path


def fix_for_loop_indentation(file_path: Path) -> bool:
    """Fix for loops where the body isn't indented."""
    
    print(f"\nFixing for loop indentation in {file_path}...")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if this is a for loop
        if stripped.startswith('for ') and stripped.endswith(':'):
            current_indent = len(line) - len(line.lstrip())
            print(f"Found for loop at line {i+1}: {stripped}")
            
            # Check next lines
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                
                if not next_stripped:
                    j += 1
                    continue
                    
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If next line has same or less indentation, it needs fixing
                if next_indent <= current_indent:
                    # Check if it's another block starter
                    if next_stripped.endswith(':'):
                        break
                    
                    # Fix the indentation
                    fixed_line = ' ' * (current_indent + 4) + next_stripped + '\n'
                    lines[j] = fixed_line
                    print(f"  Fixed line {j+1}: {next_stripped[:50]}...")
                    fixed = True
                    j += 1
                else:
                    # Properly indented, stop
                    break
        
        i += 1
    
    if fixed:
        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("\nFixed for loop indentation issues")
        
        # Verify syntax
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), str(file_path), 'exec')
            print("✓ File now has valid Python syntax")
            return True
        except SyntaxError as e:
            print(f"✗ Syntax error remains: {e}")
            return False
    else:
        print("No for loop indentation issues found")
        return True


def main():
    if len(sys.argv) != 2:
        print("Usage: fix_for_loop_indentation.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    success = fix_for_loop_indentation(file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()