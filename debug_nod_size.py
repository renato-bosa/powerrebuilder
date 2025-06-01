#!/usr/bin/env python3
"""Debug NOD size calculation."""

import struct
from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_io.utils import BLOCK_SIZE, retrieve_bytes_from_file

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, 'rb') as f:
    # Extract header
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    
    # Get the NOD header
    node_offset = header.first_nod_offset
    nod_header = retrieve_bytes_from_file(f, node_offset, 64, BLOCK_SIZE)
    
    print(f"NOD offset: {node_offset}")
    print(f"NOD header (first 64 bytes): {nod_header.hex()}")
    
    # Parse NOD header
    if nod_header[:4] == b'NOD*':
        print("\nNOD* signature found")
        
        # For Unicode NOD:
        # 4 bytes: 'NOD*'
        # 4 bytes: next NOD offset
        # 4 bytes: unknown1
        # 4 bytes: unknown2  
        # 2 bytes: number of entries
        # 2 bytes: unknown3
        # 4 bytes: offsetleft
        # 4 bytes: offsetright
        # 4 bytes: spaceleft
        
        next_nod = struct.unpack('<I', nod_header[4:8])[0]
        num_entries = struct.unpack('<H', nod_header[16:18])[0]
        
        print(f"Next NOD offset: {next_nod}")
        print(f"Number of entries: {num_entries}")
        
        # Calculate expected size
        node_header_size = 32  # NOD header
        estimated_entry_size = 100  # Rough estimate
        estimated_total = node_header_size + (num_entries * estimated_entry_size)
        
        print(f"\nEstimated total size: {estimated_total}")
        print(f"Blocks needed: {(estimated_total + BLOCK_SIZE - 1) // BLOCK_SIZE}")
        
        # Check actual data
        print(f"\nChecking for ENT* signatures...")
        full_data = retrieve_bytes_from_file(f, node_offset, BLOCK_SIZE * 8, BLOCK_SIZE)
        
        ent_count = 0
        for i in range(0, len(full_data) - 4, 2):
            if full_data[i:i+4] == b'ENT*':
                print(f"  ENT* at offset {i}")
                ent_count += 1
                if ent_count >= 35:  # Stop after finding enough
                    break