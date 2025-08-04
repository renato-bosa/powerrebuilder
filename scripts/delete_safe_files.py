#!/usr/bin/env python3
"""Delete files that are confirmed safe to delete."""

import os

# Read the safe delete list
with open("build/safe_delete_list.txt") as f:
    files_to_delete = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

print(f"Found {len(files_to_delete)} files safe to delete")
print("=" * 80)

# Group files by directory for better organization
files_by_dir = {}
for filepath in files_to_delete:
    dirname = os.path.dirname(filepath)
    if dirname not in files_by_dir:
        files_by_dir[dirname] = []
    files_by_dir[dirname].append(filepath)

# Delete files in batches by directory
total_deleted = 0
total_size_freed = 0

for dirname, files in sorted(files_by_dir.items()):
    print(f"\nDeleting {len(files)} files from {dirname}:")

    for filepath in files:
        if not os.path.exists(filepath):
            print(f"  SKIP: {filepath} - Already deleted")
            continue

        # Get file size before deletion
        try:
            file_size = os.path.getsize(filepath)
        except:
            file_size = 0

        # Delete the file
        try:
            os.remove(filepath)
            total_deleted += 1
            total_size_freed += file_size
            print(f"  ✓ Deleted: {filepath} ({file_size:,} bytes)")
        except Exception as e:
            print(f"  ✗ Failed: {filepath} - {e}")

print("\n" + "=" * 80)
print("Summary:")
print(f"  Files deleted: {total_deleted}")
print(
    f"  Space freed: {total_size_freed:,} bytes ({total_size_freed / 1024 / 1024:.2f} MB)"
)

# Check for empty directories that can be removed
print("\nChecking for empty directories...")
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
    for d in empty_dirs:
        print(f"  - {d}")

    response = input("\nDelete these empty directories? (y/n): ")
    if response.lower() == "y":
        for d in empty_dirs:
            try:
                os.rmdir(d)
                print(f"  ✓ Removed: {d}")
            except Exception as e:
                print(f"  ✗ Failed: {d} - {e}")
else:
    print("No empty directories found.")
