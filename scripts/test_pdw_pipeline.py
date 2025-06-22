#!/usr/bin/env python3
"""Test PDW extraction in the pipeline."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extract.pbd.io.file_operations import _extract_datawindow_syntax

def test_pdw_extraction():


    

    """Test PDW extraction with our problematic files."""
    test_files = [
        "test_output/extracted/dcm_detailobjects.pbd/dcm_detailobjects.pbd/resources/d_latest_treatment_ds.dwo",
        "test_output/extracted/dcm_detailobjects.pbd/dcm_detailobjects.pbd/resources/d_outstandinginv_ds.dwo"
    ]
    
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            print(f"\nTesting: {path.name}")
            print("=" * 60)
            
            with open(path, 'rb') as f:
                data = f.read()
            
            # Test extraction
            result = _extract_datawindow_syntax(data, path.name)
            
            if result:
                print(f"SUCCESS: Extracted {len(result)} characters")
                # Show first few lines
                lines = result.split('\n')[:10]
                print("First 10 lines:")
                for line in lines:
                    print(f"  {line}")
            else:
                print("FAILED: No extraction result")
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    test_pdw_extraction()