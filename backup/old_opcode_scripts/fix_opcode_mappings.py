#!/usr/bin/env python3
"""Fix opcode mappings based on reference implementations and pattern analysis."""

import sys
from pathlib import Path
import yaml
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def create_verified_opcodes():
    """Create verified opcode mappings from multiple sources."""
    
    # Opcodes verified from pbdviewer C# implementation
    pbdviewer_opcodes = {
        0x00: ("HALT", "Halt execution / Return"),
        0x01: ("PUSHCONST", "Push constant value"),
        0x02: ("PUSHVAR", "Push variable value"),
        0x03: ("POPVAR", "Pop value to variable"),
        0x04: ("CALL", "Call function"),
        0x05: ("RETURN", "Return from function"),
        0x15: ("ADD", "Add two values"),
        0x16: ("SUB", "Subtract two values"),
        0x17: ("MUL", "Multiply two values"),
        0x18: ("DIV", "Divide two values"),
    }
    
    # Opcodes from pattern analysis
    pattern_opcodes = {
        0x35: ("CALL_FUNC", "Call function by name"),
        0x37: ("STORE", "Store/assign value"),
        0x39: ("CONST", "Push constant"),
    }
    
    # Opcodes from powerbuilder-decompile analysis
    pb_decompile_opcodes = {
        0x02: ("JUMPTRUE", "Jump if true"),
        0x03: ("JUMPFALSE", "Jump if false"), 
        0x04: ("JUMP", "Unconditional jump"),
        0x0C: ("NEG", "Negate value"),
        0x19: ("MOD", "Modulo operation"),
        0x1A: ("POWER", "Power operation"),
        0x1F: ("EQ", "Equal comparison"),
        0x20: ("NE", "Not equal comparison"),
        0x21: ("GT", "Greater than"),
        0x22: ("LT", "Less than"),
        0x23: ("GE", "Greater or equal"),
        0x24: ("LE", "Less or equal"),
        0x25: ("NOT", "Logical NOT"),
        0x26: ("AND", "Logical AND"),
        0x27: ("OR", "Logical OR"),
    }
    
    # Merge all sources
    verified_opcodes = {}
    
    # Start with pbdviewer (most reliable)
    for opcode, (mnemonic, desc) in pbdviewer_opcodes.items():
        verified_opcodes[opcode] = {
            'mnemonic': mnemonic,
            'description': desc,
            'source': 'pbdviewer',
            'confidence': 'high',
            'category': 'verified'
        }
    
    # Add pattern analysis (override conflicts)
    for opcode, (mnemonic, desc) in pattern_opcodes.items():
        if opcode not in verified_opcodes:
            verified_opcodes[opcode] = {
                'mnemonic': mnemonic,
                'description': desc,
                'source': 'pattern_analysis',
                'confidence': 'medium',
                'category': 'verified'
            }
    
    # Add powerbuilder-decompile (don't override)
    for opcode, (mnemonic, desc) in pb_decompile_opcodes.items():
        if opcode not in verified_opcodes:
            verified_opcodes[opcode] = {
                'mnemonic': mnemonic,
                'description': desc,
                'source': 'powerbuilder-decompile',
                'confidence': 'medium',
                'category': 'verified'
            }
    
    # Add stack effects where known
    stack_effects = {
        0x00: "... -> ...",  # HALT
        0x01: "-> value",    # PUSHCONST
        0x02: "-> value",    # PUSHVAR
        0x03: "value ->",    # POPVAR
        0x04: "args... -> result",  # CALL
        0x05: "value ->",    # RETURN
        0x15: "a, b -> result",  # ADD
        0x16: "a, b -> result",  # SUB
        0x17: "a, b -> result",  # MUL
        0x18: "a, b -> result",  # DIV
        0x19: "a, b -> result",  # MOD
        0x1A: "a, b -> result",  # POWER
        0x1F: "a, b -> bool",    # EQ
        0x20: "a, b -> bool",    # NE
        0x21: "a, b -> bool",    # GT
        0x22: "a, b -> bool",    # LT
        0x23: "a, b -> bool",    # GE
        0x24: "a, b -> bool",    # LE
        0x25: "bool -> bool",    # NOT
        0x26: "a, b -> bool",    # AND
        0x27: "a, b -> bool",    # OR
        0x35: "args... -> result",  # CALL_FUNC
        0x37: "value ->",    # STORE
        0x39: "-> value",    # CONST
    }
    
    # Add operand info
    operands = {
        0x01: ["byte"],      # PUSHCONST - constant index
        0x02: ["byte"],      # PUSHVAR - variable index
        0x03: ["byte"],      # POPVAR - variable index
        0x04: ["byte"],      # CALL - function index
        0x35: ["byte", "string"],  # CALL_FUNC - name length, name
        0x37: ["byte"],      # STORE - variable index
        0x39: ["varies"],    # CONST - value follows
    }
    
    # Update with additional info
    for opcode in verified_opcodes:
        if opcode in stack_effects:
            verified_opcodes[opcode]['stack_effect'] = stack_effects[opcode]
        else:
            verified_opcodes[opcode]['stack_effect'] = '? -> ?'
            
        if opcode in operands:
            verified_opcodes[opcode]['operands'] = operands[opcode]
        else:
            verified_opcodes[opcode]['operands'] = []
        
        verified_opcodes[opcode]['updated'] = datetime.now().isoformat()
    
    return verified_opcodes


def save_corrected_opcodes():
    """Save the corrected opcode mappings."""
    verified = create_verified_opcodes()
    
    # Create a new clean opcode file
    output_file = project_root / 'extract' / 'pbd_core' / 'opcodes_corrected.yaml'
    
    # Convert to the format expected by the decoder
    output_data = {}
    for opcode, info in sorted(verified.items()):
        output_data[opcode] = info
    
    with open(output_file, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Saved {len(output_data)} corrected opcodes to {output_file}")
    
    # Show summary
    print("\nCorrected opcodes:")
    for opcode, info in sorted(verified.items()):
        print(f"  0x{opcode:02x}: {info['mnemonic']:15s} - {info['description']}")


def main():
    """Main function."""
    save_corrected_opcodes()
    
    print("\nNext steps:")
    print("1. Backup current opcodes.yaml")
    print("2. Replace with opcodes_corrected.yaml")
    print("3. Test with known P-code files")
    print("4. Iterate and refine based on results")


if __name__ == "__main__":
    main()