#!/usr/bin/env python3
"""Test P-code extraction to see raw bytes."""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extract.pbd.extraction.library import Library
from extract.pbd.structures.data_block import get_binary_from_data

def test_extract_pcode():
    """Extract P-code and show hex dump."""
    
    pbd_path = Path("input/pbd_files/dcm_accounting.pbd")
    object_name = "of_get_linked_acc.fun"
    
    print(f"Extracting {object_name} from {pbd_path.name}")
    
    with Library(str(pbd_path)) as library:
        if object_name not in library.entries_map:
            print(f"Object {object_name} not found")
            return
        
        # Check entry first
        entry = library.entries_map[object_name]
        print(f"Entry: {entry}")
        
        # Get the PBD object
        try:
            pbd_obj = library[object_name]
        except Exception as e:
            print(f"Error getting object: {e}")
            
            # Try manual extraction
            print("\nTrying manual extraction...")
            with open(pbd_path, 'rb') as f:
                f.seek(entry.offset)
                data = f.read(entry.objectsize)
                print(f"Read {len(data)} bytes from offset 0x{entry.offset:x}")
                binary_data = data
        
        else:
            # Get binary data
            binary_data = get_binary_from_data(pbd_obj)
        
        if binary_data:
            print(f"\nTotal size: {len(binary_data)} bytes")
            print(f"\nFirst 256 bytes (hex):")
            
            # Print hex dump
            for i in range(0, min(256, len(binary_data)), 16):
                hex_part = ' '.join(f'{b:02x}' for b in binary_data[i:i+16])
                ascii_part = ''.join(
                    chr(b) if 32 <= b < 127 else '.' 
                    for b in binary_data[i:i+16]
                )
                print(f"{i:04x}: {hex_part:<48} {ascii_part}")
            
            # Look for P-code markers
            print("\n\nSearching for P-code markers...")
            
            # Check for known patterns
            for i in range(len(binary_data) - 4):
                # Look for potential P-code start
                if binary_data[i:i+2] == b'\x00\x00' and binary_data[i+2] != 0:
                    print(f"Potential P-code start at 0x{i:04x}")
                    if i > 0:
                        # Show context
                        start = max(0, i - 16)
                        end = min(len(binary_data), i + 32)
                        print(f"Context [{start:04x}-{end:04x}]:")
                        for j in range(start, end, 16):
                            hex_part = ' '.join(f'{b:02x}' for b in binary_data[j:j+16])
                            print(f"  {j:04x}: {hex_part}")
                        print()


if __name__ == "__main__":
    test_extract_pcode()