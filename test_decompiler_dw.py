#!/usr/bin/env python3
"""Test the decompiler with DataWindow handling."""

from pathlib import Path
from decompile.main_decompiler import PowerBuilderDecompiler
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Create output directory
output_dir = Path("output/test_dw_handling")
output_dir.mkdir(parents=True, exist_ok=True)

# Run decompiler
decompiler = PowerBuilderDecompiler(output_dir)
success = decompiler.decompile_pbd(Path("input/pbd_files/dcm_accounting.pbd"))

print(f"\nDecompilation {'succeeded' if success else 'failed'}")

# Check what was created for DataWindows
dw_files = list(output_dir.glob("*.dwo.txt"))
print(f"\nDataWindow metadata files created: {len(dw_files)}")
if dw_files:
    # Show content of first DW metadata file
    print(f"\nSample DataWindow metadata ({dw_files[0].name}):")
    print(dw_files[0].read_text())