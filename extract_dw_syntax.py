#!/usr/bin/env python3
"""Extract DataWindow syntax based on discovered format."""

import struct
from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE

def extract_datawindow_syntax(data):
    """Extract DataWindow syntax from binary data."""
    # Look for PBSELECT marker
    pbselect_pos = data.find(b'P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00')
    if pbselect_pos < 0:
        # Try to find other markers
        for marker in [b'r\x00e\x00l\x00e\x00a\x00s\x00e\x00', 
                       b'd\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w\x00']:
            pos = data.find(marker)
            if pos >= 0:
                pbselect_pos = pos
                break
    
    if pbselect_pos < 0:
        return None
    
    print(f"Found syntax marker at offset 0x{pbselect_pos:x}")
    
    # Look backwards for a length field
    # The length field appears to be just before the syntax
    best_length = None
    best_offset = None
    
    for offset in range(max(0, pbselect_pos - 100), pbselect_pos, 4):
        if offset + 4 <= len(data):
            potential_length = struct.unpack('<I', data[offset:offset+4])[0]
            
            # Check if this length makes sense
            if offset + 4 + potential_length > pbselect_pos and offset + 4 + potential_length <= len(data):
                # This could be our length field
                syntax_start = offset + 4
                syntax_end = syntax_start + potential_length
                
                # Verify by checking if we can decode the entire range
                try:
                    test_data = data[syntax_start:syntax_end]
                    decoded = test_data.decode('utf-16-le', errors='strict')
                    
                    # Check if it looks like complete DataWindow syntax
                    if decoded.startswith(('PBSELECT', 'release', 'datawindow')):
                        # Check for reasonable ending
                        if decoded.strip().endswith(')') or decoded.count('(') == decoded.count(')'):
                            best_length = potential_length
                            best_offset = offset
                            print(f"Found length field at offset 0x{offset:x}: {potential_length} bytes")
                            break
                except:
                    pass
    
    if best_length and best_offset:
        syntax_start = best_offset + 4
        syntax_data = data[syntax_start:syntax_start + best_length]
        try:
            syntax_text = syntax_data.decode('utf-16-le', errors='ignore')
            return syntax_text.strip('\x00')
        except:
            pass
    
    # Fallback: just extract from the marker to the end or next null section
    syntax_data = data[pbselect_pos:]
    null_pos = syntax_data.find(b'\x00\x00\x00\x00')
    if null_pos > 0:
        syntax_data = syntax_data[:null_pos]
    
    try:
        return syntax_data.decode('utf-16-le', errors='ignore').strip('\x00')
    except:
        return None

def process_datawindow(pbd_path, entry, f):
    """Process a single DataWindow entry."""
    print(f"\nProcessing: {entry.objectname}")
    print("-" * 50)
    
    f.seek(entry.offset)
    data = f.read(entry.objectsize)
    
    syntax = extract_datawindow_syntax(data)
    if syntax:
        print(f"Successfully extracted {len(syntax)} characters of syntax")
        return syntax
    else:
        print("Failed to extract syntax")
        return None

# Test on all DataWindows
pbd_path = Path("input/pbd_files/dcm_accounting.pbd")
output_dir = Path("output/extracted_datawindows")
output_dir.mkdir(parents=True, exist_ok=True)

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    dw_count = 0
    success_count = 0
    
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    dw_count += 1
                    syntax = process_datawindow(pbd_path, entry, f)
                    
                    if syntax:
                        success_count += 1
                        # Save the syntax
                        output_file = output_dir / f"{entry.objectname}.sql"
                        with open(output_file, 'w', encoding='utf-8') as out:
                            out.write(f"-- DataWindow: {entry.objectname}\n")
                            out.write(f"-- Extracted from: {pbd_path.name}\n")
                            out.write("-" * 60 + "\n\n")
                            out.write(syntax)
                            out.write("\n")
                        
                        print(f"Saved to: {output_file}")
                        
                        # Show preview
                        print("\nSyntax preview:")
                        print(syntax[:300] + "..." if len(syntax) > 300 else syntax)
    
    print(f"\n{'='*60}")
    print(f"Summary: Successfully extracted {success_count}/{dw_count} DataWindows")