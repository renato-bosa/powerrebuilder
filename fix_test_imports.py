#!/usr/bin/env python3
"""Fix test imports after module consolidation."""

import os
import re
from pathlib import Path

# Import mappings based on the consolidation
IMPORT_MAPPINGS = {
    # Common utilities have been reorganized
    "from src.model.utils.common import": [
        "from src.common.utils.strings import camel_to_snake, snake_to_camel, truncate",
        "from src.common.utils.files import ensure_directory, get_file_extension, normalize_path, read_file_safe", 
        "from src.common.utils.collections import chunk_list, find_duplicates, filter_dict",
    ],
    
    # Extract modules consolidated
    "from src.extract.pbd.corruption import": "from src.extract.pbd.corruption import",
    "from src.common.utils.type_detector import": "from src.common.utils.type_detector import",
    "from src.common.utils.datawindow import": "from src.common.utils.datawindow import",
    
    # Contracts moved
    "from src.contracts.extractors import": "from src.contracts import",
    "from src.contracts.parsers import": "from src.contracts import",
    "from src.contracts.decompilers import": "from src.contracts import",
    "from src.contracts.generators import": "from src.contracts import",
    
    # Model AST reorganized
    "from src.model.ast.node_kind import": "from src.model.ast import",
    
    # System functions
    "from src.model.system.functions import": "from src.model.expressions import",
}

# Additional simple replacements
SIMPLE_REPLACEMENTS = {
    "tests.factories": "tests.utils.factories",
}


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply import mappings
        for old_import, new_imports in IMPORT_MAPPINGS.items():
            if old_import in content:
                if isinstance(new_imports, list):
                    # For multi-line replacements, we need to be smarter
                    # Find what was being imported
                    pattern = rf"{re.escape(old_import)}\s*\((.*?)\)"
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        imported_items = match.group(1)
                        # Parse imported items
                        items = [item.strip() for item in imported_items.split(',')]
                        items = [item for item in items if item and not item.startswith('#')]
                        
                        # Group items by their new import
                        new_import_lines = []
                        for new_import in new_imports:
                            # Extract module from new import
                            module_match = re.search(r'from ([\w.]+) import', new_import)
                            if module_match:
                                module = module_match.group(1)
                                # Find which items belong to this module
                                module_items = []
                                for item in items:
                                    # Check if this item is in the new import line
                                    if item in new_import:
                                        module_items.append(item)
                                
                                if module_items:
                                    new_import_lines.append(f"from {module} import {', '.join(module_items)}")
                        
                        # Replace the old import with new ones
                        if new_import_lines:
                            replacement = '\n'.join(new_import_lines)
                            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                else:
                    content = content.replace(old_import, new_imports)
        
        # Apply simple replacements
        for old, new in SIMPLE_REPLACEMENTS.items():
            content = content.replace(old, new)
        
        # Write back if changed
        if content != original_content:
            file_path.write_text(content)
            print(f"Fixed imports in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Fix imports in all test files."""
    test_dir = Path("tests")
    fixed_count = 0
    
    # Find all Python test files
    test_files = list(test_dir.rglob("*.py"))
    
    print(f"Found {len(test_files)} Python files in tests/")
    
    for test_file in test_files:
        if fix_imports_in_file(test_file):
            fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files")


if __name__ == "__main__":
    main()