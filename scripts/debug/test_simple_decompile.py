#!/usr/bin/env python3
"""Simple test of decompiler with corrected opcodes."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from decompile.opcodes import OPCODE_TABLE


def analyze_with_corrected_opcodes(pcode_file):
    """Analyze P-code with corrected opcodes."""
    print(f"\nAnalyzing: {pcode_file}")
    print("=" * 80)
    
    # Use opcodes table
    opcodes = OPCODE_TABLE
    print(f"Loaded {len(opcodes)} opcode definitions")
    
    # Read P-code
    with open(pcode_file, 'rb') as f:
        data = f.read()
    
    print(f"P-code size: {len(data)} bytes")
    
    # Simple decode
    pc = 0
    instructions = []
    unknown_opcodes = set()
    
    while pc < len(data):
        opcode = data[pc]
        
        if opcode in opcodes:
            op_info = opcodes[opcode]
            mnemonic = op_info.get('mnemonic', f'OP_{opcode:02X}')
            
            # Simple operand handling
            operands = []
            pc += 1
            
            if 'operands' in op_info:
                for op_type in op_info['operands']:
                    if op_type == 'byte' and pc < len(data):
                        operands.append(data[pc])
                        pc += 1
                    elif op_type == 'string' and pc < len(data):
                        # Read string length
                        if pc < len(data):
                            str_len = data[pc]
                            pc += 1
                            if pc + str_len <= len(data):
                                str_data = data[pc:pc+str_len]
                                try:
                                    operands.append(str_data.decode('ascii'))
                                except:
                                    operands.append(f"<binary:{str_len}>")
                                pc += str_len
            
            instructions.append({
                'address': pc - 1,
                'opcode': opcode,
                'mnemonic': mnemonic,
                'operands': operands
            })
        else:
            unknown_opcodes.add(opcode)
            instructions.append({
                'address': pc,
                'opcode': opcode,
                'mnemonic': f'UNKNOWN_{opcode:02X}',
                'operands': []
            })
            pc += 1
    
    print(f"\nDecoded {len(instructions)} instructions")
    print(f"Unknown opcodes: {len(unknown_opcodes)}")
    
    # Show first 30 instructions
    print("\nFirst 30 instructions:")
    for i, instr in enumerate(instructions[:30]):
        operands_str = ", ".join(str(op) for op in instr['operands'])
        print(f"  {instr['address']:04X}: {instr['mnemonic']:15s} {operands_str}")
    
    # Count opcode usage
    opcode_counts = {}
    for instr in instructions:
        mnemonic = instr['mnemonic']
        opcode_counts[mnemonic] = opcode_counts.get(mnemonic, 0) + 1
    
    print(f"\nOpcode frequency (top 20):")
    for mnemonic, count in sorted(opcode_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {mnemonic:20s}: {count:5d}")
    
    # Show unknown opcodes
    if unknown_opcodes:
        print(f"\nUnknown opcodes ({len(unknown_opcodes)}):")
        for opcode in sorted(unknown_opcodes)[:20]:
            print(f"  0x{opcode:02x} ({opcode:3d})")
    
    # Look for patterns
    print("\nPattern analysis:")
    
    # Count STORE operations
    store_count = sum(1 for instr in instructions if instr['mnemonic'] == 'STORE')
    print(f"  STORE operations: {store_count}")
    
    # Count CONST operations
    const_count = sum(1 for instr in instructions if instr['mnemonic'] == 'CONST')
    print(f"  CONST operations: {const_count}")
    
    # Count arithmetic operations
    arith_ops = ['ADD', 'SUB', 'MUL', 'DIV', 'MOD']
    arith_count = sum(1 for instr in instructions if instr['mnemonic'] in arith_ops)
    print(f"  Arithmetic operations: {arith_count}")
    
    # Count PUSH/POP operations
    push_count = sum(1 for instr in instructions if 'PUSH' in instr['mnemonic'])
    pop_count = sum(1 for instr in instructions if 'POP' in instr['mnemonic'])
    print(f"  PUSH operations: {push_count}")
    print(f"  POP operations: {pop_count}")
    
    return len(instructions), len(unknown_opcodes)


def main():
    """Main test function."""
    test_files = [
        "tests/fixtures/pcode_files/test.pcode",
        "tests/fixtures/pcode_files/test_tj_report.pcode",
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            analyze_with_corrected_opcodes(test_file)


if __name__ == "__main__":
    main()