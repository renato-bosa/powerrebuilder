#!/usr/bin/env python3
"""Test using the CLI extraction to see if it works."""

import subprocess
import sys

# Run the extraction
result = subprocess.run([
    sys.executable, "-m", "extract.pbd_core.core",
    "input/pbd_files/dcm_accounting.pbd",
    "-o", "output/test_extract_cli"
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")