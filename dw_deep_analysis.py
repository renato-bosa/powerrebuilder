#!/usr/bin/env python3
"""Deep analysis of DataWindow format looking at the entire structure."""

import struct
from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE

def find_utf16_text(data, min_length=20):
    """Find UTF-16 encoded text in binary data."""
    results = []
    
    # Try UTF-16 LE
    for i in range(0, len(data) - min_length * 2, 2):
        try:
            # Check if this could be the start of UTF-16 text
            chunk = data[i:i + min_length * 2]
            decoded = chunk.decode('utf-16-le', errors='strict')
            
            # Check if it contains printable characters
            if all(32 <= ord(c) <= 126 or c in '\r\n\t' for c in decoded):
                # Extend to find the full string
                j = i + min_length * 2
                while j < len(data) - 2:
                    next_chars = data[j:j+2]
                    if next_chars == b'\x00\x00':  # Null terminator
                        break
                    try:
                        next_char = next_chars.decode('utf-16-le', errors='strict')
                        if 32 <= ord(next_char) <= 126 or next_char in '\r\n\t':
                            j += 2
                        else:
                            break
                    except:
                        break
                
                full_string = data[i:j].decode('utf-16-le', errors='ignore')
                if len(full_string) >= min_length:
                    results.append((i, full_string, 'utf-16-le'))
        except:
            pass
    
    return results

def analyze_dw_in_detail(data):
    """Detailed analysis of DataWindow structure."""
    print(f"File size: {len(data)} bytes")
    
    # Parse the DAT* header
    if data[:4] == b'DAT*':
        print("\nDAT* Header found")
        print(f"  Next 4 bytes: 0x{data[4:8].hex()}")
        print(f"  Bytes 8-12: 0x{data[8:12].hex()}")
        
        # The 0xf601 we saw earlier
        field_at_10 = struct.unpack('<H', data[10:12])[0]
        print(f"  Field at offset 10: 0x{field_at_10:04x} ({field_at_10})")
    
    # Look for PDW marker
    pdw_pos = data.find(b'PDW')
    if pdw_pos >= 0:
        print(f"\nPDW marker at offset 0x{pdw_pos:x}")
        print(f"  Version string: {data[pdw_pos:pdw_pos+8]}")
    
    # After the header (502 bytes based on field at offset 10)
    header_size = 502  # 0xf601 seems to be a version/type indicator, not size
    
    # Try different header sizes
    for test_header_size in [502, 512, 256, 128, 64, 32]:
        if test_header_size < len(data):
            print(f"\nChecking after {test_header_size} byte header:")
            after_header = data[test_header_size:test_header_size+100]
            print(f"  Hex: {after_header[:50].hex()}")
            
            # Check if there's a length field here
            if test_header_size + 4 <= len(data):
                potential_length = struct.unpack('<I', data[test_header_size:test_header_size+4])[0]
                if 100 < potential_length < len(data) - test_header_size:
                    print(f"  Potential length at offset {test_header_size}: {potential_length}")
                    
                    # Check what's after this length field
                    if test_header_size + 4 + potential_length <= len(data):
                        test_data = data[test_header_size + 4:test_header_size + 4 + 100]
                        for encoding in ['utf-16-le', 'utf-16-be']:
                            try:
                                decoded = test_data.decode(encoding, errors='ignore')
                                if any(kw in decoded.lower() for kw in ['release', 'datawindow', 'table', 'select']):
                                    print(f"    → Found syntax! Encoding: {encoding}")
                                    print(f"    → Preview: {decoded[:100]}")
                                    return test_header_size, potential_length, encoding
                            except:
                                pass
    
    # Search for any UTF-16 text
    print("\nSearching for UTF-16 text blocks...")
    texts = find_utf16_text(data, min_length=30)
    for offset, text, encoding in texts[:5]:  # First 5 results
        if any(kw in text.lower() for kw in ['release', 'datawindow', 'table', 'select', 'column']):
            print(f"\nFound DataWindow-like text at offset 0x{offset:x}:")
            print(f"  Encoding: {encoding}")
            print(f"  Text: {text[:200]}...")
            
            # Look for length field before this
            for i in range(max(0, offset - 100), offset, 4):
                if i + 4 <= len(data):
                    length = struct.unpack('<I', data[i:i+4])[0]
                    if i + 4 + length >= offset and i + 4 + length <= len(data):
                        print(f"  Possible length field at 0x{i:x}: {length}")
    
    return None

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    # Just analyze first DataWindow in detail
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    print(f"Analyzing: {entry.objectname}")
                    print("="*60)
                    
                    f.seek(entry.offset)
                    data = f.read(entry.objectsize)
                    
                    result = analyze_dw_in_detail(data)
                    if result:
                        header_size, syntax_length, encoding = result
                        print(f"\nSUCCESS!")
                        print(f"  Header size: {header_size}")
                        print(f"  Syntax length: {syntax_length}")
                        print(f"  Encoding: {encoding}")
                        
                        # Extract and show the full syntax
                        syntax_data = data[header_size + 4:header_size + 4 + syntax_length]
                        syntax_text = syntax_data.decode(encoding, errors='ignore')
                        print(f"\nFull syntax preview (first 500 chars):")
                        print(syntax_text[:500])
                    
                    # Just analyze one for now
                    break
            break