#!/usr/bin/env python3
"""Test DataWindow extraction only."""

from pathlib import Path
from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_io.utils import BLOCK_SIZE
from decompile.main_decompiler import PowerBuilderDecompiler
import logging

logging.basicConfig(level=logging.INFO)

pbd_path = Path("input/pbd_files/dcm_accounting.pbd")
output_dir = Path("output/test_dw_only")
output_dir.mkdir(parents=True, exist_ok=True)

# Create decompiler instance
decompiler = PowerBuilderDecompiler(output_dir)

with open(pbd_path, 'rb') as f:
    header = extract_pbl_header(f, BLOCK_SIZE, str(pbd_path))
    nodes = extract_nods(f, header.is_unicode, header.first_nod_offset, BLOCK_SIZE)
    
    print("Processing DataWindows only:")
    dw_count = 0
    for node in nodes:
        if node and hasattr(node, 'entry_defs'):
            for entry in node.entry_defs:
                if entry and entry.objectname.lower().endswith('.dwo'):
                    dw_count += 1
                    print(f"\nProcessing DW #{dw_count}: {entry.objectname}")
                    
                    # Use the decompiler's DataWindow extraction method
                    success = decompiler._extract_datawindow(f, entry, pbd_path.name)
                    print(f"  Result: {'Success' if success else 'Failed'}")
                    
                    if dw_count >= 3:  # Just test first 3
                        break
        if dw_count >= 3:
            break

print(f"\nCreated files:")
for file in sorted(output_dir.iterdir()):
    print(f"  {file.name}")
    if file.suffix == '.txt' and file.stat().st_size < 1000:
        print(f"    Content preview:")
        print("    " + file.read_text().replace('\n', '\n    ')[:500])