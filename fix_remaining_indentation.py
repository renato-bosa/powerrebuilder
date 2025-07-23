#!/usr/bin/env python3
"""
Final comprehensive indentation fix for detector.py
"""

import re
import sys
from pathlib import Path


def fix_remaining_indentation():
    """Apply comprehensive indentation fixes."""
    
    file_path = Path("src/decompile/pcode/detector.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix the specific patterns that are causing issues
    
    # Pattern 1: Fix blocks after if i == 0:
    content = re.sub(
        r'(\s+if i == 0:)\n(\s+)# First opcode',
        r'\1\n\2    # First opcode',
        content
    )
    
    # Pattern 2: Fix the multi-line set definition
    content = re.sub(
        r'(\s+)if byte in {\s*:\n',
        r'\1if byte in {\n',
        content
    )
    
    # Pattern 3: Fix lines that should be indented after if/elif/for/while
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        fixed_lines.append(line)
        
        # Check if this line ends with : and starts a block
        if stripped and stripped.endswith(':') and not stripped.startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            
            # Look ahead to see if next lines need indenting
            j = i + 1
            while j < len(lines) and j < i + 20:  # Look ahead up to 20 lines
                next_line = lines[j]
                next_stripped = next_line.strip()
                
                if not next_stripped or next_stripped.startswith('#'):
                    j += 1
                    continue
                    
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If the next line has same or less indentation, it might need fixing
                if next_indent <= current_indent:
                    # Check specific patterns that need fixing
                    if any([
                        next_stripped.startswith('if ') and not next_stripped.endswith(':'),
                        next_stripped.startswith('elif ') and not next_stripped.endswith(':'),
                        next_stripped.startswith('# '),
                        next_stripped in ['0x0B,', '0x0C,', '0x0D,', '0x2D,', '0x32,', '0x33,', '0x34,', '0x35,', '0x3A,', '0x3B,', '0x3C,', '}:'],
                        next_stripped.startswith('confidence +='),
                        next_stripped.startswith('logger.'),
                        next_stripped.startswith('return '),
                        next_stripped.startswith('stats['),
                        next_stripped.startswith('sections.'),
                        next_stripped.startswith('merged_sections'),
                        next_stripped.startswith('prev ='),
                        next_stripped.startswith('object_type ='),
                        next_stripped.startswith('confidence ='),
                        next_stripped.startswith('pcode_offset'),
                        next_stripped.startswith('pcode_length'),
                        next_stripped.startswith('low_confidence_bytes'),
                        next_stripped.startswith('hex_str ='),
                        next_stripped.startswith('ascii_str ='),
                        next_stripped.startswith('opcode_names ='),
                        next_stripped.startswith('opcodes_found.'),
                        next_stripped.startswith('byte ='),
                        next_stripped.startswith('chunk ='),
                        next_stripped.startswith('chunk_type ='),
                        next_stripped.startswith('sections_list.'),
                        next_stripped.startswith('current_type ='),
                        next_stripped.startswith('section_start ='),
                    ]):
                        # Skip - this line has already been processed in the fixed content
                        break
                else:
                    # Properly indented, stop checking
                    break
                    
                j += 1
        
        i += 1
    
    # Join the lines back
    content = '\n'.join(fixed_lines)
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Applied comprehensive indentation fixes to {file_path}")
    
    # Test compilation
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(file_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ File now compiles successfully!")
        return True
    else:
        print(f"✗ Still has errors: {result.stderr}")
        return False


if __name__ == "__main__":
    success = fix_remaining_indentation()
    sys.exit(0 if success else 1)