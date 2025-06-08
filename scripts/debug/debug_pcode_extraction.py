#!/usr/bin/env python3
"""Debug script to understand why P-code files (.fun) are not being created during extraction."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from extract.pbd.extraction.library import Library as PBDFile
from extract.pbd.structures.entry import PbEntryDefinition as Entry
from extract.pbd.exceptions import PbdError as PBDParseError

# Source extensions from the core.py file
SOURCE_EXTENSIONS = ('.sru', '.srw', '.srd', '.srm', '.sra', '.srq', '.srs', '.srf', '.srj')

def debug_pcode_detection(pbd_path: str):
    """Extract PBD and debug P-code detection logic."""
    print(f"Debugging P-code extraction for: {pbd_path}")
    print("=" * 80)
    
    try:
        # Create output directory for debug info
        output_dir = Path("output/debug_pcode")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open and read the PBD file
        with open(pbd_path, 'rb') as f:
            pbd_data = f.read()
        
        # Create PBD instance
        pbd = PBDFile(pbd_data, filename=pbd_path)
        
        # Parse the PBD
        pbd.parse()
        
        # Debug log file
        debug_log = output_dir / "pcode_detection_debug.txt"
        
        with open(debug_log, 'w') as log:
            log.write(f"PBD File: {pbd_path}\n")
            log.write(f"Total entries: {len(pbd.entries)}\n")
            log.write("=" * 80 + "\n\n")
            
            pcode_count = 0
            non_pcode_count = 0
            
            for i, entry in enumerate(pbd.entries):
                # Get entry details
                obj_name = entry.objectname if hasattr(entry, 'objectname') else 'N/A'
                version = entry.version if hasattr(entry, 'version') else 'N/A'
                
                # Check if it ends with source extensions
                ends_with_source = obj_name.lower().endswith(SOURCE_EXTENSIONS)
                
                # Check version string
                version_lower = version.lower() if version != 'N/A' else ''
                has_function = "function" in version_lower
                has_event = "event" in version_lower
                
                # Check special extensions
                is_srf_srj = obj_name.lower().endswith((".srf", ".srj"))
                
                # Apply the exact logic from core.py
                is_potential_pcode = (ends_with_source and (has_function or has_event)) or is_srf_srj
                
                # Log entry details
                log.write(f"Entry {i}:\n")
                log.write(f"  Object Name: {obj_name}\n")
                log.write(f"  Version: {version}\n")
                log.write(f"  Version (lower): {version_lower}\n")
                log.write(f"  Ends with source extension: {ends_with_source}\n")
                log.write(f"  Has 'function' in version: {has_function}\n")
                log.write(f"  Has 'event' in version: {has_event}\n")
                log.write(f"  Is .srf/.srj: {is_srf_srj}\n")
                log.write(f"  Is potential P-code: {is_potential_pcode}\n")
                
                # Also check if entry has data
                has_data = hasattr(entry, 'data') and entry.data is not None
                data_length = len(entry.data) if has_data else 0
                log.write(f"  Has data: {has_data} (length: {data_length})\n")
                
                # Print to console for immediate feedback
                print(f"\nEntry {i}: {obj_name}")
                print(f"  Version: {version}")
                print(f"  Is potential P-code: {is_potential_pcode}")
                
                if is_potential_pcode:
                    pcode_count += 1
                    # Try to extract P-code data
                    if has_data:
                        # Save raw data for inspection
                        pcode_file = output_dir / f"{obj_name}.raw"
                        with open(pcode_file, 'wb') as pf:
                            pf.write(entry.data)
                        log.write(f"  Saved raw data to: {pcode_file}\n")
                        print(f"  Saved raw data to: {pcode_file}")
                else:
                    non_pcode_count += 1
                
                log.write("\n")
            
            # Summary
            summary = f"\nSummary:\n"
            summary += f"Total entries: {len(pbd.entries)}\n"
            summary += f"Potential P-code entries: {pcode_count}\n"
            summary += f"Non P-code entries: {non_pcode_count}\n"
            
            log.write("=" * 80 + "\n")
            log.write(summary)
            print("\n" + "=" * 80)
            print(summary)
            
            # Additional analysis - check what types of objects we have
            log.write("\nObject types analysis:\n")
            print("\nObject types analysis:")
            
            extensions = {}
            for entry in pbd.entries:
                obj_name = entry.objectname if hasattr(entry, 'objectname') else 'N/A'
                ext = Path(obj_name).suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1
            
            for ext, count in sorted(extensions.items()):
                msg = f"  {ext}: {count} entries"
                log.write(msg + "\n")
                print(msg)
        
        print(f"\nDebug log saved to: {debug_log}")
        
        # Now let's actually try the extraction process
        print("\n" + "=" * 80)
        print("Testing actual extraction process...")
        
        # Create a fresh output directory for extraction
        extract_dir = output_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract entries
        extracted_files = pbd.extract_all(str(extract_dir))
        
        print(f"\nExtracted {len(extracted_files)} files to: {extract_dir}")
        
        # Check for .fun files
        fun_files = list(extract_dir.glob("**/*.fun"))
        print(f"Found {len(fun_files)} .fun files")
        
        if fun_files:
            print("\n.fun files created:")
            for fun_file in fun_files[:10]:  # Show first 10
                print(f"  {fun_file}")
        else:
            print("\nNo .fun files were created!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test PBD file
    test_pbd = "tests/fixtures/pbd_files/dcm_email.pbd"
    
    if not os.path.exists(test_pbd):
        print(f"Error: Test PBD file not found: {test_pbd}")
        sys.exit(1)
    
    debug_pcode_detection(test_pbd)