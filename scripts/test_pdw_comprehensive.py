#!/usr/bin/env python3
"""Test the comprehensive PDW extractor."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decompile.analysis.pdw_comprehensive_extractor import PDWComprehensiveExtractor

def test_comprehensive_extraction(file_path):


    

    """Test comprehensive PDW extraction."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"Testing comprehensive PDW extraction on: {file_path}")
    print(f"File size: {len(data)} bytes")
    print("=" * 80)
    
    # Decompile the PDW
    dw = PDWComprehensiveExtractor.decompile_pdw(data, Path(file_path).name)
    
    # Print extracted information
    print(f"\nExtracted DataWindow Information:")
    print(f"Version: {dw.version}")
    if dw.name:
        print(f"Name: {dw.name}")
    print()
    
    if dw.sql:
        print("SQL Query:")
        print("-" * 40)
        print(dw.sql)
        print()
        
        if dw.tables:
            print("Tables:")
            for table in dw.tables:
                print(f"  - {table}")
            print()
    
    if dw.columns:
        print(f"Columns ({len(dw.columns)} found):")
        print("-" * 40)
        for col in dw.columns:
            print(f"  {col}")
        print()
    
    if dw.window_bounds:
        print(f"Window Bounds: {dw.window_bounds}")
        print()
    
    if dw.background_color:
        print(f"Background Color: {dw.background_color}")
        print()
    
    if dw.properties:
        print("Additional Properties:")
        print("-" * 40)
        for key, value in dw.properties.items():
            print(f"  {key}: {value}")
        print()
    
    # Generate source approximation
    print("\nGenerated Source Approximation:")
    print("=" * 80)
    source = dw.get_source_approximation()
    print(source)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test file
        test_file = "/Users/michael/Projects/sime-finch/test_output/extracted/dcm_detailobjects.pbd/dcm_detailobjects.pbd/resources/d_latest_treatment_ds.dwo"
        test_comprehensive_extraction(test_file)
    else:
        test_comprehensive_extraction(sys.argv[1])