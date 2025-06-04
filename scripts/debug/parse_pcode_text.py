#!/usr/bin/env python3
"""Parse text-format P-code files and extract actual opcodes."""

import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from decompile.opcodes import OPCODE_TABLE


def parse_text_pcode(filename):
    """Parse text-format P-code file."""
    print(f"\nParsing text P-code: {filename}")
    print("=" * 80)
    
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Look for lines with format "XXXX: OPCODE_NAME args"
    pattern = r'^([0-9A-F]{4}):\s+(\w+)(?:\s+(.*))?$'
    
    instructions = []
    for line in content.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            addr = int(match.group(1), 16)
            opcode = match.group(2)
            args = match.group(3) or ""
            
            instructions.append({
                'address': addr,
                'opcode': opcode,
                'args': args,
                'line': line.strip()
            })
    
    print(f"Found {len(instructions)} instructions")
    
    # Show first 30
    print("\nFirst 30 instructions:")
    for instr in instructions[:30]:
        print(f"  {instr['address']:04X}: {instr['opcode']:20s} {instr['args']}")
    
    # Count opcodes
    opcode_counts = {}
    for instr in instructions:
        opcode = instr['opcode']
        opcode_counts[opcode] = opcode_counts.get(opcode, 0) + 1
    
    print(f"\nOpcode frequency (top 20):")
    for opcode, count in sorted(opcode_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {opcode:25s}: {count:5d}")
    
    # Analyze patterns
    print("\nPattern analysis:")
    
    # Function structure
    func_starts = sum(1 for i in instructions if i['opcode'] == 'FUNCTION_START')
    func_ends = sum(1 for i in instructions if i['opcode'] == 'FUNCTION_END')
    print(f"  Functions: {func_starts} starts, {func_ends} ends")
    
    # Control flow
    jumps = sum(1 for i in instructions if 'JUMP' in i['opcode'])
    conditionals = sum(1 for i in instructions if i['opcode'] in ['JUMPTRUE', 'JUMPFALSE'])
    print(f"  Jumps: {jumps} total, {conditionals} conditional")
    
    # Data operations
    stores = sum(1 for i in instructions if 'STORE' in i['opcode'])
    loads = sum(1 for i in instructions if 'LOAD' in i['opcode'])
    consts = sum(1 for i in instructions if 'CONST' in i['opcode'] or i['opcode'] == 'STRING')
    print(f"  Data: {stores} stores, {loads} loads, {consts} constants")
    
    # Look for actual opcode values in comments
    hex_pattern = r'0x([0-9A-F]{2})'
    found_opcodes = []
    for instr in instructions:
        if 'args' in instr and instr['args']:
            hex_matches = re.findall(hex_pattern, instr['args'])
            for hex_val in hex_matches:
                found_opcodes.append((instr['opcode'], int(hex_val, 16)))
    
    if found_opcodes:
        print(f"\nFound {len(found_opcodes)} potential opcode mappings:")
        for name, value in found_opcodes[:20]:
            print(f"  {name:20s} -> 0x{value:02x}")
    
    return instructions


def create_opcode_mapping(instructions):
    """Try to create opcode mapping from text format."""
    mapping = {}
    
    # Known mappings from our corrected opcodes
    known = {
        'HALT': 0x00,
        'PUSHCONST': 0x01,
        'PUSHVAR': 0x02,
        'POPVAR': 0x03,
        'CALL': 0x04,
        'RETURN': 0x05,
        'ADD': 0x15,
        'SUB': 0x16,
        'MUL': 0x17,
        'DIV': 0x18,
        'STORE': 0x37,
        'CONST': 0x39,
    }
    
    # Try to infer from instruction sequence
    for i, instr in enumerate(instructions):
        opcode_name = instr['opcode']
        
        # Check if we have a hex value in args
        if instr['args'] and instr['args'].startswith('0x'):
            try:
                hex_val = int(instr['args'].split()[0], 16)
                if opcode_name not in mapping:
                    mapping[opcode_name] = hex_val
            except:
                pass
    
    # Add known mappings
    mapping.update(known)
    
    return mapping


def main():
    """Main function."""
    test_files = [
        "tests/fixtures/pcode_files/test.pcode",
        "tests/fixtures/pcode_files/test_tj_report.pcode",
    ]
    
    all_instructions = []
    for test_file in test_files:
        if Path(test_file).exists():
            instructions = parse_text_pcode(test_file)
            all_instructions.extend(instructions)
    
    # Try to create mapping
    mapping = create_opcode_mapping(all_instructions)
    
    print("\n\nInferred opcode mappings:")
    print("=" * 80)
    for name, value in sorted(mapping.items(), key=lambda x: x[1]):
        print(f"  0x{value:02x}: {name}")


if __name__ == "__main__":
    main()