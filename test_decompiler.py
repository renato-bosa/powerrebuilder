#!/usr/bin/env python3
"""Test the decompilation pipeline on a sample P-code file."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from decompile.decompiler import PowerBuilderDecompiler
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_decompilation():
    """Test decompilation on a sample file."""
    # Test file
    test_file = Path("output/test_bytes_fix/dcm_login.pbd/dcm_login.pbd/f_get_username.fun")
    
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return
    
    # Create decompiler
    decompiler = PowerBuilderDecompiler()
    
    print(f"\n{'='*60}")
    print(f"Testing decompilation of: {test_file.name}")
    print(f"{'='*60}\n")
    
    try:
        # Decompile the file
        source = decompiler.decompile_file(test_file)
        
        # Display results
        print("Decompiled Source:")
        print("-" * 60)
        print(source)
        print("-" * 60)
        
        # Save to output file
        output_file = test_file.with_suffix('.pb')
        output_file.write_text(source, encoding='utf-8')
        print(f"\nSaved decompiled source to: {output_file}")
        
    except Exception as e:
        print(f"Error during decompilation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_decompilation()