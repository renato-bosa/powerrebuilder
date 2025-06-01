#!/usr/bin/env python3
"""Look deeper into DataWindow structure."""

from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE
import struct

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

def analyze_dat_structure(data):
    """Analyze DAT* structure in detail."""
    print("DAT* Structure Analysis:")
    print(f"  Total size: {len(data)} bytes")
    
    # Parse potential header fields
    if len(data) < 100:
        print("  Data too short")
        return
        
    # Common structure seems to be:
    # 0x00: 'DAT*' (4 bytes)
    # 0x04: Unknown (4 bytes) 
    # 0x08: Unknown (2 bytes)
    # 0x0A: Possible offset/size (2 bytes) - we saw 0xf601
    # 0x0C: 'PDW1000\0' (8 bytes)
    # ... more fields
    
    magic = data[0:4]
    field1 = struct.unpack('<I', data[4:8])[0]
    field2 = struct.unpack('<H', data[8:10])[0] 
    field3 = struct.unpack('<H', data[10:12])[0]
    
    print(f"  Magic: {magic}")
    print(f"  Field1 (offset 0x04): 0x{field1:08x} ({field1})")
    print(f"  Field2 (offset 0x08): 0x{field2:04x} ({field2})")
    print(f"  Field3 (offset 0x0A): 0x{field3:04x} ({field3})")
    
    # Look for PDW marker
    pdw_offset = data.find(b'PDW')
    if pdw_offset >= 0:
        print(f"  PDW marker at offset: 0x{pdw_offset:x}")
        pdw_version = data[pdw_offset:pdw_offset+8]
        print(f"  PDW version: {pdw_version}")
    
    # Look for any text after a certain offset
    # The 0xf601 value (502 decimal) might indicate where data starts
    if field3 < len(data):
        print(f"\nChecking data at offset 0x{field3:x}:")
        check_data = data[field3:field3+200]
        print(f"  Hex: {check_data[:50].hex()}")
        
        # Try to find readable text
        for i in range(0, min(1000, len(data) - field3), 1):
            chunk = data[field3 + i:field3 + i + 100]
            # Check for common DataWindow keywords
            for keyword in [b'release', b'datawindow', b'table', b'column', b'retrieve']:
                if keyword in chunk.lower():
                    print(f"  Found '{keyword.decode()}' at relative offset {i}")
                    print(f"    Context: {chunk[:50].hex()}")
                    break

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    # Analyze all DataWindow objects
    dw_count = 0
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    dw_count += 1
                    print(f"\n{'='*60}")
                    print(f"DataWindow #{dw_count}: {entry.objectname}")
                    print(f"Offset: 0x{entry.offset:x}, Size: {entry.objectsize} bytes")
                    
                    # Read the data
                    f.seek(entry.offset)
                    data = f.read(entry.objectsize)
                    
                    if data.startswith(b'DAT*'):
                        analyze_dat_structure(data)
                    else:
                        print(f"Does not start with DAT*, starts with: {data[:4].hex()}")
                    
                    # Try a different approach - look for the DataWindow source
                    # It might be stored as a separate blob or at the end
                    print("\nScanning entire object for DataWindow syntax patterns...")
                    
                    # Look for any occurrence of DataWindow syntax patterns
                    found_syntax = False
                    for offset in range(0, len(data) - 100, 1):
                        chunk = data[offset:offset+100]
                        
                        # Check various encodings of "release" which starts DW syntax
                        if (b'release' in chunk or 
                            b'r\x00e\x00l\x00e\x00a\x00s\x00e' in chunk or
                            b'\x00r\x00e\x00l\x00e\x00a\x00s\x00e' in chunk):
                            
                            print(f"  Found potential syntax at offset 0x{offset:x}")
                            # Extract and try to decode
                            syntax_data = data[offset:]
                            
                            # Find the end (usually null bytes or specific terminator)
                            end_pos = syntax_data.find(b'\x00\x00\x00\x00')
                            if end_pos > 0:
                                syntax_data = syntax_data[:end_pos]
                            
                            for encoding in ['utf-8', 'utf-16le', 'utf-16be', 'latin-1']:
                                try:
                                    text = syntax_data.decode(encoding, errors='ignore')
                                    if 'release' in text and ('datawindow' in text or 'table' in text):
                                        print(f"  Successfully decoded as {encoding}")
                                        print(f"  First 200 chars: {text[:200]}")
                                        found_syntax = True
                                        break
                                except:
                                    pass
                            
                            if found_syntax:
                                break
                    
                    if not found_syntax:
                        print("  No DataWindow syntax found in object")
                    
                    if dw_count >= 3:  # Just analyze first 3
                        break
            else:
                continue
            break