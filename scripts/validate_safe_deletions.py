#!/usr/bin/env python3
"""Validate which files from delete_list.txt are truly safe to delete."""

import os
import subprocess
from pathlib import Path
import re

# Read the delete list
with open('build/delete_list.txt', 'r') as f:
    files_to_check = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Files that are definitely safe to delete
safe_to_delete = []
not_safe = []

def check_file_references(filepath):
    """Check if a file is referenced anywhere in the codebase."""
    # Get the module name from the file path
    module_parts = filepath.replace('.py', '').replace('/', '.')
    if module_parts.startswith('src.'):
        module_parts = module_parts[4:]
    
    basename = os.path.basename(filepath).replace('.py', '')
    
    # Patterns to search for
    patterns = [
        f"from {module_parts}",
        f"import {module_parts}",
        f"from .{basename}",
        f"import .{basename}",
        f'"{filepath}"',
        f"'{filepath}'",
        f'"{module_parts}"',
        f"'{module_parts}'",
        basename  # Check for dynamic imports or string references
    ]
    
    references = []
    for pattern in patterns:
        try:
            # Use ripgrep to search for the pattern
            result = subprocess.run(
                ['rg', '-l', '--type', 'py', pattern, 'src/', 'tests/'],
                capture_output=True,
                text=True
            )
            if result.stdout:
                found_files = result.stdout.strip().split('\n')
                # Filter out self-references
                found_files = [f for f in found_files if f != filepath]
                if found_files:
                    references.extend(found_files)
        except subprocess.CalledProcessError:
            pass
    
    return list(set(references))

print("Validating files for safe deletion...")
print("=" * 80)

for filepath in files_to_check:
    if not os.path.exists(filepath):
        print(f"SKIP: {filepath} - File doesn't exist")
        continue
    
    print(f"\nChecking: {filepath}")
    
    # Check for references
    refs = check_file_references(filepath)
    
    if refs:
        print(f"  NOT SAFE - Referenced by:")
        for ref in refs[:5]:  # Show first 5 references
            print(f"    - {ref}")
        if len(refs) > 5:
            print(f"    ... and {len(refs) - 5} more files")
        not_safe.append((filepath, refs))
    else:
        print(f"  SAFE - No references found")
        safe_to_delete.append(filepath)

# Write safe delete list
with open('build/safe_delete_list.txt', 'w') as f:
    f.write("# Files that are confirmed safe to delete\n")
    f.write(f"# Total: {len(safe_to_delete)} files\n\n")
    for filepath in sorted(safe_to_delete):
        f.write(f"{filepath}\n")

# Write not safe list
with open('build/not_safe_to_delete.txt', 'w') as f:
    f.write("# Files that have references and cannot be safely deleted\n")
    f.write(f"# Total: {len(not_safe)} files\n\n")
    for filepath, refs in sorted(not_safe):
        f.write(f"\n{filepath}\n")
        f.write(f"  Referenced by {len(refs)} files:\n")
        for ref in refs[:10]:
            f.write(f"    - {ref}\n")
        if len(refs) > 10:
            f.write(f"    ... and {len(refs) - 10} more\n")

print("\n" + "=" * 80)
print(f"Summary:")
print(f"  Total files checked: {len(files_to_check)}")
print(f"  Safe to delete: {len(safe_to_delete)}")
print(f"  Not safe: {len(not_safe)}")
print(f"\nResults written to:")
print(f"  - build/safe_delete_list.txt")
print(f"  - build/not_safe_to_delete.txt")