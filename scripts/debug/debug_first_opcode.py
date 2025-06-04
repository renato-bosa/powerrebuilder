#!/usr/bin/env python3
"""Debug tool to examine the first bytes of P-code files and decode them."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from decompile.opcodes import OPCODE_TABLE


def debug_first_bytes(pcode_file: str) -> None:
    """Debug the first bytes of a P-code file."""
    with open(pcode_file, 'rb') as f:
        data = f.read(100)  # First 100 bytes
    
    print(f"Analyzing: {pcode_file}")
    print("=" * 80)
    
    # Show raw bytes
    print("\nFirst 20 bytes (hex):")
    print(" ".join(f"{b:02x}" for b in data[:20]))
    
    print("\nFirst 20 bytes (decimal):")
    print(" ".join(f"{b:3d}" for b in data[:20]))
    
    # Look for patterns
    print("\nByte frequency in first 100 bytes:")
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    
    for byte, count in sorted(freq.items(), key=lambda x: -x[1])[:10]:
        print(f"  0x{byte:02x} ({byte:3d}): {count} times")
    
    # Try to interpret as opcodes
    print("\nTrying to decode as opcodes (using our opcode table):")
    opcodes = OPCODE_TABLE
    
    pc = 0
    decoded = []
    while pc < min(len(data), 50):  # First 50 bytes
        opcode = data[pc]
        
        if opcode in opcodes:
            op_info = opcodes[opcode]
            decoded.append(f"  {pc:04x}: 0x{opcode:02x} {op_info.get('mnemonic', 'UNKNOWN')}")
            pc += 1
            
            # Skip operands if we know the size
            if 'size' in op_info:
                pc += op_info['size'] - 1
        else:
            decoded.append(f"  {pc:04x}: 0x{opcode:02x} *** UNKNOWN ***")
            pc += 1
    
    print("\n".join(decoded[:20]))  # First 20 decoded
    
    # Look for string patterns (often UTF-16 in PowerBuilder)
    print("\nPossible strings (UTF-16 LE):")
    try:
        # Try to decode as UTF-16 LE
        text = data.decode('utf-16-le', errors='ignore')
        printable = ''.join(c if c.isprintable() else '.' for c in text)
        if any(c.isalpha() for c in printable):
            print(f"  {printable[:80]}")
    except:
        pass
    
    # Look for ASCII strings
    print("\nPossible strings (ASCII):")
    ascii_str = ""
    for b in data:
        if 32 <= b <= 126:  # Printable ASCII
            ascii_str += chr(b)
        else:
            if len(ascii_str) > 3:  # String of at least 4 chars
                print(f"  {ascii_str}")
            ascii_str = ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_first_opcode.py <pcode_file>")
        sys.exit(1)
    
    debug_first_bytes(sys.argv[1])