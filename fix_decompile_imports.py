#!/usr/bin/env python3
"""Fix import paths in decompile module after reorganization."""

import re
from pathlib import Path

def fix_file(file_path, mappings):
    """Fix imports in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for old_import, new_import in mappings.items():
        content = re.sub(old_import, new_import, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed imports in {file_path}")
        return True
    return False

# Define import mappings
IMPORT_MAPPINGS = {
    # Fix analysis -> analyzers
    r'from \.analysis\.': 'from .analyzers.',
    r'from decompile\.analysis\.': 'from decompile.analyzers.',
    
    # Fix enhanced_datawindow_integration location
    r'from \.analysis\.enhanced_datawindow_integration': 'from .extractors.enhanced_datawindow_integration',
    r'from decompile\.analysis\.enhanced_datawindow_integration': 'from decompile.extractors.enhanced_datawindow_integration',
    
    # Fix schema_documentation_generator location
    r'from \.analysis\.schema_documentation_generator': 'from .analyzers.schema_documentation_generator',
    
    # Fix core references
    r'from \.core\.': 'from decompile.core.',
    
    # Fix extractors references
    r'from \.extractors\.': 'from decompile.extractors.',
}

# Find all Python files in decompile directory
decompile_dir = Path('decompile')
python_files = list(decompile_dir.rglob('*.py'))

# Fix imports in all files
fixed_count = 0
for file_path in python_files:
    if fix_file(file_path, IMPORT_MAPPINGS):
        fixed_count += 1

print(f"\nFixed imports in {fixed_count} files")