#!/usr/bin/env python3
"""Fix critical test imports based on actual module structure."""

import os
import re
import ast
from pathlib import Path

# More comprehensive import mappings based on errors
IMPORT_MAPPINGS = {
    # Model AST reorganization
    "from src.model.ast.node_kind import": "from src.model.ast import",
    "src.model.ast.node_kind": "src.model.ast",
    
    # Expressions moved
    "from src.model.expressions.ast_expressions import": "from src.model.ast.expressions import",
    "src.model.expressions.ast_expressions": "src.model.ast.expressions",
    
    # Contracts consolidated
    "from src.contracts.extractors import": "from src.contracts.interfaces import",
    "src.contracts.extractors": "src.contracts.interfaces",
    
    # Utils consolidated
    "from src.common.utils.type_detector import": "from src.parse.parser.specialized.types import detect_type",
    "src.common.utils.type_detector": "src.parse.parser.specialized.types",
    
    # Core interfaces moved
    "from src.core.interfaces import": "from src.contracts.interfaces import",
    "src.core.interfaces": "src.contracts.interfaces",
    
    # Pipeline interfaces
    "from src.common.pipeline.interfaces import": "from src.contracts.interfaces import",
    "src.common.pipeline.interfaces": "src.contracts.interfaces",
    
    # Startup module removed
    "from src.core.startup import": "from src.core import",
    "src.core.startup": "src.core",
}

def fix_file(filepath):
    """Fix imports in a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Apply mappings
        for old, new in IMPORT_MAPPINGS.items():
            content = content.replace(old, new)
        
        # Fix mock patches
        for old, new in IMPORT_MAPPINGS.items():
            # Replace in @patch decorators
            content = re.sub(
                rf'@patch\(["\']({re.escape(old)}[^"\']*)["\']',
                rf'@patch("{new}\1"',
                content
            )
            # Replace in with patch statements
            content = re.sub(
                rf'with patch\(["\']({re.escape(old)}[^"\']*)["\']',
                rf'with patch("{new}\1"',
                content
            )
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Fixed imports in {filepath}")
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def find_missing_modules():
    """Find which modules are actually missing."""
    missing = set()
    
    # Run pytest collect to find import errors
    import subprocess
    result = subprocess.run(
        ['python', '-m', 'pytest', '--collect-only'],
        capture_output=True,
        text=True
    )
    
    # Parse output for ModuleNotFoundError
    for line in result.stderr.split('\n'):
        match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", line)
        if match:
            missing.add(match.group(1))
    
    return missing

def main():
    """Fix imports in all test files."""
    print("Finding missing modules...")
    missing = find_missing_modules()
    print(f"Missing modules: {missing}")
    
    fixed = 0
    test_files = list(Path('tests').rglob('*.py'))
    
    print(f"\nProcessing {len(test_files)} test files...")
    
    for test_file in test_files:
        if fix_file(test_file):
            fixed += 1
    
    print(f"\nFixed {fixed} files")
    
    # Check if we still have errors
    print("\nChecking remaining errors...")
    remaining = find_missing_modules()
    if remaining:
        print(f"Still missing: {remaining}")
    else:
        print("No missing modules found!")

if __name__ == "__main__":
    main()