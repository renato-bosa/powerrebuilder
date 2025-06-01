#!/usr/bin/env python3
"""Analyze DataWindow hex patterns more deeply."""

from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    # Find first DataWindow
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    print(f"Analyzing: {entry.objectname}")
                    
                    # Read the full data
                    f.seek(entry.offset)
                    data = f.read(entry.objectsize)
                    
                    # Look for the DAT* header
                    if data.startswith(b'DAT*'):
                        print("Found DAT* header")
                        
                        # Parse header (first 512 bytes typically)
                        header_data = data[:512]
                        print("\nHeader analysis:")
                        print(f"  Magic: {header_data[:4]}")
                        print(f"  Next 4 bytes: {header_data[4:8].hex()}")
                        
                        # Look for PDW1000 or similar markers
                        pdw_pos = header_data.find(b'PDW')
                        if pdw_pos >= 0:
                            print(f"  Found PDW at offset {pdw_pos}: {header_data[pdw_pos:pdw_pos+20]}")
                        
                        # Look for the actual DataWindow syntax after header
                        # It might be compressed or encoded
                        print("\nSearching for DataWindow syntax...")
                        
                        # Common DataWindow syntax patterns (in various encodings)
                        patterns = [
                            b'release',  # ASCII
                            b'r\x00e\x00l\x00e\x00a\x00s\x00e\x00',  # UTF-16LE
                            b'\x00r\x00e\x00l\x00e\x00a\x00s\x00e',  # UTF-16BE
                            b'datawindow',
                            b'd\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w\x00',
                            b'table(',
                            b't\x00a\x00b\x00l\x00e\x00(\x00',
                        ]
                        
                        for pattern in patterns:
                            pos = data.find(pattern)
                            if pos >= 0:
                                print(f"  Found pattern at offset {pos}: {pattern[:20]}")
                                # Show surrounding context
                                start = max(0, pos - 50)
                                end = min(len(data), pos + 200)
                                context = data[start:end]
                                print(f"  Context (hex): {context.hex()[:200]}...")
                                
                                # Try to decode from this position
                                syntax_data = data[pos:]
                                for encoding in ['utf-8', 'utf-16le', 'utf-16be', 'latin-1']:
                                    try:
                                        text = syntax_data[:500].decode(encoding, errors='ignore')
                                        # Check if it looks like DataWindow syntax
                                        if 'release' in text or 'datawindow' in text or 'table' in text:
                                            print(f"  Decoded as {encoding}:")
                                            print(f"    {repr(text[:200])}")
                                            break
                                    except:
                                        pass
                        
                        # Also check for compressed data signatures
                        if b'\x78\x9c' in data:  # zlib compression
                            print("\n  Found possible zlib compressed data")
                        if b'\x1f\x8b' in data:  # gzip compression
                            print("\n  Found possible gzip compressed data")
                        
                        # Check specific offsets based on the header structure
                        print("\nChecking specific offsets based on header...")
                        # The 0xf601 at offset 10 might be a size or offset
                        possible_offset = int.from_bytes(header_data[10:12], 'little')
                        print(f"  Possible data offset from header: 0x{possible_offset:x} ({possible_offset})")
                        
                        if possible_offset < len(data):
                            print(f"  Data at that offset: {data[possible_offset:possible_offset+50].hex()}")
                            
                            # Try to find DataWindow syntax from there
                            search_data = data[possible_offset:]
                            for pattern in [b'release', b'datawindow', b'table']:
                                pos = search_data.find(pattern)
                                if pos >= 0 and pos < 1000:  # Within reasonable distance
                                    print(f"    Found '{pattern.decode()}' at relative offset {pos}")
                    
                    # Only analyze first DataWindow for now
                    break
            else:
                continue
            break