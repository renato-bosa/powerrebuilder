#!/usr/bin/env python3
"""Test the improved DataWindow extraction."""

from pathlib import Path
from decompile.main_decompiler import PowerBuilderDecompiler
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Create output directory
output_dir = Path("output/test_improved_dw")
output_dir.mkdir(parents=True, exist_ok=True)

# Create decompiler instance
decompiler = PowerBuilderDecompiler(output_dir)

# Test on just the DataWindows
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    print("Testing improved DataWindow extraction:")
    print("="*60)
    
    dw_count = 0
    success_count = 0
    
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    dw_count += 1
                    print(f"\nProcessing DW #{dw_count}: {entry.objectname}")
                    
                    success = decompiler._extract_datawindow(f, entry, pbd_path.name)
                    if success:
                        success_count += 1
                        print(f"  ✓ Success")
                    else:
                        print(f"  ✗ Failed")

print(f"\n{'='*60}")
print(f"Summary: {success_count}/{dw_count} DataWindows processed successfully")

# Check output files
print("\nOutput files created:")
for file in sorted(output_dir.iterdir()):
    size = file.stat().st_size
    print(f"  {file.name} ({size} bytes)")
    
    # Show preview of SQL files
    if file.suffix == '.sql' and size < 2000:
        content = file.read_text()
        # Extract just the SQL part
        if 'PBSELECT' in content:
            sql_start = content.find('PBSELECT')
            sql_part = content[sql_start:sql_start+200]
            print(f"    Preview: {sql_part}...")