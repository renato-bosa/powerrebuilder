#!/usr/bin/env python3
"""Script to merge duplicate test directories."""

import shutil
from pathlib import Path


def merge_test_directories() -> None:








    """Merge tests/parse into tests/test_parse."""
    project_root = Path(__file__).parent.parent.parent

    source_dir = project_root / "tests" / "parse"
    target_dir = project_root / "tests" / "test_parse"

    if not source_dir.exists():
        return

    if not target_dir.exists():
        return

    # Get lists of files
    source_files = {f.name: f for f in source_dir.glob("*.py")}
    target_files = {f.name: f for f in target_dir.glob("*.py")}

    # Check for conflicts
    conflicts = set(source_files.keys()) & set(target_files.keys())
    if conflicts:
        for conflict in sorted(conflicts):
            source_size = source_files[conflict].stat().st_size
            target_size = target_files[conflict].stat().st_size

            # For now, keep the larger file (likely more complete)
            if source_size > target_size:
                # Backup target version
                backup_name = target_files[conflict].stem + "_from_test_parse.py"
                backup_path = target_dir / backup_name
                shutil.copy2(target_files[conflict], backup_path)

                # Copy source over target
                shutil.copy2(source_files[conflict], target_files[conflict])
            else:
                pass

    # Copy unique files from source to target
    unique_in_source = set(source_files.keys()) - set(target_files.keys())
    if unique_in_source:
        for filename in sorted(unique_in_source):
            source_file = source_files[filename]
            target_file = target_dir / filename
            shutil.copy2(source_file, target_file)

    # Remove the source directory
    shutil.rmtree(source_dir)

    # Check if __init__.py exists, create if not
    init_file = target_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Parse module tests."""\n')


if __name__ == "__main__":
    merge_test_directories()
