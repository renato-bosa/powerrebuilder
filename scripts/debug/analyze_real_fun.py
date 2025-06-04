#!/usr/bin/env python3
"""Analyze real .fun P-code files."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from decompile.opcodes import OPCODE_TABLE


def analyze_fun_file(filename):
    """Analyze a .fun P-code file."""
    print(f"\nAnalyzing: {filename}")
    print("=" * 80)
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Show hex dump of first 200 bytes
    print("\nFirst 200 bytes (hex dump):")
    for i in range(0, min(200, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    # Use opcodes table
    opcodes = OPCODE_TABLE
    
    # Frequency analysis
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    
    print("\nByte frequency (top 30):")
    for byte_val, count in sorted(freq.items(), key=lambda x: -x[1])[:30]:
        percentage = count / len(data) * 100
        opcode_name = ""
        if byte_val in opcodes:
            opcode_name = opcodes[byte_val].get('mnemonic', '')
        print(f"  0x{byte_val:02X} ({byte_val:3d}) {opcode_name:15s}: {count:5d} ({percentage:5.1f}%)")
    
    # Look for P-code patterns
    print("\nLooking for P-code patterns...")
    
    # Find potential P-code start
    pcode_start = None
    for i in range(len(data) - 50):
        # Look for sequences of known opcodes
        known_count = 0
        for j in range(10):
            if i + j < len(data) and data[i + j] in opcodes:
                known_count += 1
        
        if known_count >= 5:  # At least 5 known opcodes in 10 bytes
            pcode_start = i
            print(f"Potential P-code start at offset: 0x{i:04X}")
            break
    
    if pcode_start is None:
        # Try another approach - look for low byte values
        for i in range(100, min(500, len(data) - 50)):
            low_count = sum(1 for j in range(20) if data[i + j] < 0x40)
            if low_count > 15:
                pcode_start = i
                print(f"Potential P-code start at offset: 0x{i:04X} (low byte pattern)")
                break
    
    if pcode_start is not None:
        # Decode some instructions
        print(f"\nDecoding from offset 0x{pcode_start:04X}:")
        pc = pcode_start
        for _ in range(30):  # Decode 30 instructions
            if pc >= len(data):
                break
            
            opcode = data[pc]
            if opcode in opcodes:
                info = opcodes[opcode]
                mnemonic = info.get('mnemonic', f'OP_{opcode:02X}')
                print(f"  {pc:04X}: {opcode:02X} {mnemonic}")
            else:
                print(f"  {pc:04X}: {opcode:02X} UNKNOWN")
            
            pc += 1
            
            # Skip operands (simplified)
            if opcode in opcodes and 'operands' in opcodes[opcode]:
                for op_type in opcodes[opcode]['operands']:
                    if op_type == 'byte' and pc < len(data):
                        print(f"         {data[pc]:02X} (operand)")
                        pc += 1
    
    # Look for specific patterns
    print("\nSpecific pattern search:")
    
    # Null terminators (common in data sections)
    null_count = data.count(0x00)
    print(f"  Null bytes (0x00): {null_count} ({null_count/len(data)*100:.1f}%)")
    
    # Common opcodes
    for op_val, op_name in [(0x01, "PUSHCONST"), (0x02, "PUSHVAR"), (0x03, "POPVAR"), 
                             (0x04, "CALL"), (0x05, "RETURN"), (0x37, "STORE"), (0x39, "CONST")]:
        count = data.count(op_val)
        if count > 0:
            print(f"  {op_name} (0x{op_val:02X}): {count} occurrences")


def main():
    """Main function."""
    test_files = [
        "output/test_bytes_fix/dcm_login.pbd/dcm_login.pbd/f_get_username.fun",
        "output/test_bytes_fix/pfcapsrv.pbd/pfcapsrv.pbd/f_setplatform.fun",
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            analyze_fun_file(test_file)
        else:
            print(f"File not found: {test_file}")


if __name__ == "__main__":
    main()