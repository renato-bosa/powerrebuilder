#!/usr/bin/env python3
"""Comprehensive parser test to check success rate across all DataWindow files."""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parse.parse_coordinator import parse_powerbuilder_directory


def analyze_parser_results():
    """Analyze parser results across all extracted DataWindow files."""
    
    print("Comprehensive Parser Test")
    print("=" * 70)
    
    # Find all extracted DataWindow files
    extracted_dir = Path(__file__).parent.parent / "output" / "extracted" / "pbd_files"
    
    if not extracted_dir.exists():
        print("⚠️  No extracted files found. Please run extraction first.")
        return
    
    # Collect all .dwo.srd files (DataWindow source files)
    dwo_files = list(extracted_dir.rglob("*.dwo.srd"))
    
    print(f"\nFound {len(dwo_files)} DataWindow source files")
    
    if not dwo_files:
        print("⚠️  No DataWindow files found.")
        return
    
    # Group by PBD file
    pbd_groups = defaultdict(list)
    for f in dwo_files:
        pbd_name = f.parts[-3] if len(f.parts) > 3 else "unknown"
        pbd_groups[pbd_name].append(f)
    
    # Parse each group
    total_files = 0
    total_success = 0
    total_failures = 0
    failure_types = defaultdict(int)
    
    for pbd_name, files in pbd_groups.items():
        print(f"\n\nTesting PBD: {pbd_name}")
        print("-" * 50)
        print(f"Files: {len(files)}")
        
        # Create temporary directory with files
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_dir = temp_path / "input"
            input_dir.mkdir()
            
            # Copy files
            for src_file in files[:10]:  # Test first 10 files from each PBD
                dst_file = input_dir / src_file.name
                import shutil
                shutil.copy2(src_file, dst_file)
            
            # Parse
            output_dir = temp_path / "parsed"
            output_dir.mkdir()
            
            try:
                parse_powerbuilder_directory(input_dir, output_dir)
                
                # Check results
                summary_file = output_dir / "parsed_summary.json"
                if summary_file.exists():
                    with open(summary_file, 'r') as f:
                        summary = json.load(f)
                    
                    pbd_total = summary['total_files']
                    pbd_success = summary['parsed_files']
                    pbd_failed = summary['failed_files']
                    
                    total_files += pbd_total
                    total_success += pbd_success
                    total_failures += pbd_failed
                    
                    print(f"  Parsed: {pbd_success}/{pbd_total} ({pbd_success/pbd_total*100:.1f}%)")
                    
                    # Analyze failures
                    if 'errors' in summary:
                        for error in summary['errors']:
                            error_type = error.get('error_type', 'Unknown')
                            failure_types[error_type] += 1
                            
                            # Show first few errors
                            if failure_types[error_type] <= 2:
                                print(f"  Error: {error_type}")
                                print(f"    File: {error.get('file', 'unknown')}")
                                print(f"    Details: {error.get('error', '')[:100]}...")
                
            except Exception as e:
                print(f"  Failed to parse: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)
    print(f"Total DataWindow files tested: {total_files}")
    print(f"Successfully parsed: {total_success}")
    print(f"Failed to parse: {total_failures}")
    print(f"Success rate: {total_success/total_files*100:.1f}%" if total_files > 0 else "N/A")
    
    if failure_types:
        print("\nFailure breakdown:")
        for error_type, count in sorted(failure_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count}")
    
    # Check specific improvements
    print("\n" + "=" * 70)
    print("IMPROVEMENT VALIDATION")
    print("=" * 70)
    
    # Test PBSELECT with COMPUTE
    pbselect_files = []
    compute_files = []
    
    for f in dwo_files[:50]:  # Check first 50 files
        try:
            content = f.read_text()
            if "PBSELECT" in content:
                pbselect_files.append(f)
                if "COMPUTE" in content:
                    compute_files.append(f)
        except:
            pass
    
    print(f"Files with PBSELECT: {len(pbselect_files)}")
    print(f"Files with COMPUTE: {len(compute_files)}")
    
    # Test a few specific files
    if compute_files:
        print("\nTesting COMPUTE clause handling:")
        test_file = compute_files[0]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_dir = temp_path / "input"
            input_dir.mkdir()
            output_dir = temp_path / "parsed"
            output_dir.mkdir()
            
            # Copy test file
            import shutil
            shutil.copy2(test_file, input_dir / test_file.name)
            
            try:
                parse_powerbuilder_directory(input_dir, output_dir)
                summary_file = output_dir / "parsed_summary.json"
                if summary_file.exists():
                    with open(summary_file, 'r') as f:
                        summary = json.load(f)
                    if summary['parsed_files'] > 0:
                        print(f"  ✓ COMPUTE clause parsing works!")
                    else:
                        print(f"  ✗ COMPUTE clause parsing failed")
            except:
                print(f"  ✗ Error testing COMPUTE clause")


if __name__ == "__main__":
    analyze_parser_results()