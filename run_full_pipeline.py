#!/usr/bin/env python3
"""Run the full PowerBuilder conversion pipeline on all PBD files."""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the pipeline on all PBD files."""
    input_dir = Path("data/input/pbd_files")
    output_dir = Path("output/full_pipeline_run")
    
    # Get all PBD files
    pbd_files = list(input_dir.glob("*.pbd"))
    print(f"Found {len(pbd_files)} PBD files to process")
    
    # Run the extraction phase
    print("\n" + "="*60)
    print("PHASE 1: EXTRACTION")
    print("="*60)
    
    cmd = [
        "python", "main.py", "extract", "files",
        str(input_dir),
        str(output_dir / "extract"),
        "--enable-byte-recovery"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"Extraction failed with return code {result.returncode}")
        sys.exit(1)
    
    print("\n✅ Extraction completed")
    
    # Count extracted files
    extracted_files = list((output_dir / "extract").rglob("*"))
    file_count = len([f for f in extracted_files if f.is_file()])
    print(f"Extracted {file_count} files")
    
    # Show summary
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"Input PBD files: {len(pbd_files)}")
    print(f"Extracted files: {file_count}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()