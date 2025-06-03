#!/usr/bin/env python3
"""Final debug script to understand P-code extraction issue."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def extract_entries_manual(pbd_path: str):
    """Extract entries from PBD using the actual extraction logic."""
    print(f"Extracting from: {pbd_path}")
    print("=" * 80)
    
    # Import here to avoid the type annotation issue
    try:
        from extract.pbd_core.header import extract_pbl_header
        from extract.pbd_core.node import extract_nods
        from extract.pbd_core.entry import extract_entry_def, extract_entry_def_unicode
        from extract.pbd_io.utils import retrieve_bytes_from_file
        
        # Read the file
        with open(pbd_path, 'rb') as f:
            data = f.read()
        
        # Parse header
        header = extract_pbl_header(data)
        if not header:
            print("Failed to parse header")
            return
            
        print(f"Header info:")
        print(f"  Version: {header.header_version}")
        print(f"  Is Unicode: {header.is_unicode}")
        print(f"  First NOD offset: {header.first_nod_offset}")
        print(f"  Block size: {getattr(header, 'effective_block_size', 'N/A')}")
        
        # Extract NODs
        nodes = extract_nods(pbd_path, header.is_unicode, header.first_nod_offset, 
                           getattr(header, 'effective_block_size', 0x200))
        
        print(f"\nFound {len(nodes)} NOD(s)")
        
        total_entries = 0
        source_files = []
        
        for i, node in enumerate(nodes):
            if not node:
                continue
                
            print(f"\nNOD {i}: {node.numberofentries} entries")
            
            # Extract entries from this NOD
            for j in range(node.numberofentries):
                entry_offset = node.entriesoffset[j]
                
                # Read entry data
                entry_data = retrieve_bytes_from_file(pbd_path, entry_offset, 200)
                
                # Parse entry based on Unicode flag
                if header.is_unicode:
                    entry = extract_entry_def_unicode(entry_data)
                else:
                    entry = extract_entry_def(entry_data)
                
                if entry:
                    total_entries += 1
                    print(f"  Entry {j+1}: {entry.objectname}")
                    print(f"    Version: {entry.version}")
                    print(f"    Size: {entry.objectsize}")
                    print(f"    Comment len: {entry.commentlen}")
                    
                    # Check if it's a source file
                    ext = Path(entry.objectname).suffix.lower()
                    if ext in {'.sru', '.srw', '.srd', '.srm', '.sra', '.srq', '.srs', '.srf', '.srj'}:
                        source_files.append(entry)
                        
                        # Check P-code detection logic
                        version_lower = entry.version.lower()
                        has_function = "function" in version_lower
                        has_event = "event" in version_lower
                        is_srf_srj = ext in {'.srf', '.srj'}
                        
                        would_be_pcode = (has_function or has_event) or is_srf_srj
                        
                        print(f"    ⚠️  Source file!")
                        print(f"       Version contains 'function': {has_function}")
                        print(f"       Version contains 'event': {has_event}")
                        print(f"       Is .srf/.srj: {is_srf_srj}")
                        print(f"       Would create .fun file: {would_be_pcode}")
        
        print(f"\n\nSummary:")
        print(f"  Total entries: {total_entries}")
        print(f"  Source files: {len(source_files)}")
        
        if source_files:
            print("\nSource files that should have P-code:")
            for entry in source_files:
                print(f"  - {entry.objectname} (version: '{entry.version}')")
                
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Try multiple PBD files
    test_pbds = [
        "input/pbd_files/pfcmain.pbd",  # PFC files often have source code
        "input/pbd_files/dcm_email.pbd",
        "tests/fixtures/pbd_files/dcm_email.pbd"
    ]
    
    for test_pbd in test_pbds:
        if os.path.exists(test_pbd):
            extract_entries_manual(test_pbd)
            break
    else:
        print("No test PBD files found")