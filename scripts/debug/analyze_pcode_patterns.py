#!/usr/bin/env python3
"""Analyze P-code patterns to discover actual opcodes."""

import sys
from pathlib import Path
from collections import Counter
import struct

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def analyze_pcode_file(filepath):
    """Analyze patterns in a P-code file."""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\nAnalyzing: {filepath}")
    print(f"File size: {len(data)} bytes")
    print("=" * 80)
    
    # Frequency analysis
    byte_freq = Counter(data)
    print("\nMost common bytes:")
    for byte_val, count in byte_freq.most_common(20):
        print(f"  0x{byte_val:02x} ({byte_val:3d}): {count:5d} times ({count/len(data)*100:.1f}%)")
    
    # Look for patterns
    print("\nPattern analysis:")
    
    # Common sequences (2-byte)
    two_byte_seqs = Counter()
    for i in range(len(data) - 1):
        seq = (data[i], data[i+1])
        two_byte_seqs[seq] += 1
    
    print("\nMost common 2-byte sequences:")
    for seq, count in two_byte_seqs.most_common(10):
        print(f"  {seq[0]:02x} {seq[1]:02x}: {count} times")
    
    # Look for potential string markers
    print("\nPotential string locations (00 00 patterns):")
    for i in range(len(data) - 3):
        if data[i] == 0 and data[i+1] == 0:
            # Show context
            start = max(0, i-5)
            end = min(len(data), i+10)
            context = data[start:end]
            print(f"  Offset 0x{i:04x}: {' '.join(f'{b:02x}' for b in context)}")
            
            # Try to read as UTF-16
            if i > 2:
                length_candidate = data[i-2]
                if length_candidate < 50 and i >= 2 + length_candidate * 2:
                    str_start = i - length_candidate * 2
                    str_data = data[str_start:i]
                    try:
                        decoded = str_data.decode('utf-16-le')
                        if decoded.isprintable():
                            print(f"    Possible string: '{decoded}'")
                    except:
                        pass
    
    # Analyze instruction patterns
    print("\nInstruction pattern analysis:")
    
    # Look for STORE patterns (0x37 is common)
    store_count = data.count(0x37)
    print(f"  0x37 (possible STORE): {store_count} occurrences")
    
    # Look for CONST patterns (0x39 is common)
    const_count = data.count(0x39)
    print(f"  0x39 (possible CONST): {const_count} occurrences")
    
    # Look for function calls (patterns like 0x35 followed by string)
    call_patterns = []
    for i in range(len(data) - 10):
        if data[i] == 0x35:  # Possible CALL
            # Check if followed by a length byte and string
            length = data[i+1]
            if length > 0 and length < 50 and i + 2 + length <= len(data):
                try:
                    # Try ASCII
                    name = data[i+2:i+2+length].decode('ascii')
                    if name.isprintable() and name.isidentifier():
                        call_patterns.append((i, name))
                except:
                    pass
    
    if call_patterns:
        print(f"\n  Found {len(call_patterns)} possible function calls:")
        for offset, name in call_patterns[:5]:
            print(f"    Offset 0x{offset:04x}: CALL '{name}'")
    
    return data


def compare_with_verified_opcodes():
    """Compare patterns with verified opcodes."""
    print("\n\nVerified Opcodes Reference:")
    print("=" * 80)
    
    # Known opcodes from analysis
    verified_opcodes = {
        0x00: "RETURN/HALT",
        0x01: "CONST_INT8",
        0x37: "STORE/ASSIGN",
        0x39: "CONST/PUSH",
        0x35: "CALL_FUNCTION",
        0x04: "JUMP",
        0x02: "JUMP_TRUE",
        0x03: "JUMP_FALSE",
    }
    
    print("Common opcodes based on pattern analysis:")
    for opcode, name in sorted(verified_opcodes.items()):
        print(f"  0x{opcode:02x}: {name}")


def main():
    """Main analysis function."""
    if len(sys.argv) < 2:
        # Analyze test files
        test_files = [
            "tests/fixtures/pcode_files/test.pcode",
            "tests/fixtures/pcode_files/test_tj_report.pcode",
            "tests/fixtures/pcode_files/test_decode.pcode",
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                analyze_pcode_file(test_file)
        
        compare_with_verified_opcodes()
    else:
        analyze_pcode_file(sys.argv[1])


if __name__ == "__main__":
    main()