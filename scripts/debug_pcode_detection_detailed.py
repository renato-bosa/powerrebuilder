#!/usr/bin/env python3
"""Detailed debug of P-code detection logic to understand the issue."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Define source extensions directly to avoid import issues
SOURCE_EXTENSIONS = ('.sru', '.srw', '.srd', '.srm', '.sra', '.srq', '.srs', '.srf', '.srj')

def analyze_pbd_for_pcode(pbd_path: str):
    """Analyze a PBD file to understand P-code detection."""
    print(f"Analyzing: {pbd_path}")
    print("=" * 80)
    
    # Read the file
    with open(pbd_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Check if it's Unicode
    if data.startswith(b'HDR*P\x00o\x00w\x00e\x00r\x00'):
        print("This is a Unicode PBD file")
        is_unicode = True
    elif data.startswith(b'HDR*Power'):
        print("This is an ANSI PBD file")
        is_unicode = False
    else:
        print("Unknown PBD format")
        return
    
    # Find all ENT* entries
    entries = []
    offset = 0
    
    while offset < len(data) - 4:
        if data[offset:offset+4] == b'ENT*':
            entries.append(offset)
        offset += 1
    
    print(f"\nFound {len(entries)} ENT* entries")
    
    # Analyze each entry
    for i, entry_offset in enumerate(entries):
        print(f"\n--- Entry {i+1} at offset {entry_offset} ---")
        
        # Read entry header
        entry_data = data[entry_offset:entry_offset+100]  # Read enough for header
        
        # Extract version (8 bytes after ENT* for Unicode)
        if is_unicode:
            version_bytes = entry_data[4:12]  # 8 bytes for Unicode
            # For Unicode, version appears to be in UTF-16LE format
            try:
                version = version_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
            except:
                version = version_bytes.hex()
        else:
            version_bytes = entry_data[4:8]  # 4 bytes for ANSI
            version = version_bytes.decode('ascii', errors='ignore').rstrip('\x00')
        
        print(f"Version bytes (hex): {version_bytes.hex()}")
        print(f"Version string: '{version}'")
        
        # Extract object name
        # For Unicode files, we need to account for the larger header
        if is_unicode:
            # Unicode ENT* structure (48 bytes fixed header):
            # 0-4: "ENT*"
            # 4-12: Version (8 bytes)
            # 12-16: Offset (4 bytes)
            # 16-20: Object size (4 bytes)
            # 20-24: Mod time (4 bytes)
            # 24-28: Comment length (4 bytes)
            # 28-32: Object name length (4 bytes)
            # 32-48: Reserved/padding
            # 48+: Object name (Unicode)
            
            if len(entry_data) > 48:
                name_len_bytes = entry_data[28:32]
                name_len = int.from_bytes(name_len_bytes, 'little')
                print(f"Name length: {name_len}")
                
                name_start = 48
                name_end = name_start + name_len
                if name_end <= len(entry_data):
                    name_bytes = entry_data[name_start:name_end]
                    try:
                        obj_name = name_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
                    except:
                        obj_name = name_bytes.hex()
                else:
                    # Need to read more data
                    more_data = data[entry_offset:entry_offset + name_end + 10]
                    name_bytes = more_data[name_start:name_end]
                    try:
                        obj_name = name_bytes.decode('utf-16le', errors='ignore').rstrip('\x00')
                    except:
                        obj_name = "<decode error>"
            else:
                obj_name = "<too short>"
        else:
            # ANSI format (24 bytes fixed header)
            name_len_bytes = entry_data[22:24]
            name_len = int.from_bytes(name_len_bytes, 'little')
            name_start = 24
            name_end = name_start + name_len
            if name_end <= len(entry_data):
                obj_name = entry_data[name_start:name_end].decode('ascii', errors='ignore')
            else:
                obj_name = "<truncated>"
        
        print(f"Object name: '{obj_name}'")
        
        # Check P-code detection logic
        if isinstance(obj_name, str):
            ends_with_source = obj_name.lower().endswith(SOURCE_EXTENSIONS)
            is_srf_srj = obj_name.lower().endswith(('.srf', '.srj'))
            
            version_lower = version.lower() if isinstance(version, str) else ''
            has_function = 'function' in version_lower
            has_event = 'event' in version_lower
            
            # This is the exact logic from core.py
            is_potential_pcode = (ends_with_source and (has_function or has_event)) or is_srf_srj
            
            print(f"\nP-code detection analysis:")
            print(f"  - Ends with source extension: {ends_with_source}")
            print(f"  - Is .srf/.srj: {is_srf_srj}")
            print(f"  - Version contains 'function': {has_function}")
            print(f"  - Version contains 'event': {has_event}")
            print(f"  - Would be detected as P-code: {is_potential_pcode}")
            
            if ends_with_source and not is_potential_pcode:
                print(f"  ⚠️  This is a source file but NOT detected as P-code!")
                print(f"     Reason: Version '{version}' doesn't contain 'function' or 'event'")

if __name__ == "__main__":
    test_pbd = "tests/fixtures/pbd_files/dcm_email.pbd"
    
    if not os.path.exists(test_pbd):
        print(f"Error: Test PBD file not found: {test_pbd}")
    else:
        analyze_pbd_for_pcode(test_pbd)