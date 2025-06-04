#!/usr/bin/env python3
"""Test real P-code extraction - simplified version."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from extract.pbd_core.library import Library
from decompile.opcodes import OPCODE_TABLE


def find_pcode_section(data):
    """Simple P-code detection."""
    # Look for common P-code patterns
    # P-code often starts after a sequence of nulls or specific markers
    
    for i in range(len(data) - 100):
        # Look for potential P-code start
        # Common pattern: sequence of low bytes (opcodes) followed by data
        if i > 10:
            # Check if we have a run of bytes that could be opcodes
            potential_opcodes = data[i:i+20]
            
            # Most opcodes are < 0x80
            opcode_like = sum(1 for b in potential_opcodes if b < 0x80)
            
            if opcode_like > 15:  # Most bytes look like opcodes
                # Check for common patterns
                if any(b in [0x00, 0x01, 0x02, 0x03, 0x04, 0x05] for b in potential_opcodes[:5]):
                    return i
    
    # Fallback: skip header (usually first 100-200 bytes)
    return 200 if len(data) > 200 else 0


def test_real_pcode():
    """Test with real P-code from PBD file."""
    pbd_file = "tests/fixtures/pbd_files/dcm_email.pbd"
    
    print(f"Extracting from: {pbd_file}")
    print("=" * 80)
    
    try:
        with Library(pbd_file) as lib:
            # List entries
            entries = lib.list_entries()
            print(f"Found {len(entries)} entries")
            
            # Find functions or any compiled objects
            compiled_objects = []
            for entry in entries:
                if any(entry.lower().endswith(ext) for ext in ['.fun', '.srf', '.udo', '.win']):
                    compiled_objects.append(entry)
            
            print(f"Found {len(compiled_objects)} compiled objects")
            
            if compiled_objects:
                # Try first few objects
                for obj_name in compiled_objects[:3]:
                    print(f"\nExtracting: {obj_name}")
                    
                    obj = lib[obj_name]
                    if obj and obj.data:
                        print(f"Data size: {len(obj.data)} bytes")
                        
                        # Find P-code section
                        pcode_start = find_pcode_section(obj.data)
                        
                        if pcode_start < len(obj.data) - 50:
                            pcode_data = obj.data[pcode_start:]
                            
                            # Show hex dump
                            print(f"\nP-code starting at offset {pcode_start:04X}:")
                            for i in range(0, min(160, len(pcode_data)), 16):
                                hex_str = ' '.join(f'{b:02x}' for b in pcode_data[i:i+16])
                                ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in pcode_data[i:i+16])
                                print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
                            
                            # Analyze opcodes
                            analyze_pcode(pcode_data[:500])
                            
                            # Save first object for analysis
                            if obj_name == compiled_objects[0]:
                                output_file = f"output/real_{Path(obj_name).stem}.pcode"
                                Path(output_file).parent.mkdir(exist_ok=True)
                                with open(output_file, 'wb') as f:
                                    f.write(pcode_data[:1000])  # First 1KB
                                print(f"\nSaved P-code sample to: {output_file}")
                        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def analyze_pcode(pcode_data):
    """Analyze P-code with corrected opcodes."""
    print("\nOpcode analysis:")
    print("-" * 40)
    
    opcodes = OPCODE_TABLE
    
    # Count byte frequencies
    freq = {}
    for b in pcode_data:
        freq[b] = freq.get(b, 0) + 1
    
    print("Most common bytes:")
    for byte_val, count in sorted(freq.items(), key=lambda x: -x[1])[:20]:
        mnemonic = "?"
        if byte_val in opcodes:
            mnemonic = opcodes[byte_val].get('mnemonic', '?')
        print(f"  0x{byte_val:02X} ({byte_val:3d}) {mnemonic:15s}: {count} times")
    
    # Look for specific patterns
    print("\nPattern search:")
    
    # RETURN (0x00 or 0x05)
    returns = pcode_data.count(0x00) + pcode_data.count(0x05)
    print(f"  Potential RETURNs: {returns}")
    
    # Arithmetic ops (0x15-0x18)
    arith = sum(pcode_data.count(op) for op in range(0x15, 0x19))
    print(f"  Arithmetic ops: {arith}")
    
    # Look for sequences
    print("\nInteresting sequences:")
    for i in range(len(pcode_data) - 10):
        # Look for PUSH followed by POP
        if pcode_data[i] in [0x01, 0x02] and pcode_data[i+1] == 0x03:
            print(f"  {i:04X}: PUSH->POP sequence")
        
        # Look for CALL patterns
        if pcode_data[i] == 0x04:
            print(f"  {i:04X}: CALL (next byte: 0x{pcode_data[i+1]:02X})")
        
        # Only show first few
        if i > 100:
            break


def main():
    """Main function."""
    test_real_pcode()


if __name__ == "__main__":
    main()