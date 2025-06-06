#!/usr/bin/env python3
"""Script to merge duplicate test directories."""

import shutil
from pathlib import Path


def merge_test_directories():
    """Merge tests/parse into tests/test_parse."""
    project_root = Path(__file__).parent.parent.parent
    
    source_dir = project_root / "tests" / "parse"
    target_dir = project_root / "tests" / "test_parse"
    
    if not source_dir.exists():
        print("Source directory tests/parse not found")
        return
    
    if not target_dir.exists():
        print("Target directory tests/test_parse not found")
        return
    
    # Get lists of files
    source_files = {f.name: f for f in source_dir.glob("*.py")}
    target_files = {f.name: f for f in target_dir.glob("*.py")}
    
    # Check for conflicts
    conflicts = set(source_files.keys()) & set(target_files.keys())
    if conflicts:
        print(f"Found {len(conflicts)} conflicting files:")
        for conflict in sorted(conflicts):
            print(f"  - {conflict}")
            source_size = source_files[conflict].stat().st_size
            target_size = target_files[conflict].stat().st_size
            print(f"    Source: {source_size} bytes")
            print(f"    Target: {target_size} bytes")
            
            # For now, keep the larger file (likely more complete)
            if source_size > target_size:
                print(f"    → Will use source version (larger)")
                # Backup target version
                backup_name = target_files[conflict].stem + "_from_test_parse.py"
                backup_path = target_dir / backup_name
                shutil.copy2(target_files[conflict], backup_path)
                print(f"    → Backed up target to {backup_name}")
                
                # Copy source over target
                shutil.copy2(source_files[conflict], target_files[conflict])
                print(f"    → Copied source version to target")
            else:
                print(f"    → Keeping target version (larger or equal)")
    
    # Copy unique files from source to target
    unique_in_source = set(source_files.keys()) - set(target_files.keys())
    if unique_in_source:
        print(f"\nCopying {len(unique_in_source)} unique files from tests/parse:")
        for filename in sorted(unique_in_source):
            source_file = source_files[filename]
            target_file = target_dir / filename
            shutil.copy2(source_file, target_file)
            print(f"  ✓ Copied {filename}")
    
    # Remove the source directory
    print(f"\nRemoving source directory: {source_dir}")
    shutil.rmtree(source_dir)
    print("✓ Removed tests/parse")
    
    # Check if __init__.py exists, create if not
    init_file = target_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Parse module tests."""\n')
        print("✓ Created __init__.py in tests/test_parse")
    
    print("\nTest directory merge complete!")
    print(f"All parse tests are now in: {target_dir}")


if __name__ == "__main__":
    merge_test_directories()