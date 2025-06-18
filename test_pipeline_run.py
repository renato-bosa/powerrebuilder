#!/usr/bin/env python3
"""Test pipeline run to check for errors."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extract.extract_coordinator import extract_pbls

def test_pipeline():
    """Run extraction pipeline on a sample file."""
    input_dir = Path("/Users/michael/Projects/sime-finch/input/pbd_files")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        print("Running extraction pipeline...")
        print(f"Input: {input_dir}")
        print(f"Output: {output_dir}")
        
        try:
            # Run extraction
            extract_pbls(
                str(input_dir),
                str(output_dir),
                enable_byte_recovery=False,
                extract_resources=True
            )
            print("\nExtraction completed successfully!")
            
            # Count results
            pbd_files = list(input_dir.glob("*.pbd"))
            extracted_dirs = list(output_dir.glob("*"))
            
            print(f"\nProcessed {len(pbd_files)} PBD files")
            print(f"Created {len(extracted_dirs)} output directories")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()