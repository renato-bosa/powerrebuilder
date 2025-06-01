#!/usr/bin/env python3
"""Test PBD extraction to debug the issue."""

import logging
from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, 'rb') as f:
    # Extract header
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    print(f"Header: Unicode={header.is_unicode}, First NOD={header.first_nod_offset}")
    
    # Extract nodes
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    print(f"\nTotal nodes: {len(nodes)}")
    
    total_entries = 0
    for i, node in enumerate(nodes):
        entries = len(node.entry_defs) if node and hasattr(node, 'entry_defs') else 0
        total_entries += entries
        print(f"Node {i}: {entries} entries")
        
    print(f"\nTotal entries: {total_entries}")