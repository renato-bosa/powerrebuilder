#!/usr/bin/env python3
"""
Incrementally fix indentation issues by applying fixes one at a time
and checking syntax after each fix.
"""

import sys
import shutil
from pathlib import Path
import re
import subprocess


def check_syntax(file_path: Path) -> tuple[bool, str]:
    """Check if file has valid syntax."""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(file_path)],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return True, ""
    else:
        return False, result.stderr


def fix_indentation_incremental(file_path: Path) -> bool:
    """Fix indentation issues incrementally."""
    
    print(f"\nFixing indentation in {file_path}...")
    
    # Backup the file
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    total_fixes = 0
    max_iterations = 20  # Prevent infinite loops
    
    for iteration in range(max_iterations):
        print(f"\nIteration {iteration + 1}...")
        
        # Read current content
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find and fix one issue at a time
        fix_applied = False
        
        for i in range(len(lines) - 1):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check if this line ends with : (block starter)
            if stripped.endswith(':') and not stripped.startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                
                # Look at the next non-empty line
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    
                    if not next_stripped or next_stripped.startswith('#'):
                        j += 1
                        continue
                    
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # Check if next line needs indenting
                    if next_indent <= current_indent:
                        # Skip if it's another block starter
                        if next_stripped.endswith(':'):
                            break
                        
                        # Apply fix
                        fixed_line = ' ' * (current_indent + 4) + next_stripped + '\n'
                        lines[j] = fixed_line
                        
                        # Write the fix
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                        
                        print(f"  Fixed line {j+1}: {next_stripped[:50]}...")
                        total_fixes += 1
                        fix_applied = True
                        break
                    else:
                        # Line already indented correctly
                        break
                
                if fix_applied:
                    break
        
        if not fix_applied:
            print("  No more fixes needed")
            break
        
        # Check syntax after each fix
        valid, error = check_syntax(file_path)
        if not valid and "expected an indented block" not in error:
            print(f"  New error introduced: {error}")
            print("  Stopping fixes")
            break
    
    # Final syntax check
    valid, error = check_syntax(file_path)
    if valid:
        print(f"\n✓ Success! Fixed {total_fixes} indentation issues")
        print("✓ File now has valid Python syntax")
        backup_path.unlink()
        return True
    else:
        print(f"\n✗ Still has syntax errors after {total_fixes} fixes:")
        print(f"  {error}")
        
        # Keep partial fixes by default in non-interactive mode
        print("Keeping partial fixes...")
        
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: fix_indentation_incremental.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    success = fix_indentation_incremental(file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()