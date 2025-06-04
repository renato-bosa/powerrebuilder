#!/usr/bin/env python3
"""Test real P-code extraction and decompilation."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from extract.pbd_core.library import Library
from decompile.opcodes import OPCODE_TABLE
from decompile.analysis.pcode_detector import PCodeDetector


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
            
            # Find functions
            functions = [e for e in entries if e.lower().endswith('.fun')]
            print(f"Found {len(functions)} functions")
            
            if functions:
                # Extract first function
                func_name = functions[0]
                print(f"\nExtracting: {func_name}")
                
                obj = lib[func_name]
                if obj and obj.data:
                    print(f"Data size: {len(obj.data)} bytes")
                    
                    # Detect P-code
                    detector = PCodeDetector()
                    pcode_sections = detector.detect_pcode_sections(obj.data)
                    
                    print(f"\nFound {len(pcode_sections)} P-code sections")
                    
                    if pcode_sections:
                        # Analyze first section
                        start, end = pcode_sections[0]
                        pcode_data = obj.data[start:end]
                        print(f"P-code section: offset {start:04X}-{end:04X} ({end-start} bytes)")
                        
                        # Show hex dump of first 100 bytes
                        print("\nFirst 100 bytes of P-code (hex):")
                        for i in range(0, min(100, len(pcode_data)), 16):
                            hex_str = ' '.join(f'{b:02x}' for b in pcode_data[i:i+16])
                            ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in pcode_data[i:i+16])
                            print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
                        
                        # Simple opcode analysis
                        analyze_pcode(pcode_data)
                        
                        # Save for further analysis
                        output_file = "output/test_real.pcode"
                        Path(output_file).parent.mkdir(exist_ok=True)
                        with open(output_file, 'wb') as f:
                            f.write(pcode_data)
                        print(f"\nSaved P-code to: {output_file}")
                        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def analyze_pcode(pcode_data):
    """Analyze P-code with corrected opcodes."""
    print("\nOpcode analysis with corrected mappings:")
    print("-" * 40)
    
    opcodes = OPCODE_TABLE
    
    # Simple decode
    pc = 0
    instructions = []
    unknown_count = 0
    
    while pc < min(len(pcode_data), 200):  # First 200 bytes
        opcode = pcode_data[pc]
        
        if opcode in opcodes:
            op_info = opcodes[opcode]
            mnemonic = op_info.get('mnemonic', f'OP_{opcode:02X}')
            instructions.append((pc, opcode, mnemonic))
        else:
            instructions.append((pc, opcode, f'UNKNOWN_{opcode:02X}'))
            unknown_count += 1
        
        pc += 1
    
    # Show first 20 instructions
    print("\nFirst 20 instructions:")
    for addr, opcode, mnemonic in instructions[:20]:
        print(f"  {addr:04X}: {opcode:02X} {mnemonic}")
    
    # Count known vs unknown
    print(f"\nSummary:")
    print(f"  Total instructions: {len(instructions)}")
    print(f"  Unknown opcodes: {unknown_count} ({unknown_count/len(instructions)*100:.1f}%)")
    
    # Frequency analysis
    freq = {}
    for _, opcode, _ in instructions:
        freq[opcode] = freq.get(opcode, 0) + 1
    
    print(f"\nMost common opcodes:")
    for opcode, count in sorted(freq.items(), key=lambda x: -x[1])[:10]:
        mnemonic = opcodes[opcode].get('mnemonic', f'UNKNOWN_{opcode:02X}') if opcode in opcodes else f'UNKNOWN_{opcode:02X}'
        print(f"  0x{opcode:02X} ({mnemonic:15s}): {count} times")


def main():
    """Main function."""
    test_real_pcode()


if __name__ == "__main__":
    main()