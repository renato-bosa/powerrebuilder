#!/usr/bin/env python3
"""Test DataWindow extraction to understand the format."""

from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE
from extract.pbd_core.datawindow import detect_datawindow_blob, extract_datawindow_metadata
import logging

logging.basicConfig(level=logging.DEBUG)

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    print("Analyzing DataWindow objects in PBD:")
    print("=" * 60)
    
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    print(f"\nDataWindow: {entry.objectname}")
                    print(f"  Offset: {entry.offset}")
                    print(f"  Size: {entry.objectsize}")
                    
                    # Read the raw data
                    f.seek(entry.offset)
                    raw_data = f.read(min(entry.objectsize, 1000))  # First 1KB
                    
                    # Show hex dump of first 200 bytes
                    print("  First 200 bytes (hex):")
                    hex_dump = raw_data[:200].hex()
                    for i in range(0, len(hex_dump), 64):
                        print(f"    {hex_dump[i:i+64]}")
                    
                    # Try to detect if it's a DataWindow
                    f.seek(entry.offset)
                    full_data = f.read(entry.objectsize)
                    is_dw = detect_datawindow_blob(full_data)
                    print(f"  Detected as DataWindow: {is_dw}")
                    
                    if is_dw:
                        metadata = extract_datawindow_metadata(full_data)
                        print(f"  Format: {metadata['format']}")
                        print(f"  Estimated name: {metadata['estimated_name']}")
                        print(f"  Preview: {metadata['summary_preview'][:100]}...")
                    
                    # Look for text patterns
                    print("  Text pattern search:")
                    for pattern in [b'release ', b'datawindow(', b'table(', b'column=', b'HA$PBExportHeader$']:
                        pos = full_data.find(pattern)
                        if pos >= 0:
                            print(f"    Found '{pattern.decode('ascii', errors='ignore')}' at offset {pos}")
                            # Show context around pattern
                            context_start = max(0, pos - 20)
                            context_end = min(len(full_data), pos + 100)
                            context = full_data[context_start:context_end]
                            # Try to decode as text
                            for encoding in ['utf-8', 'utf-16le', 'latin-1']:
                                try:
                                    text = context.decode(encoding)
                                    print(f"      Context ({encoding}): {repr(text[:80])}")
                                    break
                                except:
                                    pass
                    
                    print("-" * 60)