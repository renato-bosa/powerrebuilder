#!/usr/bin/env python3
"""Manual syntax fixes for PowerRebuilder project."""

import os
from pathlib import Path

def fix_decoder_py():
    """Fix src/decompile/pcode/decoder.py"""
    file_path = Path("src/decompile/pcode/decoder.py")
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Fix line 84: add if statement
    if lines[83].strip().startswith("pcode_bytes = object_data"):
        lines[84] = "                if pcode_size > 0:\n"
        lines[85] = "                    instructions = self.decode_pcode(\n"
        lines[86] = "                    pcode_bytes,\n"
        lines[87] = "                    entry_offset + pcode_offset,\n"
        lines[88] = "                    )\n"
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {file_path}")

def fix_recovery_py():
    """Fix src/decompile/pcode/recovery.py"""
    file_path = Path("src/decompile/pcode/recovery.py")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix unexpected indent - remove extra indentation
    lines = content.splitlines(keepends=True)
    if lines[10].startswith("    import logging"):
        lines[10] = "import logging\n"
        lines[11] = "from dataclasses import dataclass\n"
        lines[12] = "from typing import Any\n"
        lines[13] = "from src.decompile.pcode.decoder import PCodeInstruction\n"
        lines[14] = "\n"
        lines[15] = "@dataclass\n"
        lines[16] = "class RecoveryResult:\n"
        lines[17] = '    """Result of a recovery attempt."""\n'
        lines[18] = "    success: bool\n"
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {file_path}")

def fix_definitions_py():
    """Fix src/decompile/pcode/opcodes/definitions.py"""
    file_path = Path("src/decompile/pcode/opcodes/definitions.py")
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Fix line 16 unexpected indent
    if len(lines) > 15 and lines[15].lstrip().startswith("import logging"):
        # Find proper indentation level
        lines[15] = "import logging\n"
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {file_path}")

def fix_control_py():
    """Fix src/decompile/analysis/control.py"""
    file_path = Path("src/decompile/analysis/control.py")
    
    # Read file and find the unmatched parenthesis
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Look for line 344 with unmatched )
    if len(lines) > 343 and lines[343].strip() == ")":
        # Check previous lines for opening parenthesis
        for i in range(343, max(0, 333), -1):
            if "(" in lines[i]:
                # Found potential start, ensure proper closure
                break
        # Remove the standalone )
        lines[343] = ""
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {file_path}")

def fix_formatter_py():
    """Fix src/decompile/core/formatter.py"""
    file_path = Path("src/decompile/core/formatter.py")
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Fix line 623 unmatched parenthesis
    if len(lines) > 622:
        line = lines[622]
        if ") and i + 1 < len(decoded_obj.instructions):" in line:
            # Find the matching opening parenthesis
            # Likely missing opening parenthesis
            lines[622] = line.replace(") and i + 1", " and i + 1")
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {file_path}")

def fix_detector_py():
    """Fix src/decompile/pcode/detector.py"""
    file_path = Path("src/decompile/pcode/detector.py")
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Fix line 14 - unmatched parenthesis in function definition
    if len(lines) > 13 and "confidence: float = 0.0) -> None:" in lines[13]:
        # This looks like a parameter line - find the function def
        for i in range(13, -1, -1):
            if lines[i].strip().startswith("def "):
                # Found function definition, ensure it has opening (
                if "(" not in lines[i]:
                    lines[i] = lines[i].rstrip() + "(\n"
                break
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {file_path}")

def fix_variants_py():
    """Fix src/decompile/pcode/opcodes/variants.py"""
    file_path = Path("src/decompile/pcode/opcodes/variants.py")
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Fix line 423 - invalid elif without if
    if len(lines) > 422 and lines[422].strip().startswith("elif low_nibble == 0x09:"):
        # Find the corresponding if statement
        for i in range(422, max(0, 400), -1):
            if lines[i].strip().startswith("if ") and "low_nibble" in lines[i]:
                # Found it, check indentation
                expected_indent = len(lines[i]) - len(lines[i].lstrip())
                lines[422] = " " * expected_indent + lines[422].strip() + "\n"
                break
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {file_path}")

def fix_all_files():
    """Fix all files with syntax errors."""
    fixes = [
        fix_decoder_py,
        fix_recovery_py,
        fix_definitions_py,
        fix_control_py,
        fix_formatter_py,
        fix_detector_py,
        fix_variants_py,
    ]
    
    for fix_func in fixes:
        try:
            fix_func()
        except Exception as e:
            print(f"Error in {fix_func.__name__}: {e}")

if __name__ == "__main__":
    fix_all_files()