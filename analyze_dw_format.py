#!/usr/bin/env python3
"""Analyze DataWindow binary format to find the syntax offset and structure."""

import struct
from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE

def analyze_datawindow_structure(data):
    """Analyze DataWindow binary structure in detail."""
    print(f"Total size: {len(data)} bytes")
    print(f"First 64 bytes (hex): {data[:64].hex()}")
    print()
    
    # Look for potential syntax length fields (4-byte integers)
    print("Potential syntax length fields (4-byte integers):")
    for offset in range(0, min(64, len(data) - 4), 4):
        value = struct.unpack('<I', data[offset:offset+4])[0]
        if 100 < value < len(data):  # Reasonable size for syntax
            print(f"  Offset 0x{offset:02x}: {value} (0x{value:x})")
            
            # Check if this could be a valid syntax length
            if offset + 4 + value <= len(data):
                # Try to decode the data at this position as UTF-16
                test_data = data[offset + 4:offset + 4 + min(value, 200)]
                for encoding in ['utf-16-le', 'utf-16-be', 'utf-16']:
                    try:
                        decoded = test_data.decode(encoding, errors='strict')
                        if any(keyword in decoded.lower() for keyword in ['release', 'datawindow', 'table', 'column']):
                            print(f"    → Likely syntax at offset 0x{offset:02x} + 4!")
                            print(f"    → First 100 chars ({encoding}): {decoded[:100]}")
                            return offset + 4, value, encoding
                    except:
                        pass
    
    # Try looking further into the file
    print("\nSearching for DataWindow syntax patterns...")
    for offset in range(0, min(len(data) - 100, 1000), 1):
        chunk = data[offset:offset+100]
        
        # Check for UTF-16 encoded "release" or "datawindow"
        for pattern, encoding in [
            (b'r\x00e\x00l\x00e\x00a\x00s\x00e\x00', 'utf-16-le'),
            (b'\x00r\x00e\x00l\x00e\x00a\x00s\x00e', 'utf-16-be'),
            (b'd\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w\x00', 'utf-16-le'),
            (b'\x00d\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w', 'utf-16-be'),
        ]:
            if pattern in chunk:
                print(f"\nFound pattern at offset 0x{offset:x}!")
                
                # Look backwards for a length field
                for length_offset in range(max(0, offset - 20), offset, 4):
                    if length_offset + 4 <= len(data):
                        potential_length = struct.unpack('<I', data[length_offset:length_offset+4])[0]
                        if length_offset + 4 + potential_length >= offset + len(pattern):
                            print(f"  Potential length field at 0x{length_offset:x}: {potential_length}")
                            
                            # Verify by trying to decode
                            syntax_start = length_offset + 4
                            syntax_data = data[syntax_start:syntax_start + potential_length]
                            try:
                                decoded = syntax_data.decode(encoding, errors='strict')
                                if 'release' in decoded.lower() or 'datawindow' in decoded.lower():
                                    print(f"  → Confirmed! Syntax starts at 0x{syntax_start:x}")
                                    print(f"  → First 200 chars: {decoded[:200]}")
                                    return syntax_start, potential_length, encoding
                            except:
                                pass
                
                return None
    
    return None

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    # Analyze first few DataWindows
    dw_count = 0
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    dw_count += 1
                    print(f"\n{'='*60}")
                    print(f"Analyzing DataWindow: {entry.objectname}")
                    
                    f.seek(entry.offset)
                    data = f.read(entry.objectsize)
                    
                    result = analyze_datawindow_structure(data)
                    if result:
                        syntax_offset, syntax_length, encoding = result
                        print(f"\nSUCCESS! Found syntax:")
                        print(f"  Syntax offset: 0x{syntax_offset:x}")
                        print(f"  Syntax length: {syntax_length}")
                        print(f"  Encoding: {encoding}")
                    else:
                        print("\nFailed to find syntax in this DataWindow")
                    
                    if dw_count >= 3:
                        break
            if dw_count >= 3:
                break