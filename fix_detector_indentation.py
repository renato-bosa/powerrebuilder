#!/usr/bin/env python3
"""
Fix the specific indentation pattern in detector.py where statements after
if/for/while blocks have the same indentation as the block starter.
"""

import sys
import shutil
from pathlib import Path
import re


def fix_detector_indentation(file_path: Path) -> bool:
    """Fix indentation where block contents have same indent as block starter."""
    
    print(f"\nFixing indentation in {file_path}...")
    
    # Backup the file
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    changes_made = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        # Add current line
        fixed_lines.append(line)
        
        # Check if this line starts a block
        if stripped and stripped.endswith(':') and not stripped.startswith('#'):
            # This is a block starter (if, for, while, def, class, etc.)
            block_indent = current_indent
            expected_indent = block_indent + 4
            
            # Look at subsequent lines
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # Skip empty lines
                if not next_stripped:
                    j += 1
                    continue
                
                # Skip comments
                if next_stripped.startswith('#'):
                    j += 1
                    continue
                
                # Check if this line has the same indentation as the block starter
                if next_indent == block_indent and not next_stripped.endswith(':'):
                    # This line should be indented more
                    print(f"  Line {j+1}: Fixing indentation - '{next_stripped[:30]}...' should be indented")
                    changes_made += 1
                    
                    # Fix all lines at this wrong indentation level until we hit a proper block
                    while j < len(lines):
                        fix_line = lines[j]
                        fix_stripped = fix_line.strip()
                        fix_indent = len(fix_line) - len(fix_line.lstrip())
                        
                        if not fix_stripped:
                            j += 1
                            continue
                            
                        if fix_stripped.startswith('#'):
                            j += 1  
                            continue
                        
                        # Stop if we hit a line with different indentation or a new block
                        if fix_indent != block_indent or fix_stripped.endswith(':'):
                            break
                        
                        # Fix this line
                        lines[j] = ' ' * expected_indent + fix_stripped + '\n'
                        j += 1
                    
                    # Continue from where we left off
                    i = j - 1
                    break
                else:
                    # Indentation looks correct, stop checking
                    break
        
        i += 1
    
    # Reconstruct the file with fixed lines
    if changes_made > 0:
        # Re-read and fix
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check if this line starts a block
            if stripped and stripped.endswith(':') and not stripped.startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                i += 1
                
                # Fix subsequent lines at wrong indentation
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    
                    if not next_stripped:
                        fixed_lines.append(next_line)
                        i += 1
                        continue
                    
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # If line has same or less indentation than block starter, it needs fixing
                    if next_indent <= current_indent and not next_stripped.startswith('#'):
                        # Check if it's a block ender or new block
                        if re.match(r'^(class|def|if|elif|else|try|except|finally|for|while|with)', next_stripped) and \
                           next_stripped.endswith(':'):
                            break
                        
                        # Fix indentation
                        fixed_line = ' ' * (current_indent + 4) + next_stripped
                        fixed_lines.append(fixed_line)
                        print(f"  Fixed line {i+1}: {next_stripped[:40]}...")
                        i += 1
                    else:
                        # Properly indented or comment
                        fixed_lines.append(next_line)
                        i += 1
                        
                        # Stop if we see proper indentation
                        if next_indent > current_indent:
                            break
            else:
                fixed_lines.append(line)
                i += 1
        
        # Write fixed content
        fixed_content = '\n'.join(fixed_lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"\nFixed indentation issues")
        
        # Verify syntax
        try:
            compile(fixed_content, str(file_path), 'exec')
            print("✓ File now has valid Python syntax")
            backup_path.unlink()
            return True
        except SyntaxError as e:
            print(f"✗ Syntax error remains: {e}")
            # Restore from backup
            shutil.copy2(backup_path, file_path)
            print("Restored from backup")
            return False
    else:
        print("No indentation issues found")
        backup_path.unlink()
        return True


def main():
    if len(sys.argv) != 2:
        print("Usage: fix_detector_indentation.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    success = fix_detector_indentation(file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()