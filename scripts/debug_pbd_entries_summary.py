#!/usr/bin/env python3
"""Quick summary of all entries in a PBD file."""

import os
import sys
from pathlib import Path

def summarize_pbd(pbd_path: str):
    """Show a summary of all entries in the PBD."""
    print(f"PBD Summary: {pbd_path}")
    print("=" * 80)
    
    with open(pbd_path, 'rb') as f:
        data = f.read()
    
    # Check if Unicode
    is_unicode = data.startswith(b'HDR*P\x00o\x00w\x00e\x00r\x00')
    print(f"Format: {'Unicode' if is_unicode else 'ANSI'}")
    print(f"File size: {len(data)} bytes\n")
    
    # Find all entries
    entries = []
    offset = 0
    
    # From the hexdump, we know entries are at specific offsets
    known_offsets = [0x620, 0x668, 0x6B0, 0x6F0]  # From hexdump
    
    for entry_offset in known_offsets:
        if entry_offset + 4 <= len(data) and data[entry_offset:entry_offset+4] == b'ENT*':
            # For this Unicode PBD, the structure is:
            # ENT* (4) + version (8) + offset (4) + size (4) + time (4) + commentlen (2) + namelen (2) + name
            if entry_offset + 24 < len(data):
                name_len_bytes = data[entry_offset+22:entry_offset+24]
                name_len = int.from_bytes(name_len_bytes, 'little') * 2  # Unicode is 2 bytes per char
                name_start = entry_offset + 24
                name_end = name_start + name_len
                
                if name_end <= len(data):
                    name_bytes = data[name_start:name_end]
                    try:
                        obj_name = name_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
                        entries.append(obj_name)
                        print(f"  Found at 0x{entry_offset:X}: {obj_name}")
                    except Exception as e:
                        print(f"  Error at 0x{entry_offset:X}: {e}")
    
    print(f"Found {len(entries)} entries:")
    for i, name in enumerate(entries, 1):
        ext = Path(name).suffix.lower()
        print(f"  {i}. {name} ({ext})")
    
    # Summary by extension
    print("\nSummary by extension:")
    ext_counts = {}
    for name in entries:
        ext = Path(name).suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    
    for ext, count in sorted(ext_counts.items()):
        print(f"  {ext}: {count}")
    
    # Check for source files
    source_exts = {'.sru', '.srw', '.srd', '.srm', '.sra', '.srq', '.srs', '.srf', '.srj'}
    source_files = [name for name in entries if Path(name).suffix.lower() in source_exts]
    
    print(f"\nSource files that would need P-code: {len(source_files)}")
    if source_files:
        for name in source_files:
            print(f"  - {name}")

if __name__ == "__main__":
    # Try multiple PBD files
    test_pbds = [
        "tests/fixtures/pbd_files/dcm_email.pbd",
        "input/pbd_files/dcm_email.pbd",
        "input/pbd_files/pfcmain.pbd"  # PFC files often have source code
    ]
    
    for test_pbd in test_pbds:
        if os.path.exists(test_pbd):
            summarize_pbd(test_pbd)
            print("\n" + "="*80 + "\n")
            break
    else:
        print("No test PBD files found")