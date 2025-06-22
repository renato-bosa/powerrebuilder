#!/usr/bin/env python3
"""Analyze PDW file structure to understand what can be extracted beyond SQL."""

import struct
import sys
import logging


logger = logging.getLogger(__name__)

def analyze_pdw(file_path) -> None:


    

    """Analyze PDW file structure."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"Analyzing: {file_path}")
    print(f"File size: {len(data)} bytes")
    print("=" * 80)
    
    # Header analysis
    if len(data) < 0x20:
        print("File too small to be a valid PDW")
        return
    
    # PDW signature
    signature = data[:8]
    print(f"Signature: {signature} ({signature.decode('ascii', errors='ignore')})")
    
    # Parse header fields (based on hex dump analysis)
    print("\nHeader fields:")
    print(f"  0x08-0x0B: {struct.unpack('<I', data[0x08:0x0C])[0]:08x}")
    print(f"  0x0C-0x0F: {struct.unpack('<I', data[0x0C:0x10])[0]:08x}")
    print(f"  0x10-0x13: {data[0x10:0x14].hex()} ('{data[0x10:0x14].decode('ascii', errors='ignore')}')")
    
    # Look for structure patterns
    print("\nStructure analysis:")
    
    # Find integer patterns (offsets, counts, etc.)
    offset = 0x30
    print(f"\nIntegers at offset 0x30:")
    for i in range(10):
        if offset + 4 <= len(data):
            val = struct.unpack('<I', data[offset:offset+4])[0]
            if val > 0 and val < 0x10000:  # Reasonable range
                print(f"  0x{offset:04x}: {val} (0x{val:08x})")
        offset += 4
    
    # Look for string tables
    print("\nSearching for string patterns...")
    
    # Method 1: Look for UTF-16 LE strings
    utf16_strings = []
    i = 0
    while i < len(data) - 4:
        # Look for pattern: length (4 bytes) followed by UTF-16 string
        if i + 4 <= len(data):
            str_len = struct.unpack('<I', data[i:i+4])[0]
            if 2 <= str_len <= 100 and i + 4 + str_len * 2 <= len(data):
                # Check if it looks like UTF-16
                str_data = data[i+4:i+4+str_len*2]
                try:
                    decoded = str_data.decode('utf-16-le', errors='ignore')
                    # Check if it's mostly printable
                    if sum(1 for c in decoded if c.isprintable()) > len(decoded) * 0.8:
                        utf16_strings.append((i, decoded))
                        i += 4 + str_len * 2
                        continue
                except Exception as e:
                    logger.debug("Exception caught: %s", e)
        i += 1
    
    if utf16_strings:
        print(f"\nFound {len(utf16_strings)} UTF-16 strings:")
        for offset, s in utf16_strings[:
            20]:  # First 20
            print(f"  0x{offset:04x}: '{s}'")
    
    # Method 2: Look for ASCII strings
    ascii_strings = []
    current_string = b""
    start_offset = 0
    
    for i, byte in enumerate(data):
        if 0x20 <= byte <= 0x7E:  # Printable ASCII
            if not current_string:
                start_offset = i
            current_string += bytes([byte])
        else:
            if len(current_string) >= 4:  # Minimum string length
                ascii_strings.append((start_offset, current_string.decode('ascii')))
            current_string = b""
    
    if ascii_strings:
        print(f"\nFound {len(ascii_strings)} ASCII strings:")
        for offset, s in ascii_strings[:
            20]:  # First 20
            print(f"  0x{offset:04x}: '{s}'")
    
    # Look for table structures
    print("\nLooking for table/array structures...")
    
    # Common pattern: count followed by array of fixed-size records
    for offset in range(0, min(0x100, len(data)), 4):
        if offset + 4 <= len(data):
            count = struct.unpack('<I', data[offset:offset+4])[0]
            if 2 <= count <= 100:  # Reasonable count
                # Check if there's a repeating pattern after this
                print(f"  Potential array at 0x{offset:04x} with count={count}")
    
    # Look for SQL patterns
    print("\nSearching for SQL patterns...")
    sql_keywords = [b'SELECT', b'FROM', b'WHERE', b'ORDER', b'GROUP', b'JOIN', b'INSERT', b'UPDATE', b'DELETE']
    
    for keyword in sql_keywords:
        # ASCII version
        idx = data.find(keyword)
        if idx >= 0:
            print(f"  Found {keyword.decode()} at 0x{idx:04x}")
            # Show context
            start = max(0, idx - 20)
            end = min(len(data), idx + 100)
            context = data[start:end].replace(b'\x00', b' ')
            print(f"    Context: {context[:80]}...")
        
        # UTF-16 LE version
        utf16_keyword = b''.join(bytes([c, 0]) for c in keyword)
        idx = data.find(utf16_keyword)
        if idx >= 0:
            print(f"  Found UTF-16 {keyword.decode()} at 0x{idx:04x}")
    
    # Look for DataWindow property patterns
    print("\nSearching for DataWindow properties...")
    dw_properties = [b'column', b'table', b'retrieve', b'update', b'key', b'primary', b'foreign',
                     b'datawindow', b'release', b'dbname', b'font', b'color', b'width', b'height']
    
    for prop in dw_properties:
        count = data.count(prop)
        if count > 0:
            print(f"  '{prop.decode()}' appears {count} times")
    
    # Hex dump of interesting regions
    print("\nInteresting regions:")
    
    # Region around 0xb20 where we saw UTF-16 strings
    if len(data) > 0xb20:
        print(f"\nRegion 0xb20-0xc80 (UTF-16 strings):")
        region = data[0xb20:0xc80]
        for i in range(0, len(region), 16):
            hex_str = region[i:i+16].hex()
            ascii_str = ''.join(chr(b) if 0x20 <= b <= 0x7E else '.' for b in region[i:i+16])
            print(f"  {0xb20+i:04x}: {hex_str[:32]:<32} {ascii_str}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: analyze_pdw_structure.py <pdw_file>")
        sys.exit(1)
    
    analyze_pdw(sys.argv[1])