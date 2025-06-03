#!/usr/bin/env python3
"""Extract opcodes from reference YAML and create PowerBuilder opcode tables."""

import json
from pathlib import Path

import yaml


def determine_operand_hint(length):
    """Determine operand hint based on instruction length."""
    if length == 1:
        return None  # No operands
    if length == 2:
        return "uint8"  # 1-byte operand
    if length == 3:
        return "uint16le"  # 2-byte operand
    if length == 4:
        return "int16le"  # 2-byte signed (for jumps)
    if length == 5:
        return "uint32le"  # 4-byte operand
    if length == 6:
        return "uint32le"  # 4-byte operand + more
    return f"bytes[{length-1}]"  # Multiple bytes


def main():
    # Read the reference file
    ref_path = Path("reference/opcode_reference.yaml")
    with open(ref_path) as f:
        data = yaml.safe_load(f)

    # Also try JSON format if YAML fails
    if not data or 'opcodes' not in data:
        ref_path = Path("reference/opcode_reference.json")
        with open(ref_path) as f:
            data = json.load(f)

    opcodes = data.get('opcodes', {})

    # Create PowerBuilder 8.0 opcode table
    pb8_opcodes = {}

    for opcode_hex, info in opcodes.items():
        # Convert hex string to int
        if isinstance(opcode_hex, str):
            if opcode_hex.startswith('0x'):
                opcode_int = int(opcode_hex, 16)
            else:
                opcode_int = int(opcode_hex)
        else:
            opcode_int = opcode_hex

        name = info.get('name', f'UNKNOWN_{opcode_int:02X}')
        length = info.get('length', 1)

        # Special handling for specific opcodes
        operand_hint = None
        if name in ['JUMP', 'JUMPTRUE', 'JUMPFALSE', 'BRFALSE', 'BRTRUE']:
            if length == 2:
                operand_hint = "relative_offset_byte"
            elif length == 3:
                operand_hint = "relative_offset_short"
            elif length == 5:
                operand_hint = "relative_offset_int"
        elif name.startswith('PUSH_CONST_'):
            operand_hint = "uint16le"  # Constant pool index
        elif name.startswith('PUSH_LOCAL_VAR'):
            operand_hint = "uint8"  # Local variable index
        elif name.startswith('PUSH_GLOBAL_VAR'):
            operand_hint = "uint16le"  # Global variable index
        elif 'CALL' in name:
            operand_hint = "uint16le"  # Method/function index
        elif name.startswith('STORE_'):
            operand_hint = "uint8"  # Variable index
        elif name.startswith('DB'):
            if length > 1:
                operand_hint = "uint16le"
        else:
            operand_hint = determine_operand_hint(length)

        pb8_opcodes[opcode_int] = (name, length, operand_hint)

    # Generate Python file
    output_path = Path("decompile/opcode_tables/pb8_0.py")
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        f.write('"""PowerBuilder 8.0 opcode table.\n\n')
        f.write('Generated from reference implementations:\n')
        f.write('- https://github.com/hucxy/pbdviewer\n')
        f.write('- https://github.com/sijms/powerbuilder-decompile\n')
        f.write('"""\n\n')
        f.write('# Format: opcode -> (mnemonic, length, operand_hint)\n')
        f.write('OPCODES = {\n')

        # Sort by opcode value
        for opcode in sorted(pb8_opcodes.keys()):
            name, length, hint = pb8_opcodes[opcode]
            if hint:
                f.write(f'    0x{opcode:02X}: ("{name}", {length}, "{hint}"),\n')
            else:
                f.write(f'    0x{opcode:02X}: ("{name}", {length}, None),\n')

        f.write('}\n')

    print(f"Created {output_path} with {len(pb8_opcodes)} opcodes")

    # Also create a PowerBuilder 10.5 version (Unicode support)
    output_path = Path("decompile/opcode_tables/pb10_5.py")

    with open(output_path, 'w') as f:
        f.write('"""PowerBuilder 10.5 opcode table (Unicode version).\n\n')
        f.write('Generated from reference implementations.\n')
        f.write('This version includes Unicode support.\n')
        f.write('"""\n\n')
        f.write('# Import base opcodes from PB 8.0\n')
        f.write('from .pb8_0 import OPCODES as BASE_OPCODES\n\n')
        f.write('# PowerBuilder 10.5 uses the same opcodes as 8.0\n')
        f.write('# but with Unicode string handling\n')
        f.write('OPCODES = BASE_OPCODES.copy()\n')

    print(f"Created {output_path}")


if __name__ == '__main__':
    main()
