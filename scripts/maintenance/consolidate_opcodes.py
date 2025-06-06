#!/usr/bin/env python3
"""Script to consolidate opcode implementations."""

import shutil
from pathlib import Path


def consolidate_opcodes():
    """Consolidate duplicate opcode implementations."""
    project_root = Path(__file__).parent.parent.parent
    
    # The decompile version is more comprehensive and actively used
    # We'll remove the extract version and update imports
    
    extract_opcodes = project_root / "extract" / "pbd_core" / "opcodes.py"
    extract_opcodes_yaml = project_root / "extract" / "pbd_core" / "opcodes.yaml"
    
    if extract_opcodes.exists():
        print(f"Removing extract opcode implementation: {extract_opcodes}")
        extract_opcodes.unlink()
        print("✓ Removed extract/pbd_core/opcodes.py")
    
    if extract_opcodes_yaml.exists():
        print(f"Removing extract opcode YAML: {extract_opcodes_yaml}")
        extract_opcodes_yaml.unlink()
        print("✓ Removed extract/pbd_core/opcodes.yaml")
    
    # Update extract/pbd_core/__init__.py to not import opcodes
    init_file = project_root / "extract" / "pbd_core" / "__init__.py"
    if init_file.exists():
        print("Updating extract/pbd_core/__init__.py to remove opcode imports")
        
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Remove opcode-related imports and exports
        lines = content.split('\n')
        new_lines = []
        skip_until_close = False
        
        for line in lines:
            if 'from .opcodes import' in line:
                skip_until_close = True
                continue
            if skip_until_close and ')' in line:
                skip_until_close = False
                continue
            if skip_until_close:
                continue
            
            # Remove from __all__ list
            if any(item in line for item in ['"load_opcodes"', '"get_opcode_info"', '"log_unknown_opcode"',
                                              '"attempt_symbolic_fallback"', '"SymbolicStack"', '"CFGNode"', 
                                              '"FallbackResult"']):
                continue
            
            new_lines.append(line)
        
        # Write updated content
        with open(init_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✓ Updated extract/pbd_core/__init__.py")
    
    # Check if any files need to be updated to import from decompile.opcodes instead
    print("\nNote: If any code was using extract.pbd_core.opcodes, update imports to use decompile.opcodes instead")
    
    print("\nOpcode consolidation complete!")


if __name__ == "__main__":
    consolidate_opcodes()