#!/usr/bin/env python3
"""Delete empty directories."""

import os

print("Checking for empty directories...")
empty_dirs = []

for root, dirs, files in os.walk("src", topdown=False):
    # Skip __pycache__ directories
    if "__pycache__" in root:
        continue

    # Check if directory is empty (no files and no subdirs except __pycache__)
    real_files = [f for f in files if not f.endswith(".pyc")]
    real_dirs = [d for d in dirs if d != "__pycache__"]

    if not real_files and not real_dirs:
        empty_dirs.append(root)

if empty_dirs:
    print(f"\nFound {len(empty_dirs)} empty directories:")
    for d in sorted(empty_dirs):
        print(f"  - {d}")

    print("\nDeleting empty directories...")
    for d in empty_dirs:
        try:
            os.rmdir(d)
            print(f"  ✓ Removed: {d}")
        except Exception as e:
            print(f"  ✗ Failed: {d} - {e}")
else:
    print("No empty directories found.")
