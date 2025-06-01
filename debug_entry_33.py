#!/usr/bin/env python3
"""Debug entry 33 parsing issue."""

import logging
from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nod
from extract.pbd_io.utils import BLOCK_SIZE, retrieve_bytes_from_file

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, 'rb') as f:
    # Extract header
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    
    # Get the NOD data
    node_offset = header.first_nod_offset
    
    # Read raw NOD data
    node_data = retrieve_bytes_from_file(f, node_offset, BLOCK_SIZE * 4, BLOCK_SIZE)
    
    # Look at the data around offset 2546 (where entry 33 fails)
    offset = 2546
    print(f"Data at offset {offset}:")
    print(f"Hex: {node_data[offset:offset+64].hex()}")
    print(f"First 4 bytes: {node_data[offset:offset+4]}")
    
    # Check if it's ENT* signature
    if node_data[offset:offset+4] == b'ENT*':
        print("Found ENT* signature")
    else:
        print(f"No ENT* signature, got: {node_data[offset:offset+4]}")
    
    # Look at previous successful entry (entry 32)
    # Estimate where it might be
    print("\nLooking for previous entries...")
    for i in range(offset-200, offset, 4):
        if node_data[i:i+4] == b'ENT*':
            print(f"Found ENT* at offset {i}")