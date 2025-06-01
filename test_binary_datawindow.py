#!/usr/bin/env python3
"""Test if DataWindows are in binary compiled format."""

from pathlib import Path
from extract.pbd_core.header import extract_pbl_header  
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE
import struct

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

def analyze_binary_dw(data):
    """Analyze binary DataWindow format."""
    # The format appears to be:
    # DAT* header followed by compiled DataWindow data
    # This is likely the compiled binary representation, not source
    
    print(f"\nBinary DataWindow Analysis:")
    print(f"  Size: {len(data)} bytes")
    
    # Skip the DAT* header (appears to be 502 bytes based on field2)
    header_size = 502
    if len(data) > header_size:
        # The actual DataWindow data starts after the header
        dw_data = data[header_size:]
        print(f"  Data after header: {len(dw_data)} bytes")
        print(f"  First 100 bytes: {dw_data[:100].hex()}")
        
        # Look for any structure markers
        # PowerBuilder compiled objects often have internal structure markers
        markers = [b'HDR', b'TBL', b'COL', b'DAT', b'ENT', b'NOD', b'FRM']
        for marker in markers:
            pos = dw_data.find(marker)
            if pos >= 0:
                print(f"  Found marker '{marker.decode()}' at offset {pos}")
    
    return None

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    print("Binary DataWindow Format Test")
    print("="*60)
    
    # Test on first DataWindow
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    print(f"\nTesting: {entry.objectname}")
                    
                    f.seek(entry.offset)
                    data = f.read(entry.objectsize)
                    
                    if data.startswith(b'DAT*'):
                        # This is a binary compiled DataWindow
                        print("This is a binary/compiled DataWindow (not source code)")
                        analyze_binary_dw(data)
                        
                        # The decompiler's _extract_datawindow method is looking for
                        # text-based source, but these are compiled binary DWs
                        print("\nConclusion: These DataWindows are stored in compiled binary format.")
                        print("The decompiler's current approach of looking for text patterns")
                        print("won't work for these files. They would need specialized binary")
                        print("DataWindow decompilation, which is beyond simple text extraction.")
                    
                    break
            break