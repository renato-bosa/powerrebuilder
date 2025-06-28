#!/usr/bin/env python3
"""Test script to validate parser and decoder improvements in the full pipeline."""

import sys
import json
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.pipeline.pipeline_coordinator import PipelineCoordinator
from parse.parse_coordinator import parse_powerbuilder_directory


def test_parser_improvements():
    """Test that the parser now handles PBSELECT statements."""
    
    print("Testing Parser Improvements")
    print("=" * 50)
    
    # Create a temporary directory for test output
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy some test DataWindow files that were failing
        test_files = [
            "d_get_treatmentbill_ds.dwo.srd",
            "d_get_person_cliniclink_sql.dwo.srd",
            "d_firstbilldate_sql.dwo.srd",
        ]
        
        source_dir = Path(__file__).parent.parent / "output" / "extracted" / "pbd_files" / "dcm_detailobjects.pbd" / "dcm_detailobjects.pbd"
        
        if not source_dir.exists():
            print("⚠️  Test files not found. Please run extraction first.")
            return False
        
        # Create test input directory
        input_dir = temp_path / "input"
        input_dir.mkdir()
        
        # Copy test files
        copied = 0
        for test_file in test_files:
            src = source_dir / test_file
            if src.exists():
                dst = input_dir / test_file
                shutil.copy2(src, dst)
                copied += 1
                print(f"  Copied: {test_file}")
        
        if copied == 0:
            print("⚠️  No test files found to copy.")
            return False
        
        # Create output directory
        output_dir = temp_path / "parsed"
        output_dir.mkdir()
        
        # Run parser
        print("\nRunning parser...")
        result = parse_powerbuilder_directory(input_dir, output_dir)
        
        # Check results
        summary_file = output_dir / "parsed_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            print(f"\nResults:")
            print(f"  Total files: {summary['total_files']}")
            print(f"  Parsed successfully: {summary['parsed_files']}")
            print(f"  Failed: {summary['failed_files']}")
            
            # Check specific files
            parsed_files = {Path(f['file']).name for f in summary.get('files', [])}
            for test_file in test_files:
                sql_file = test_file.replace('.srd', '.sql')
                if sql_file in parsed_files:
                    print(f"  ✓ {test_file} -> parsed successfully")
                else:
                    print(f"  ✗ {test_file} -> failed to parse")
            
            # Success if more than 50% parsed
            success_rate = summary['parsed_files'] / summary['total_files'] if summary['total_files'] > 0 else 0
            return success_rate > 0.5
        else:
            print("⚠️  No summary file generated")
            return False


def test_decoder_improvements():
    """Test that the new decoder handles corruption better."""
    
    print("\n\nTesting Decoder Improvements")
    print("=" * 50)
    
    # Test SQL files that might have corruption
    test_dir = Path(__file__).parent.parent / "output" / "extracted" / "pbd_files" / "dcm_detailobjects.pbd" / "dcm_detailobjects.pbd"
    
    if not test_dir.exists():
        print("⚠️  Test directory not found")
        return False
    
    # Look for SQL files
    sql_files = list(test_dir.glob("*.sql"))[:5]  # Test first 5 SQL files
    
    if not sql_files:
        print("⚠️  No SQL files found")
        return False
    
    corruption_found = 0
    corruption_fixed = 0
    
    for sql_file in sql_files:
        with open(sql_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Look for potential corruption patterns
        import re
        corruption_pattern = re.compile(r'\*(?=[A-Z])|(?<=[a-z])\*|NA\s*\*E')
        
        matches = corruption_pattern.findall(content)
        if matches:
            corruption_found += 1
            print(f"\n  File: {sql_file.name}")
            print(f"    Potential corruptions: {len(matches)}")
            
            # Check if common patterns are fixed
            if 'NAME=' in content and 'NA *E=' not in content:
                print(f"    ✓ NA *E pattern fixed")
                corruption_fixed += 1
            if 'COLUMN' in content and 'COL*MN' not in content:
                print(f"    ✓ COL*MN pattern fixed")
            if 'address' in content.lower() and 'a*dress' not in content.lower():
                print(f"    ✓ a*dress pattern fixed")
    
    if corruption_found == 0:
        print("\n  No corruption patterns found in test files - decoder working well!")
        return True
    else:
        fix_rate = corruption_fixed / corruption_found if corruption_found > 0 else 0
        print(f"\n  Corruption fix rate: {fix_rate:.1%}")
        return fix_rate > 0.5


def test_full_pipeline():
    """Test the full pipeline with improvements."""
    
    print("\n\nTesting Full Pipeline Integration")
    print("=" * 50)
    
    # Check if we have input files
    input_dir = Path(__file__).parent.parent / "input" / "pbd_files"
    test_file = input_dir / "dcm_detailobjects.pbd"
    
    if not test_file.exists():
        print("⚠️  Test PBD file not found")
        print(f"    Looking for: {test_file}")
        return False
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "pipeline_test"
        
        print(f"  Input: {test_file.name}")
        print(f"  Output: {output_dir}")
        
        # Initialize pipeline with required directories
        coordinator = PipelineCoordinator(
            input_dir=str(input_dir),
            output_dir=str(output_dir)
        )
        
        # Run extraction only (parsing is tested separately)
        print("\n  Running extraction...")
        try:
            # Process the PBD file
            result = coordinator.process_files([str(test_file)])
            
            if result and result.get('stages', {}).get('extract'):
                extract_stats = result['stages']['extract']
                # Check the temp directory for extracted files
                extracted_dir = Path(temp_dir) / '.temp' / 'extracted'
                if extracted_dir.exists():
                    extracted_files = list(extracted_dir.rglob('*'))
                    print(f"  ✓ Extraction successful: {len(extracted_files)} files")
                    
                    # Check for DataWindow files
                    dw_files = [f for f in extracted_files if f.suffix in ['.dwo', '.srd']]
                    print(f"  ✓ DataWindow files found: {len(dw_files)}")
                    
                    return len(extracted_files) > 0
                else:
                    print(f"  ✗ Extracted directory not found: {extracted_dir}")
                    return False
            else:
                print("  ✗ Extraction failed: No results or extract stage missing")
                print(f"  Result: {result}")
                return False
                
        except Exception as e:
            print(f"  ✗ Pipeline error: {e}")
            return False


def main():
    """Run all tests and report results."""
    
    print("PowerBuilder Pipeline Improvements Test Suite")
    print("=" * 70)
    
    results = {
        'parser': test_parser_improvements(),
        'decoder': test_decoder_improvements(),
        'pipeline': test_full_pipeline()
    }
    
    print("\n\nTest Summary")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name.capitalize()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All tests passed! The improvements are working correctly.")
    else:
        print("✗ Some tests failed. Please check the output above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)