#!/usr/bin/env python3
"""Simplified debug script to understand P-code detection without full imports."""

import struct
import os
from pathlib import Path

# Source extensions from the core.py file
SOURCE_EXTENSIONS = ('.sru', '.srw', '.srd', '.srm', '.sra', '.srq', '.srs', '.srf', '.srj')

def read_string(data, offset, encoding='cp1252'):
    """Read a null-terminated string from data."""
    end = data.find(b'\x00', offset)
    if end == -1:
        end = len(data)
    return data[offset:end].decode(encoding, errors='replace')

def debug_pbd_entries(pbd_path: str):
    """Read PBD file and examine entries directly."""
    print(f"Debugging P-code detection in: {pbd_path}")
    print("=" * 80)
    
    with open(pbd_path, 'rb') as f:
        data = f.read()
    
    # PBD files start with HDR* or ENT*
    if not (data.startswith(b'HDR*') or data.startswith(b'ENT*')):
        print("Error: Not a valid PBD file")
        return
    
    # Create output directory
    output_dir = Path("output/debug_pcode_simple")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    debug_log = output_dir / "pcode_detection_simple.txt"
    
    with open(debug_log, 'w') as log:
        log.write(f"PBD File: {pbd_path}\n")
        log.write(f"File size: {len(data)} bytes\n")
        log.write("=" * 80 + "\n\n")
        
        # Look for ENT* blocks
        offset = 0
        entry_count = 0
        pcode_candidates = 0
        
        while offset < len(data) - 4:
            # Look for ENT* marker
            if data[offset:offset+4] == b'ENT*':
                entry_count += 1
                log.write(f"\nEntry {entry_count} at offset {offset}:\n")
                print(f"\nFound entry {entry_count} at offset {offset}")
                
                # Skip ENT* marker
                offset += 4
                
                # Read entry size (4 bytes)
                if offset + 4 <= len(data):
                    entry_size = struct.unpack('<I', data[offset:offset+4])[0]
                    log.write(f"  Entry size: {entry_size}\n")
                    offset += 4
                    
                    # Try to find object name and version
                    # This is a simplified heuristic - actual format may vary
                    entry_data = data[offset:offset+min(entry_size, 1000)]
                    
                    # Look for string patterns
                    # Object names often appear early in the entry
                    strings = []
                    i = 0
                    while i < len(entry_data) - 1:
                        if entry_data[i] >= 32 and entry_data[i] < 127:
                            # Start of printable string
                            start = i
                            while i < len(entry_data) and entry_data[i] >= 32 and entry_data[i] < 127:
                                i += 1
                            if i - start > 3:  # Min string length
                                try:
                                    s = entry_data[start:i].decode('ascii', errors='ignore')
                                    strings.append((start, s))
                                except:
                                    pass
                        i += 1
                    
                    # Look for object name patterns
                    obj_name = None
                    version = None
                    
                    for pos, s in strings:
                        # Check if it looks like a file name
                        if any(s.lower().endswith(ext) for ext in SOURCE_EXTENSIONS):
                            obj_name = s
                            log.write(f"  Possible object name: {s}\n")
                            print(f"  Found object name: {s}")
                        # Check for version strings
                        elif any(word in s.lower() for word in ['function', 'event', 'window', 'menu', 'application']):
                            version = s
                            log.write(f"  Possible version: {s}\n")
                            print(f"  Found version: {s}")
                    
                    # Check P-code detection logic
                    if obj_name:
                        ends_with_source = obj_name.lower().endswith(SOURCE_EXTENSIONS)
                        is_srf_srj = obj_name.lower().endswith((".srf", ".srj"))
                        
                        version_lower = version.lower() if version else ''
                        has_function = "function" in version_lower
                        has_event = "event" in version_lower
                        
                        is_potential_pcode = (ends_with_source and (has_function or has_event)) or is_srf_srj
                        
                        log.write(f"  P-code detection:\n")
                        log.write(f"    Ends with source ext: {ends_with_source}\n")
                        log.write(f"    Is .srf/.srj: {is_srf_srj}\n")
                        log.write(f"    Has 'function': {has_function}\n")
                        log.write(f"    Has 'event': {has_event}\n")
                        log.write(f"    Is potential P-code: {is_potential_pcode}\n")
                        
                        if is_potential_pcode:
                            pcode_candidates += 1
                    
                    # Show first few strings found
                    log.write(f"  First 10 strings found:\n")
                    for pos, s in strings[:10]:
                        log.write(f"    {pos}: {s}\n")
                    
                    # Move to next entry
                    offset += entry_size
                else:
                    offset += 1
            else:
                offset += 1
        
        summary = f"\n\nSummary:\n"
        summary += f"Total entries found: {entry_count}\n"
        summary += f"Potential P-code entries: {pcode_candidates}\n"
        
        log.write(summary)
        print("\n" + "=" * 80)
        print(summary)
        print(f"\nDebug log saved to: {debug_log}")

if __name__ == "__main__":
    test_pbd = "tests/fixtures/pbd_files/dcm_email.pbd"
    
    if not os.path.exists(test_pbd):
        print(f"Error: Test PBD file not found: {test_pbd}")
    else:
        debug_pbd_entries(test_pbd)